// Talking to the local server: read the report, start a job, wait for it.
// The token comes from the page the server rendered; another site cannot read it.
// The published snapshot has no server: its page names a data file instead,
// and the report inside says readOnly, which hides every action.

import { buildCost } from "./cost-model.js";

const meta = (name) => document.querySelector(`meta[name="${name}"]`)?.content;
const TOKEN = meta("dashboard-token");
const SNAPSHOT_DATA = meta("dashboard-data");
const MACHINES = meta("dashboard-machines"); // online console only: every Mac that has synced
const COST_ROWS = meta("dashboard-cost-rows"); // online console only: live usage totals from its database
const MINUTE_MS = 60000;
const TOKEN_HEADER = "X-Dashboard-Token";

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/** Today as "YYYY-MM-DD" in this browser's time zone, and that zone's offset from UTC in minutes. */
const localToday = () => new Date(Date.now() - new Date().getTimezoneOffset() * MINUTE_MS).toISOString().slice(0, 10);
const utcOffsetMinutes = () => -new Date().getTimezoneOffset();

/** Live usage rows from the console (cloud sessions as they happen, each Mac as of its last sync); null if not online. */
async function liveCostRows() {
  if (!COST_ROWS) return null;
  try {
    const response = await fetch(`${COST_ROWS}?tz=${utcOffsetMinutes()}`, { cache: "no-store" });
    return response.ok ? await response.json() : null;
  } catch {
    return null;
  }
}

/** Price the report's usage rows (or the console's live ones) into report.cost. */
async function withCost(report) {
  if (!report.costMeta) return report;
  const live = await liveCostRows();
  return { ...report, costLive: Boolean(live), cost: buildCost(live ?? report.costRows ?? [], report.costMeta, localToday()) };
}

export async function fetchReport(refresh = false, machine = null) {
  const snapshot = SNAPSHOT_DATA && machine ? `${SNAPSHOT_DATA}?machine=${encodeURIComponent(machine)}` : SNAPSHOT_DATA;
  const response = await fetch(snapshot ?? `/api/report${refresh ? "?refresh=1" : ""}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return withCost(await response.json());
}

/** The Macs that have uploaded a snapshot, newest sync first; empty when there is no list to read. */
export async function fetchMachines() {
  if (!MACHINES) return [];
  try {
    const response = await fetch(MACHINES, { cache: "no-store" });
    return response.ok ? (await response.json()).filter((m) => m.generatedAt) : [];
  } catch {
    return [];
  }
}

/** Start an action and resolve with the finished job: { status: "done" | "failed", result, error, log }. */
export async function runJob(action, target, pollMs) {
  try {
    const response = await fetch("/api/actions", {
      method: "POST",
      headers: { "Content-Type": "application/json", [TOKEN_HEADER]: TOKEN },
      body: JSON.stringify({ action, target: target ?? null }),
    });
    let job = await response.json();
    if (!response.ok) throw new Error(job.error);
    while (job.status !== "done" && job.status !== "failed") {
      await sleep(pollMs);
      job = await (await fetch(`/api/jobs/${job.id}`)).json();
    }
    return job;
  } catch (error) {
    return { status: "failed", error: error.message, log: [] };
  }
}
