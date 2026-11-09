// The upload door: each Mac POSTs new rows with its secret token.
// Uploads go to D1 as raw JSON text and SQLite unpacks them (json_each), so
// the Worker never parses large bodies.

import { json, NOW } from "./shared.js";

export const INGEST = {
  events: `INSERT OR IGNORE INTO skill_events (id, machine_id, ts, skill, via, session_id, project, subagent, entrypoint)
    SELECT json_extract(value, '$.id'), ?1, json_extract(value, '$.ts'), json_extract(value, '$.skill'),
           json_extract(value, '$.via'), json_extract(value, '$.session'), json_extract(value, '$.project'),
           coalesce(json_extract(value, '$.subagent'), 0), json_extract(value, '$.entrypoint')
    FROM json_each(?2)`,
  tokens: `INSERT OR IGNORE INTO token_usage (id, machine_id, ts, model, session_id, project, subagent,
           input_tokens, output_tokens, cache_write_5m, cache_write_1h, cache_read, web_searches)
    SELECT json_extract(value, '$.id'), ?1, json_extract(value, '$.ts'), json_extract(value, '$.model'),
           json_extract(value, '$.session'), json_extract(value, '$.project'), coalesce(json_extract(value, '$.subagent'), 0),
           json_extract(value, '$.in'), json_extract(value, '$.out'), json_extract(value, '$.cw5m'),
           json_extract(value, '$.cw1h'), json_extract(value, '$.cr'), json_extract(value, '$.search')
    FROM json_each(?2)`,
  sessions: `INSERT INTO sessions (id, machine_id, title, custom)
    SELECT json_extract(value, '$.id'), ?1, json_extract(value, '$.title'), coalesce(json_extract(value, '$.custom'), 0)
    FROM json_each(?2) WHERE true
    ON CONFLICT (id) DO UPDATE SET title = excluded.title, custom = excluded.custom, updated_at = ${NOW}
    WHERE sessions.title IS NOT excluded.title OR sessions.custom IS NOT excluded.custom`,
  snapshot: `INSERT INTO snapshots (machine_id, generated_at, report)
    SELECT ?1, json_extract(?2, '$.generatedAt'), ?2 WHERE json_valid(?2)
    ON CONFLICT (machine_id) DO UPDATE SET generated_at = excluded.generated_at, report = excluded.report`,
};

export const MACHINE = `INSERT INTO machines (id, name, last_sync) VALUES (?1, ?2, ${NOW})
  ON CONFLICT (id) DO UPDATE SET name = excluded.name, last_sync = excluded.last_sync`;

export async function sameSecret(given, expected) {
  const enc = new TextEncoder();
  const a = enc.encode(given);
  const b = enc.encode(expected);
  return a.byteLength === b.byteLength && crypto.subtle.timingSafeEqual(a, b);
}

export async function ingest(request, env, kind) {
  if (!env.INGEST_TOKEN || !(await sameSecret(request.headers.get("authorization") ?? "", `Bearer ${env.INGEST_TOKEN}`))) {
    return json({ error: "unauthorized" }, 401);
  }
  const machineId = request.headers.get("x-machine-id");
  // Percent-encoded by the sender: a Mac's name ("Johnny’s MacBook") isn't valid in a raw header.
  const machineName = decodeURIComponent(request.headers.get("x-machine-name") ?? "") || machineId;
  if (!INGEST[kind] || !machineId) return json({ error: "unknown upload" }, 400);
  const body = await request.text();
  try {
    const [, result] = await env.DB.batch([
      env.DB.prepare(MACHINE).bind(machineId, machineName),
      env.DB.prepare(INGEST[kind]).bind(machineId, body),
    ]);
    return json({ ok: true, written: result.meta.changes });
  } catch (error) {
    return json({ error: String(error.message ?? error) }, 400);
  }
}
