// Page layer: merges several Macs' snapshots into one report for the "All Macs"
// view. Usage and cost add up exactly: each Mac's sessions are its own, and any
// list a Mac cut to a top N is merged and cut again. What a Mac has installed
// (pending updates, MCP servers, trash) doesn't add up across Macs, so the
// combined report leaves it out and marks itself with `combined`.

export const ALL_MACHINES = "all";

// Sources that count as installed, as in report.py's kpis.
const INSTALLED = new Set(["plugin", "personal", "account"]);
// How many top skills each project row names, as in usage.py's most_common(3).
const PROJECT_TOP_SKILLS = 3;
const SKILL_USAGE = ["uses", "usesRecent", "viaModel", "viaSlash", "viaSubagent"];
const COST_FIELDS = ["cost", "tokens", "replies", "sessions"];

const time = (value) => (value ? Date.parse(value) : -Infinity);
const later = (a, b) => (time(b) > time(a) ? b : a);
const earlier = (a, b) => (a && (!b || time(a) <= time(b)) ? a : b);
const total = (rows, key) => rows.reduce((sum, row) => sum + (row?.[key] ?? 0), 0);
const newestFirst = (key) => (a, b) => time(b[key]) - time(a[key]);
const addFields = (fields) => (into, row) => { for (const f of fields) into[f] = (into[f] ?? 0) + (row[f] ?? 0); };
const addEach = (objects) => objects.reduce((sum, o) => {
  for (const [key, value] of Object.entries(o ?? {})) sum[key] = (sum[key] ?? 0) + value;
  return sum;
}, {});

/** One row per key; `merge(into, row)` folds each later row into a copy of the first. */
function mergeBy(lists, keyOf, merge) {
  const rows = new Map();
  for (const row of lists.flat()) {
    const key = keyOf(row);
    if (rows.has(key)) merge(rows.get(key), row);
    else rows.set(key, structuredClone(row));
  }
  return [...rows.values()];
}

const byDate = (lists, field, days) =>
  mergeBy(lists, (d) => d.date, addFields([field])).sort((a, b) => a.date.localeCompare(b.date)).slice(-days);

function mergeSkills(reports, ui) {
  const skills = mergeBy(reports.map((r) => r.skills), (s) => s.id, (into, s) => {
    addFields(SKILL_USAGE)(into, s);
    into.byProject = addEach([into.byProject, s.byProject]);
    into.sessions = [...into.sessions, ...s.sessions];
    into.firstUsed = earlier(into.firstUsed, s.firstUsed);
    into.lastUsed = later(into.lastUsed, s.lastUsed);
    into.addedAt = earlier(into.addedAt, s.addedAt);
  });
  for (const s of skills) {
    s.projects = Object.keys(s.byProject ?? {}).length;
    s.sessions = s.sessions.sort(newestFirst("lastUsed")).slice(0, ui.sessionsPerSkill);
  }
  return skills.sort((a, b) => b.uses - a.uses || a.name.localeCompare(b.name));
}

function mergeProjects(reports, skills) {
  const rows = mergeBy(reports.map((r) => r.projects), (p) => p.path, (into, p) => {
    addFields(["uses", "sessions"])(into, p);
    into.lastUsed = later(into.lastUsed, p.lastUsed);
  });
  for (const p of rows) {
    const used = skills.filter((s) => s.byProject?.[p.path]).sort((a, b) => b.byProject[p.path] - a.byProject[p.path]);
    p.skills = used.length;
    p.top = used.slice(0, PROJECT_TOP_SKILLS).map((s) => s.name);
  }
  return rows.sort((a, b) => b.uses - a.uses || a.name.localeCompare(b.name));
}

const mergeGroups = (reports, skills) => mergeBy(reports.map((r) => r.groups), (g) => g.id, () => {}).map((g) => {
  const members = skills.filter((s) => s.group === g.id);
  return { ...g, skills: members.length, uses: total(members, "uses") };
});

function mergeCost(costs, report) {
  const [first] = costs;
  const sumOf = (pick) => addEach(costs.map(pick));
  const withLatest = (into, row) => { addFields(COST_FIELDS)(into, row); into.lastUsed = later(into.lastUsed, row.lastUsed); };
  const byCost = (a, b) => b.cost - a.cost;
  return {
    ...first,
    totals: sumOf((c) => c.totals),
    byKind: sumOf((c) => c.byKind),
    unpriced: sumOf((c) => c.unpriced),
    daily: byDate(costs.map((c) => c.daily), "cost", report.windows.chartDays),
    projects: mergeBy(costs.map((c) => c.projects), (p) => p.path, withLatest).sort(byCost),
    models: mergeBy(costs.map((c) => c.models), (m) => m.model, withLatest).sort(byCost),
    sessions: costs.flatMap((c) => c.sessions).sort(byCost).slice(0, report.ui.costSessions),
  };
}

/** One report for every Mac. `reports` and `machines` are in the same order, newest sync first. */
export function combineReports(reports, machines) {
  const [first] = reports;
  const skills = mergeSkills(reports, first.ui);
  const installed = skills.filter((s) => INSTALLED.has(s.source));
  const kpis = reports.map((r) => r.kpis);
  const coverage = reports.map((r) => r.coverage);
  const costs = reports.map((r) => r.cost);
  return {
    ...first,
    generatedAt: reports.map((r) => r.generatedAt).reduce(earlier),
    kpis: {
      installed: installed.length,
      used: installed.filter((s) => s.uses).length,
      unused: installed.filter((s) => !s.uses).length,
      builtinUsed: skills.filter((s) => s.source === "builtin" && s.uses).length,
      invocations: total(kpis, "invocations"),
      invocationsRecent: total(kpis, "invocationsRecent"),
      invocationsPrevious: total(kpis, "invocationsPrevious"),
      updates: 0, mcpTotal: 0, mcpAttention: 0,
    },
    daily: byDate(reports.map((r) => r.daily), "count", first.windows.chartDays),
    recent: reports.flatMap((r) => r.recent).sort(newestFirst("ts")).slice(0, first.windows.recentEvents),
    skills,
    projects: mergeProjects(reports, skills),
    groups: mergeGroups(reports, skills),
    cost: costs.every(Boolean) ? mergeCost(costs, first) : null, // never a total that covers only some Macs
    coverage: {
      ...coverage[0],
      since: coverage.map((c) => c.since).reduce(earlier),
      transcripts: total(coverage, "transcripts"),
      lastSync: coverage.map((c) => c.lastSync).reduce(earlier), // the stalest Mac bounds the whole view
      remoteEnabled: coverage.every((c) => c.remoteEnabled),
      remoteErrors: Object.assign({}, ...coverage.map((c) => c.remoteErrors)),
    },
    updates: [], mcp: null, trash: [], readOnly: true,
    machine: { id: ALL_MACHINES },
    combined: { names: machines.map((m) => m.name) },
  };
}
