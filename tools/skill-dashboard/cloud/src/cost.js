// GET /api/cost-rows?tz=<minutes east of UTC>: token usage summed per local day,
// project, session, model and source, the same rows cost.py makes on the Mac,
// so the console prices them live with the page's own model (web/cost-model.js).
// Cloud sessions are as current as their last report; each Mac as of its last
// sync. SQLite sums and serialises the rows (json_group_array), so the Worker
// passes the text through without parsing it.
//
// Folders in costLeaveOut (config.json) are left out here too: rows uploaded
// before that rule existed stay in the database but are never counted.

import config from "../../config.json";
import { JSON_TYPE } from "./shared.js";

const MAX_OFFSET_MINUTES = 840; // UTC+14, the furthest zone from UTC
const CLOUD_MACHINE = "cloud";
const leaveOut = (config.costLeaveOut?.paths ?? []).map((p) => p.replace(/\/$/, ""));
const leaveOutSql = leaveOut.map((_, i) => `AND u.project IS NOT ?${i * 2 + 2} AND u.project NOT LIKE ?${i * 2 + 3} ESCAPE '\\'`).join(" ");
const leaveOutArgs = leaveOut.flatMap((p) => [p, `${p.replace(/[\\%_]/g, "\\$&")}/%`]);

const ROWS = `SELECT json_group_array(json_object('d', d, 'p', p, 's', s, 'm', m, 'src', src, 'n', n,
    'in', i, 'out', o, 'cw5m', w5, 'cw1h', w1, 'cr', r, 'last', last, 't', t)) AS rows
  FROM (
    SELECT date(u.ts, ?1) AS d, coalesce(u.project, '') AS p, u.session_id AS s, coalesce(u.model, 'unknown') AS m,
      CASE WHEN u.machine_id = '${CLOUD_MACHINE}' THEN 'cloud' ELSE 'mac' END AS src,
      count(*) AS n, sum(u.input_tokens) AS i, sum(u.output_tokens) AS o, sum(u.cache_write_5m) AS w5,
      sum(u.cache_write_1h) AS w1, sum(u.cache_read) AS r, max(u.ts) AS last,
      (SELECT title FROM sessions WHERE sessions.id = u.session_id) AS t
    FROM token_usage u
    WHERE 1 ${leaveOutSql}
    GROUP BY d, p, s, m, src
  )`;

export async function costRows(url, env) {
  const offset = Math.trunc(Number(url.searchParams.get("tz")) || 0);
  const minutes = Math.max(-MAX_OFFSET_MINUTES, Math.min(MAX_OFFSET_MINUTES, offset));
  const modifier = `${minutes >= 0 ? "+" : ""}${minutes} minutes`;
  const row = await env.DB.prepare(ROWS).bind(modifier, ...leaveOutArgs).first();
  return new Response(row?.rows ?? "[]", { headers: JSON_TYPE });
}
