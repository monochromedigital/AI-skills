// The Monochrome console on Cloudflare: one Worker, two doors.
//
// console.monochrome.digital  The page and its read API. Cloudflare Access
//   signs people in before a request reaches this code, and the API checks
//   Access's signed token itself as well. If Access isn't configured (the two
//   ACCESS_* vars are empty) or the token doesn't verify, data is refused:
//   the console fails closed, never open.
//
// *.workers.dev  Upload only. Each Mac POSTs new rows to /api/ingest/<kind>
//   with its secret token. Nothing can be read through this address.
//
// Uploads are passed to D1 as raw JSON text and unpacked by SQLite
// (json_each), so the Worker never parses large bodies: the free plan allows
// 10 ms of CPU per request, and parsing a few thousand rows would spend it.

const NO_STORE = { "cache-control": "no-store" };
const JSON_TYPE = { "content-type": "application/json; charset=utf-8", ...NO_STORE };
const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: JSON_TYPE });
const NOW = "strftime('%Y-%m-%dT%H:%M:%SZ', 'now')";

const INGEST = {
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
    ON CONFLICT (id) DO UPDATE SET title = excluded.title, custom = excluded.custom, updated_at = ${NOW}`,
  snapshot: `INSERT INTO snapshots (machine_id, generated_at, report)
    SELECT ?1, json_extract(?2, '$.generatedAt'), ?2 WHERE json_valid(?2)
    ON CONFLICT (machine_id) DO UPDATE SET generated_at = excluded.generated_at, report = excluded.report`,
};

const MACHINE = `INSERT INTO machines (id, name, last_sync) VALUES (?1, ?2, ${NOW})
  ON CONFLICT (id) DO UPDATE SET name = excluded.name, last_sync = excluded.last_sync`;

async function sameSecret(given, expected) {
  const enc = new TextEncoder();
  const a = enc.encode(given);
  const b = enc.encode(expected);
  return a.byteLength === b.byteLength && crypto.subtle.timingSafeEqual(a, b);
}

async function ingest(request, env, kind) {
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

// ── Cloudflare Access ────────────────────────────────────────────────────────
const b64url = (text) => Uint8Array.from(atob(text.replace(/-/g, "+").replace(/_/g, "/")), (c) => c.charCodeAt(0));
const decodePart = (part) => JSON.parse(new TextDecoder().decode(b64url(part)));
let certs = { keys: [], fetchedAt: 0 };
const CERTS_TTL_MS = 3600000;

async function accessKeys(team) {
  if (Date.now() - certs.fetchedAt > CERTS_TTL_MS) {
    const response = await fetch(`https://${team}/cdn-cgi/access/certs`);
    certs = { keys: (await response.json()).keys ?? [], fetchedAt: Date.now() };
  }
  return certs.keys;
}

/** The signed-in email, or null. Checks signature, audience, issuer and expiry. */
async function viewer(request, env) {
  if (!env.ACCESS_TEAM_DOMAIN || !env.ACCESS_AUD) return null;
  const token = request.headers.get("cf-access-jwt-assertion");
  if (!token || token.split(".").length !== 3) return null;
  try {
    const [head, body, signature] = token.split(".");
    const header = decodePart(head);
    const claims = decodePart(body);
    const audiences = [].concat(claims.aud);
    if (!audiences.includes(env.ACCESS_AUD) || claims.iss !== `https://${env.ACCESS_TEAM_DOMAIN}`) return null;
    if (!claims.exp || claims.exp * 1000 < Date.now()) return null;
    const jwk = (await accessKeys(env.ACCESS_TEAM_DOMAIN)).find((k) => k.kid === header.kid);
    if (!jwk) return null;
    const key = await crypto.subtle.importKey("jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
    const valid = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, b64url(signature), new TextEncoder().encode(`${head}.${body}`));
    return valid ? claims.email ?? "service" : null;
  } catch {
    return null;
  }
}

// ── read API ─────────────────────────────────────────────────────────────────
async function report(url, env) {
  const machine = url.searchParams.get("machine");
  const row = machine
    ? await env.DB.prepare("SELECT report FROM snapshots WHERE machine_id = ?1").bind(machine).first()
    : await env.DB.prepare("SELECT report FROM snapshots ORDER BY generated_at DESC LIMIT 1").first();
  if (!row) return json({ error: "no data yet" }, 404);
  return new Response(row.report, { headers: JSON_TYPE }); // stored JSON, passed through unparsed
}

async function machines(env) {
  const { results } = await env.DB.prepare(
    "SELECT m.id, m.name, m.last_sync AS lastSync, s.generated_at AS generatedAt FROM machines m LEFT JOIN snapshots s ON s.machine_id = m.id ORDER BY m.last_sync DESC",
  ).all();
  return json(results);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.hostname.endsWith(".workers.dev")) {
      const match = url.pathname.match(/^\/api\/ingest\/([a-z]+)$/);
      if (request.method === "POST" && match) return ingest(request, env, match[1]);
      return new Response("Not found", { status: 404, headers: NO_STORE });
    }

    if (url.pathname.startsWith("/api/")) {
      if (!(await viewer(request, env))) return json({ error: "Sign in through Cloudflare Access to see this data." }, 403);
      if (url.pathname === "/api/report") return report(url, env);
      if (url.pathname === "/api/machines") return machines(env);
      return json({ error: "not found" }, 404);
    }

    return env.ASSETS.fetch(request);
  },
};
