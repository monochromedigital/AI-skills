// Talking to the local server: read the report, start a job, wait for it.
// The token comes from the page the server rendered; another site cannot read it.
// The published snapshot has no server: its page names a data file instead,
// and the report inside says readOnly, which hides every action.

const meta = (name) => document.querySelector(`meta[name="${name}"]`)?.content;
const TOKEN = meta("dashboard-token");
const SNAPSHOT_DATA = meta("dashboard-data");
const TOKEN_HEADER = "X-Dashboard-Token";

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export async function fetchReport(refresh = false) {
  const response = await fetch(SNAPSHOT_DATA ?? `/api/report${refresh ? "?refresh=1" : ""}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
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
