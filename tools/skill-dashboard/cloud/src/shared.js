// Small helpers both halves of the Worker use.

export const NO_STORE = { "cache-control": "no-store" };
export const JSON_TYPE = { "content-type": "application/json; charset=utf-8", ...NO_STORE };
export const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: JSON_TYPE });
export const NOW = "strftime('%Y-%m-%dT%H:%M:%SZ', 'now')";
