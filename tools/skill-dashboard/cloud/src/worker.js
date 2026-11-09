// The Monochrome console on Cloudflare: one Worker, two doors.
//
// console.monochrome.digital  The page and its read API. Cloudflare Access
//   signs people in before a request reaches this code, and the API checks
//   Access's signed token itself as well. If Access isn't configured (the two
//   ACCESS_* vars are empty) or the token doesn't verify, data is refused:
//   the console fails closed, never open.
//
// *.workers.dev  The upload door. Each Mac POSTs new rows to /api/ingest/<kind>
//   with its secret token; cloud sessions POST OpenTelemetry logs to /v1/logs
//   with a separate key (cloud.js). The only read is /api/cloud/<kind>, which
//   needs the Mac's key and returns cloud-session rows for the Mac to pull.
//
// Upload handling is in ingest.js and cloud.js.

import { cloudIngest, cloudPull } from "./cloud.js";
import { costRows } from "./cost.js";
import { ingest } from "./ingest.js";
import { json, JSON_TYPE, NO_STORE } from "./shared.js";

// ── Cloudflare Access ────────────────────────────────────────────────────────
const b64url = (text) => Uint8Array.from(atob(text.replace(/-/g, "+").replace(/_/g, "/")), (c) => c.charCodeAt(0));
const decodePart = (part) => JSON.parse(new TextDecoder().decode(b64url(part)));
let certs = { keys: [], fetchedAt: 0 };
const CERTS_TTL_MS = 3600000;
const CERTS_PATH = "/cdn-cgi/access/certs";

async function accessKeys(teamUrl) {
  if (Date.now() - certs.fetchedAt > CERTS_TTL_MS) {
    const response = await fetch(new URL(CERTS_PATH, teamUrl));
    certs = { keys: (await response.json()).keys ?? [], fetchedAt: Date.now() };
  }
  return certs.keys;
}

/** The signed-in email, or null. Checks signature, audience, issuer and expiry. */
async function viewer(request, env) {
  if (!env.ACCESS_TEAM_URL || !env.ACCESS_AUD) return null;
  const token = request.headers.get("cf-access-jwt-assertion");
  if (!token || token.split(".").length !== 3) return null;
  try {
    const [head, body, signature] = token.split(".");
    const header = decodePart(head);
    const claims = decodePart(body);
    const audiences = [].concat(claims.aud);
    if (!audiences.includes(env.ACCESS_AUD) || claims.iss !== env.ACCESS_TEAM_URL) return null;
    if (!claims.exp || claims.exp * 1000 < Date.now()) return null;
    const jwk = (await accessKeys(env.ACCESS_TEAM_URL)).find((k) => k.kid === header.kid);
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
      if (request.method === "POST" && url.pathname === "/v1/logs") return cloudIngest(request, env);
      const pull = url.pathname.match(/^\/api\/cloud\/([a-z]+)$/);
      if (request.method === "GET" && pull) return cloudPull(request, env, pull[1]);
      return new Response("Not found", { status: 404, headers: NO_STORE });
    }

    if (url.pathname.startsWith("/api/")) {
      if (!(await viewer(request, env))) return json({ error: "Sign in through Cloudflare Access to see this data." }, 403);
      if (url.pathname === "/api/report") return report(url, env);
      if (url.pathname === "/api/machines") return machines(env);
      if (url.pathname === "/api/cost-rows") return costRows(url, env);
      return json({ error: "not found" }, 404);
    }

    return env.ASSETS.fetch(request);
  },
};
