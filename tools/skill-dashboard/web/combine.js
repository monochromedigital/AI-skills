// Page layer: merges several Macs' snapshots into one report for the "All Macs"
// view. Usage adds up exactly: each Mac's sessions are its own, and any list a
// Mac cut to a top N is merged and cut again. Cloud sessions are the exception:
// every Mac pulls the same ones, so they are kept from the first Mac only, using
// each report's cloudShare (report.py). What a Mac has installed (pending
// updates, MCP servers, trash) doesn't add up across Macs, so the combined
// report leaves it out and marks itself with `combined`.

export const ALL_MACHINES = "all";

// Sources that count as installed, as in report.py's kpis.
const INSTALLED = new Set(["plugin", "personal", "account"]);
// How many top skills each project row names, as in usage.py's most_common(3).
const PROJECT_TOP_SKILLS = 3;
const SKILL_USAGE = ["uses", "usesRecent", "viaModel", "viaSlash", "viaSubagent"];
const KPI_USAGE = ["invocations", "invocationsRecent", "invocationsPrevious"];
const CLOUD_PREFIX = "cloud/"; // a cloud session's project path (cloud/src/cloud.js)
const CLOUD_SOURCE = "cloud";

const time = (value) => (value ? Date.parse(value) : -Infinity);
const later = (a, b) => (time(b) > time(a) ? b : a);
const earlier = (a, b) => (a && (!b || time(a) <= time(b)) ? a : b);
const total = (rows, key) => rows.reduce((sum, row) => sum + (row?.[key] ?? 0), 0);
const newestFirst = (key) => (a, b) => time(b[key]) - time(a[key]);
const isCloud = (path) => Boolean(path?.startsWith(CLOUD_PREFIX));
const addFields = (fields) => (into, row) => { for (const f of fields) into[f] = (into[f] ?? 0) + (row[f] ?? 0); };
const subtract = (fields, from, share = {}) => { for (const f of fields) from[f] -= share[f] ?? 0; };
const addEach = (objects) => objects.reduce((sum, o) => {
  for (const [key, value] of Object.entries(o ?? {})) sum[key] = (sum[key] ?? 0) + value;
  return sum;
}, {});
/** The first row for each key, in order. */
const unique = (rows, keyOf) => {
  const seen = new Set();
  return rows.filter((r) => !seen.has(keyOf(r)) && seen.add(keyOf(r)));
};

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

/** A copy of `report` without its cloud sessions, which the first Mac already counts. */
function withoutCloud(report) {
  const r = structuredClone(report);
  const share = r.cloudShare ?? {};
  for (const s of r.skills) {
    subtract(SKILL_USAGE, s, share.skills?.[s.id]);
    s.byProject = Object.fromEntries(Object.entries(s.byProject ?? {}).filter(([path]) => !isCloud(path)));
  }
  subtract(KPI_USAGE, r.kpis, share.kpis);
  for (const d of r.daily) d.count -= share.daily?.[d.date] ?? 0;
  r.projects = r.projects.filter((p) => !isCloud(p.path));
  r.costRows = r.costRows?.filter((row) => row.src !== CLOUD_SOURCE);
  return r;
}

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
    s.sessions = unique(s.sessions, (x) => x.id).sort(newestFirst("lastUsed")).slice(0, ui.sessionsPerSkill);
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

/** The usage rows the page prices, from every Mac; none unless every Mac has them (never a total covering only some). */
function mergeCost(reports) {
  const metas = reports.map((r) => r.costMeta);
  if (!metas.every(Boolean)) return { costRows: null, costMeta: null, cost: null };
  return {
    costRows: reports.flatMap((r) => r.costRows ?? []),
    costMeta: { ...metas[0], asOf: metas.map((m) => m.asOf).reduce(earlier), names: Object.assign({}, ...metas.map((m) => m.names)) },
  };
}

/** One report for every Mac. `reports` and `machines` are in the same order, newest sync first. */
export function combineReports(reports, machines) {
  const [first] = reports;
  const parts = [first, ...reports.slice(1).map(withoutCloud)];
  const skills = mergeSkills(parts, first.ui);
  const installed = skills.filter((s) => INSTALLED.has(s.source));
  const coverage = parts.map((r) => r.coverage);
  return {
    ...first,
    generatedAt: parts.map((r) => r.generatedAt).reduce(earlier),
    kpis: {
      installed: installed.length,
      used: installed.filter((s) => s.uses).length,
      unused: installed.filter((s) => !s.uses).length,
      builtinUsed: skills.filter((s) => s.source === "builtin" && s.uses).length,
      ...Object.fromEntries(KPI_USAGE.map((k) => [k, total(parts.map((r) => r.kpis), k)])),
      updates: 0, mcpTotal: 0, mcpAttention: 0,
    },
    daily: mergeBy(parts.map((r) => r.daily), (d) => d.date, addFields(["count"]))
      .sort((a, b) => a.date.localeCompare(b.date)).slice(-first.windows.chartDays),
    recent: unique(parts.flatMap((r) => r.recent), (e) => `${e.ts}|${e.id}`).sort(newestFirst("ts")).slice(0, first.windows.recentEvents),
    skills,
    projects: mergeProjects(parts, skills),
    groups: mergeGroups(parts, skills),
    ...mergeCost(parts),
    cloudShare: null,
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
