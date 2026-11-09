// Page layer: prices token usage and builds the cost section's data, one
// breakdown per month (newest first) and one for all time. The rows are token
// counts summed per day, project, session, model and source; they come from
// cost.py on the Mac and, on the online console, live from its database
// (cloud/src/cost.js), so both pages price the same way.
//
// A reply's cost, per million tokens at the list prices in `meta.models`:
//   input × input + output × output
//   + cache writes × input × 1.25 (5-minute cache) or × 2 (1-hour cache)
//   + cache reads × cache-read price

import { addDays, monthDays, monthsBetween } from "./calendar.js";

const ALL = "all";
const CLOUD = "cloud";
const CLOUD_PREFIX = "cloud/";
const UNNAMED = "unnamed";
const PER_MILLION = 1e6;
const PRECISION = 1e4; // costs are kept to four decimals
const KINDS = ["input", "output", "cacheWrite", "cacheRead"];

const round = (value) => Math.round(value * PRECISION) / PRECISION;
const tokensOf = (r) => r.in + r.out + r.cw5m + r.cw1h + r.cr;
const bucket = () => ({ cost: 0, tokens: 0, replies: 0, last: 0, sessions: new Set() });
const at = (map, key, make = bucket) => map.get(key) ?? map.set(key, make()).get(key);

function priced(r, price, multiplier) {
  return {
    input: (r.in * price.input) / PER_MILLION,
    output: (r.out * price.output) / PER_MILLION,
    cacheWrite: ((r.cw5m * multiplier["5m"] + r.cw1h * multiplier["1h"]) * price.input) / PER_MILLION,
    cacheRead: (r.cr * price.cacheRead) / PER_MILLION,
  };
}

function add(b, cost, r) {
  b.cost += cost;
  b.tokens += tokensOf(r);
  b.replies += r.n;
  b.last = Math.max(b.last, Date.parse(r.last));
  if (r.s) b.sessions.add(r.s);
}

/** The environment a cloud row's project path ("cloud/<environment>/<repository>") names. */
export function cloudEnvironment(path) {
  const parts = (path ?? "").split("/");
  return path?.startsWith(CLOUD_PREFIX) && parts.length > 1 ? parts[1] : UNNAMED;
}

function projectName(path, names) {
  if (names?.[path]) return names[path];
  const parts = (path ?? "").split("/");
  if (path?.startsWith(CLOUD_PREFIX)) return `${parts[2] ?? parts[1]} (cloud)`;
  return parts.filter(Boolean).pop() ?? "—";
}

function newPeriod() {
  return { total: bucket(), sources: { mac: 0, cloud: 0 }, kinds: Object.fromEntries(KINDS.map((k) => [k, 0])),
    series: new Map(), projects: new Map(), sessions: new Map(), models: new Map(), environments: new Map() };
}

function addTo(period, r, split, cost, slot) {
  add(period.total, cost, r);
  for (const kind of KINDS) period.kinds[kind] += split[kind];
  period.series.set(slot, (period.series.get(slot) ?? 0) + cost);
  period.sources[r.src === CLOUD ? "cloud" : "mac"] += cost;
  if (r.src === CLOUD) add(at(period.environments, cloudEnvironment(r.p)), cost, r);
  add(at(period.projects, r.p), cost, r);
  if (r.s) {
    const session = at(period.sessions, r.s, () => ({ ...bucket(), project: r.p, cloud: r.src === CLOUD, title: null }));
    add(session, cost, r);
    session.title ??= r.t ?? null;
  }
  add(at(period.models, r.m), cost, r);
}

function listOf(map, extra, limit) {
  return [...map.entries()].sort((a, b) => b[1].cost - a[1].cost).slice(0, limit).map(([key, b]) => ({
    cost: round(b.cost), tokens: b.tokens, replies: b.replies, sessions: b.sessions.size,
    lastUsed: new Date(b.last).toISOString(), ...extra(key, b),
  }));
}

/** The cost section's data from usage rows and `meta` (cost.py's cost_meta), as of `today` ("YYYY-MM-DD", local). */
export function buildCost(rows, meta, today) {
  const periods = new Map();
  const unpriced = {};
  const totals = { all: 0, recent: 0, previous: 0, month: 0 };
  const thisMonth = today.slice(0, 7);
  const recentFrom = addDays(today, 1 - meta.recentDays);
  const previousFrom = addDays(recentFrom, -meta.recentDays);
  let firstDay = today;
  for (const r of rows) {
    if (meta.free.includes(r.m)) continue;
    const price = meta.models[r.m];
    if (!price) {
      unpriced[r.m] = (unpriced[r.m] ?? 0) + r.n;
      continue;
    }
    const split = priced(r, price, meta.cacheWriteMultiplier);
    const cost = KINDS.reduce((sum, k) => sum + split[k], 0);
    const month = r.d.slice(0, 7);
    if (r.d < firstDay) firstDay = r.d;
    totals.all += cost;
    if (r.d >= recentFrom) totals.recent += cost;
    else if (r.d >= previousFrom) totals.previous += cost;
    if (month === thisMonth) totals.month += cost;
    addTo(at(periods, month, newPeriod), r, split, cost, r.d);
    addTo(at(periods, ALL, newPeriod), r, split, cost, month);
  }
  const period = (id, slots) => {
    const p = periods.get(id);
    return {
      id, kind: id === ALL ? "all" : "month", cost: round(p.total.cost), tokens: p.total.tokens,
      replies: p.total.replies, sessionCount: p.total.sessions.size,
      bySource: { mac: round(p.sources.mac), cloud: round(p.sources.cloud) },
      byKind: Object.fromEntries(KINDS.map((k) => [k, round(p.kinds[k])])),
      series: slots.map((date) => ({ date, cost: round(p.series.get(date) ?? 0) })),
      projects: listOf(p.projects, (path) => ({ path, name: projectName(path, meta.names) })),
      sessions: listOf(p.sessions, (id_, b) => ({ id: id_, title: b.title, project: projectName(b.project, meta.names), cloud: b.cloud }), meta.topSessions),
      models: listOf(p.models, (model) => ({ model })),
      environments: listOf(p.environments, (name) => ({ name, named: name !== UNNAMED })),
    };
  };
  const months = [...periods.keys()].filter((k) => k !== ALL).sort().reverse();
  return {
    currency: meta.currency, asOf: meta.asOf, thisMonth, plan: meta.plan, leftOut: meta.leftOut, unpriced,
    totals: Object.fromEntries(Object.entries(totals).map(([k, v]) => [k, round(v)])),
    periods: [...months.map((m) => period(m, monthDays(m, firstDay, today))),
      ...(months.length ? [period(ALL, monthsBetween(months[months.length - 1], months[0]))] : [])],
  };
}
