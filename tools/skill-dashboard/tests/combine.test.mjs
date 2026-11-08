// Run: node tools/skill-dashboard/tests/combine.test.mjs "$PWD/tools/skill-dashboard/web/combine.js" <a snapshot report.json>
// (a snapshot comes from export.snapshot_report; see README).
// Checks combineReports against invariants: B is A from a second Mac, with its own
// session ids, one skill A never had, and one A skill uninstalled.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
const { combineReports, ALL_MACHINES } = await import(process.argv[2]);
const A = JSON.parse(readFileSync(process.argv[3], "utf8"));
const B = structuredClone(A);
B.machine = { id: "b", name: "Test MacBook Air" };
for (const s of B.skills) s.sessions = s.sessions.map((x) => ({ ...x, id: "b-" + x.id }));
B.cost.sessions = B.cost.sessions.map((x) => ({ ...x, id: "b-" + x.id }));
const dropped = B.skills.find((s) => s.source === "personal" && !s.uses);
B.skills = B.skills.filter((s) => s !== dropped);
B.skills.push({ ...structuredClone(B.skills.find((s) => s.source === "personal")), id: "only-on-b", name: "only-on-b", uses: 0, usesRecent: 0, byProject: {}, sessions: [] });

const C = combineReports([A, B], [{ id: A.machine.id, name: A.machine.name }, { id: "b", name: "Test MacBook Air" }]);
const near = (x, y) => assert.ok(Math.abs(x - y) < 1e-6, `${x} vs ${y}`);

assert.equal(C.machine.id, ALL_MACHINES);
assert.deepEqual(C.combined.names, [A.machine.name, "Test MacBook Air"]);
assert.equal(C.kpis.invocations, 2 * A.kpis.invocations);
assert.equal(C.kpis.invocationsRecent, 2 * A.kpis.invocationsRecent);
assert.equal(C.kpis.installed, A.kpis.installed + 1, "union: A's skills plus the one only on B");
assert.equal(C.kpis.used, A.kpis.used, "same skills used");
assert.equal(C.skills.length, A.skills.length + 1);
assert.equal(C.skills[0].uses, 2 * A.skills[0].uses, "sorted by uses, doubled");
assert.equal(C.skills[0].projects, A.skills[0].projects, "same project paths, not double-counted");
assert.equal(C.skills[0].sessions.length, Math.min(A.ui.sessionsPerSkill, 2 * A.skills[0].sessions.length));
assert.ok(C.skills.find((s) => s.id === dropped.id), "skill uninstalled on B still listed from A");
assert.equal(C.daily.length, A.daily.length);
assert.equal(C.daily.reduce((t, d) => t + d.count, 0), 2 * A.daily.reduce((t, d) => t + d.count, 0));
assert.equal(C.recent.length, A.recent.length);
assert.equal(C.projects.length, A.projects.length);
assert.equal(C.projects[0].uses, 2 * A.projects[0].uses);
assert.equal(C.projects[0].skills, A.projects[0].skills, "distinct skills per project not double-counted");
assert.deepEqual(C.projects[0].top, A.projects[0].top);
for (const g of C.groups) {
  const a = A.groups.find((x) => x.id === g.id);
  assert.equal(g.uses, 2 * a.uses, `group ${g.id} uses`);
}
for (const key of Object.keys(A.cost.totals)) near(C.cost.totals[key], 2 * A.cost.totals[key]);
for (const key of Object.keys(A.cost.byKind)) near(C.cost.byKind[key], 2 * A.cost.byKind[key]);
near(C.cost.daily.reduce((t, d) => t + d.cost, 0), 2 * A.cost.daily.reduce((t, d) => t + d.cost, 0));
assert.equal(C.cost.projects.length, A.cost.projects.length);
near(C.cost.projects[0].cost, 2 * A.cost.projects[0].cost);
assert.equal(C.cost.sessions.length, A.ui.costSessions);
near(C.cost.sessions[0].cost, A.cost.sessions[0].cost);
near(C.cost.sessions[1].cost, A.cost.sessions[0].cost, "the B copy of the top session is second");
assert.equal(C.coverage.transcripts, 2 * A.coverage.transcripts);
assert.equal(C.mcp, null); assert.deepEqual(C.updates, []); assert.equal(C.readOnly, true);
assert.equal(A.kpis.invocations, A.skills.reduce((t, s) => t + s.uses, 0), "inputs untouched");

const noCost = structuredClone(B); delete noCost.cost;
assert.equal(combineReports([A, noCost], [{ name: "a" }, { name: "b" }]).cost, null, "no partial cost total");
console.log("combine: all checks passed");
