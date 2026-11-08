// Cloud sessions: Claude Code running on Anthropic's servers reports each API
// request and skill use over OpenTelemetry (OTLP over HTTP, JSON) to
// POST /v1/logs on the upload address. It authenticates with its own key,
// CLOUD_INGEST_TOKEN, which can do nothing else. Rows are stored as the
// machine "cloud" in the same tables the Macs fill, shaped like a Mac's rows,
// and each Mac pulls them (GET /api/cloud/<kind>, with the Mac's key) into its
// own report. Prompts and replies are never sent: Claude Code leaves them out
// unless OTEL_LOG_USER_PROMPTS is set, and nothing here would store them.

import { INGEST, MACHINE, sameSecret } from "./ingest.js";
import { json, JSON_TYPE } from "./shared.js";

export const CLOUD = { id: "cloud", name: "Cloud sessions", project: "Cloud sessions", entrypoint: "cloud" };
const PULL_LIMIT = 5000;

const value = (v) => v?.stringValue ?? (v?.intValue != null ? Number(v.intValue) : v?.doubleValue ?? v?.boolValue ?? null);
const attributes = (list) => Object.fromEntries((list ?? []).map((a) => [a.key, value(a.value)]));
const count = (x) => Math.max(0, Number(x) || 0);
const nanosToIso = (nanos) => (nanos ? new Date(Number(BigInt(nanos) / 1000000n)).toISOString() : new Date().toISOString());

/** Turn an OTLP logs body into token and skill rows shaped like a Mac's uploads. Other events are dropped. */
export function cloudRows(body) {
  const tokens = [];
  const events = [];
  for (const resourceLog of body.resourceLogs ?? []) {
    const resource = attributes(resourceLog.resource?.attributes);
    for (const scopeLog of resourceLog.scopeLogs ?? []) {
      for (const record of scopeLog.logRecords ?? []) {
        const a = { ...resource, ...attributes(record.attributes) };
        const name = String(a["event.name"] ?? "").replace(/^claude_code\./, "");
        const session = a["ccr.session.id"] ?? a["session.id"] ?? null;
        const ts = a["event.timestamp"] ?? nanosToIso(record.timeUnixNano);
        const base = { ts, session, project: CLOUD.project, entrypoint: CLOUD.entrypoint,
          subagent: a["agent.name"] ? 1 : 0 };
        if (name === "api_request") {
          const id = a.request_id ?? a.client_request_id;
          if (!id) continue;
          const written = count(a.cache_creation_tokens);
          const hour = count(a.cache_creation_1h_tokens);
          tokens.push({ ...base, id, model: a.model, in: count(a.input_tokens), out: count(a.output_tokens),
            cw5m: count(a.cache_creation_5m_tokens) || Math.max(0, written - hour), cw1h: hour,
            cr: count(a.cache_read_tokens), search: 0 });
        } else if (name === "skill_activated" && a["skill.name"] && a["skill.name"] !== "custom_skill") {
          events.push({ ...base, id: `cloud:${session}:${ts}:${a["skill.name"]}`, skill: a["skill.name"], via: "model" });
        }
      }
    }
  }
  return { tokens, events };
}

/** POST /v1/logs from a cloud session. */
export async function cloudIngest(request, env) {
  if (!env.CLOUD_INGEST_TOKEN || !(await sameSecret(request.headers.get("authorization") ?? "", `Bearer ${env.CLOUD_INGEST_TOKEN}`))) {
    return json({ error: "unauthorized" }, 401);
  }
  let rows;
  try {
    rows = cloudRows(await request.json());
  } catch {
    return json({ error: "expected OTLP logs as JSON" }, 400);
  }
  const writes = Object.entries(rows).filter(([, list]) => list.length)
    .map(([kind, list]) => env.DB.prepare(INGEST[kind]).bind(CLOUD.id, JSON.stringify(list)));
  if (!writes.length) return json({ partialSuccess: {} });
  try {
    await env.DB.batch([env.DB.prepare(MACHINE).bind(CLOUD.id, CLOUD.name), ...writes]);
  } catch (error) { // e.g. the free plan's daily write limit: Claude Code drops the batch and carries on
    return json({ error: String(error.message ?? error) }, 503);
  }
  return json({ partialSuccess: {} });
}

const PULL = {
  tokens: `SELECT json_group_array(json_object('cursor', rowid, 'id', id, 'ts', ts, 'model', model, 'session', session_id,
      'project', project, 'subagent', subagent, 'entrypoint', '${CLOUD.entrypoint}', 'in', input_tokens, 'out', output_tokens,
      'cw5m', cache_write_5m, 'cw1h', cache_write_1h, 'cr', cache_read, 'search', web_searches)) AS rows
    FROM (SELECT rowid, * FROM token_usage WHERE machine_id = ?1 AND rowid > ?2 ORDER BY rowid LIMIT ?3)`,
  events: `SELECT json_group_array(json_object('cursor', rowid, 'id', id, 'ts', ts, 'skill', skill, 'via', via,
      'session', session_id, 'project', project, 'subagent', subagent, 'entrypoint', entrypoint)) AS rows
    FROM (SELECT rowid, * FROM skill_events WHERE machine_id = ?1 AND rowid > ?2 ORDER BY rowid LIMIT ?3)`,
};

/** GET /api/cloud/<kind>?after=<cursor>: cloud rows a Mac hasn't pulled yet, oldest first. Mac key only. */
export async function cloudPull(request, env, kind) {
  if (!env.INGEST_TOKEN || !(await sameSecret(request.headers.get("authorization") ?? "", `Bearer ${env.INGEST_TOKEN}`))) {
    return json({ error: "unauthorized" }, 401);
  }
  if (!PULL[kind]) return json({ error: "unknown kind" }, 404);
  const after = Number(new URL(request.url).searchParams.get("after")) || 0;
  const row = await env.DB.prepare(PULL[kind]).bind(CLOUD.id, after, PULL_LIMIT).first();
  return new Response(row?.rows ?? "[]", { headers: JSON_TYPE }); // built by SQLite, passed through unparsed
}
