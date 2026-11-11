// Run: node tools/skill-dashboard/tests/combine.test.mjs   (or: make test)
// Checks combineReports against invariants, using the sample report as Mac A.
// A gains some cloud-session usage; B is A again from a second Mac: its own
// local session ids, the same cloud sessions (every Mac pulls them), one skill
// A never had, and one A skill uninstalled. Cloud usage must count once.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { combineReports, ALL_MACHINES } from "../web/combine.js";
import { buildCost } from "../web/cost-model.js";

const sample = JSON.parse(readFileSync(new URL("../fixtures/sample-report.json", import.meta.url), "utf8"));
const CLOUD_USES = 5;
const CLOUD_PATH = "cloud/env-test/repo-test";
const CLOUD_SESSION = "cloud-session";
const today = sample.daily.at(-1).date;

/** The sample, plus CLOUD_USES uses of its top skill in one cloud session today, with a cloudShare that says so. */
function withCloudUsage(report) {
  const r = structuredClone(report);
  const s = r.skills[0];
  Object.assign(s, { uses: s.uses + CLOUD_USES, usesRecent: s.usesRecent + CLOUD_USES, viaModel: s.viaModel + CLOUD_USES });
  s.byProject[CLOUD_PATH] = CLOUD_USES;
  s.projects += 1;
  s.sessions.unshift({ id: CLOUD_SESSION, title: "cloud", uses: CLOUD_USES, lastUsed: `${today}T12:00:00Z`, project: "repo-test (cloud)" });
  for (const k of ["invocations", "invocationsRecent"]) r.kpis[k] += CLOUD_USES;
  r.daily.at(-1).count += CLOUD_USES;
  r.projects.push({ path: CLOUD_PATH, name: "repo-test (cloud)", uses: CLOUD_USES, sessions: 1, skills: 1, top: [s.name], lastUsed: `${today}T12:00:00Z` });
  r.costRows.push({ ...r.costRows[0], p: CLOUD_PATH, s: CLOUD_SESSION, src: "cloud", d: today });
  r.cloudShare = {
    skills: { [s.id]: { uses: CLOUD_USES, usesRecent: CLOUD_USES, viaModel: CLOUD_USES } },
    kpis: { invocations: CLOUD_USES, invocationsRecent: CLOUD_USES, invocationsPrevious: 0 },
    daily: { [today]: CLOUD_USES },
  };
  return r;
}

const A = withCloudUsage(sample);
const B = structuredClone(A);
B.machine = { id: "b", name: "Test MacBook Air" };
const local = (id) => (id === CLOUD_SESSION ? id : `b-${id}`);
for (const s of B.skills) s.sessions = s.sessions.map((x) => ({ ...x, id: local(x.id) }));
B.costRows = B.costRows.map((row) => ({ ...row, s: local(row.s) }));
const dropped = B.skills.find((s) => s.source === "personal" && !s.uses);
B.skills = B.skills.filter((s) => s !== dropped);
B.skills.push({ ...structuredClone(B.skills.find((s) => s.source === "personal")), id: "only-on-b", name: "only-on-b", uses: 0, usesRecent: 0, byProject: {}, sessions: [] });

const machines = [{ id: A.machine.id, name: A.machine.name }, { id: "b", name: "Test MacBook Air" }];
const C = combineReports([A, B], machines);
const twiceLessCloud = (a) => 2 * a - CLOUD_USES; // A and B both carry the cloud uses; the result counts them once
const near = (x, y, why) => assert.ok(Math.abs(x - y) < 1e-6, `${why}: ${x} vs ${y}`);

assert.equal(C.machine.id, ALL_MACHINES);
assert.deepEqual(C.combined.names, machines.map((m) => m.name));
assert.equal(C.kpis.invocations, twiceLessCloud(A.kpis.invocations));
assert.equal(C.kpis.invocationsRecent, twiceLessCloud(A.kpis.invocationsRecent));
assert.equal(C.kpis.installed, A.kpis.installed + 1, "union: A's skills plus the one only on B");
assert.equal(C.skills.length, A.skills.length + 1);
assert.equal(C.skills[0].uses, twiceLessCloud(A.skills[0].uses), "top skill: both Macs' own uses, cloud once");
assert.equal(C.skills[0].byProject[CLOUD_PATH], CLOUD_USES, "cloud project counted once");
assert.equal(C.skills[0].projects, A.skills[0].projects, "same project paths, not double-counted");
assert.equal(C.skills[0].sessions.filter((x) => x.id === CLOUD_SESSION).length, 1, "the cloud session listed once");
assert.ok(C.skills.find((s) => s.id === dropped.id), "skill uninstalled on B still listed from A");
assert.equal(C.daily.length, A.daily.length);
assert.equal(C.daily.reduce((t, d) => t + d.count, 0), twiceLessCloud(A.daily.reduce((t, d) => t + d.count, 0)));
assert.equal(C.projects.find((p) => p.path === CLOUD_PATH).uses, CLOUD_USES);
assert.equal(C.projects.length, A.projects.length);
for (const g of C.groups) assert.equal(g.uses, C.skills.filter((s) => s.group === g.id).reduce((t, s) => t + s.uses, 0), `group ${g.id}`);

const priced = (rows) => buildCost(rows, A.costMeta, today).totals.all;
const cloudRows = A.costRows.filter((r) => r.src === "cloud");
assert.equal(C.costRows.length, 2 * A.costRows.length - cloudRows.length, "every Mac's rows, cloud rows once");
near(priced(C.costRows), 2 * priced(A.costRows) - priced(cloudRows), "priced total");
assert.equal(C.coverage.transcripts, 2 * A.coverage.transcripts);
assert.equal(C.mcp, null); assert.deepEqual(C.updates, []); assert.equal(C.readOnly, true);
assert.equal(A.kpis.invocations, sample.kpis.invocations + CLOUD_USES, "inputs untouched");

const noCost = structuredClone(B); delete noCost.costMeta;
const partial = combineReports([A, noCost], machines);
assert.equal(partial.costMeta, null, "no cost total that covers only some Macs");
assert.equal(partial.cost, null);

const one = combineReports([A], machines.slice(0, 1));
assert.equal(one.kpis.invocations, A.kpis.invocations, "one Mac: the same numbers");
assert.equal(one.costRows.length, A.costRows.length);
console.log("combine: all checks passed");
