"""Token usage for the cost view, summed and ready to price.

Each line of tokens.jsonl is one Claude reply with its token counts. This
module sums them per day, project, session, model and source; the page prices
them (web/cost-model.js) at Anthropic API list prices from `pricing` in
config.json. On a Claude subscription you pay a flat fee, so this is what the
same work would cost on the API: a fair way to compare projects and sessions,
not a bill. Folders in `costLeaveOut` (and everything under them) are left out
entirely: work someone else pays for. Skill uses there still count elsewhere.
"""

import os
from collections import defaultdict
from datetime import datetime

from ledger import ledger_rows

CLOUD = "cloud"  # entrypoint on rows pulled from cloud sessions (cloud_pull.py)
CLOUD_PREFIX = "cloud/"  # their project: "cloud/<environment>/<repository>" (cloud/src/cloud.js)


def cloud_project_name(project):
    """A display name for a cloud project path: its repository, or its environment when no repository was sent."""
    parts = project.split("/")
    return f"{parts[2] if len(parts) > 2 else parts[1]} (cloud)"


def _when(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None


def left_out(cfg):
    """A test for projects kept out of cost: the `costLeaveOut` folders and their subfolders.
    Takes absolute or ~-shortened paths, since uploads are shortened first."""
    roots = [os.path.expanduser(p).rstrip("/") for p in cfg.get("costLeaveOut", {}).get("paths", [])]

    def test(project):
        path = os.path.expanduser(project or "")
        return bool(project) and any(path == r or path.startswith(r + "/") for r in roots)
    return test


TOKEN_FIELDS = ("in", "out", "cw5m", "cw1h", "cr")


def cost_rows(cfg, titles):
    """Token usage summed per local day, project, session, model and source ("mac" or "cloud"):
    what the page's cost model (web/cost-model.js) prices. The Worker serves rows of the same
    shape from the console's database (cloud/src/cost.js), so both pages price the same way.
    Leaves out the costLeaveOut folders. `titles` is sessions.json."""
    skip = left_out(cfg)
    rows = {}
    for row in ledger_rows(cfg, "tokens"):
        when = _when(row.get("ts"))
        if not when or skip(row.get("project")):
            continue
        day = when.astimezone().date().isoformat()
        source = "cloud" if row.get("entrypoint") == CLOUD else "mac"
        key = (day, row.get("project") or "", row.get("session"), row.get("model") or "unknown", source)
        r = rows.get(key)
        if r is None:
            r = rows[key] = {"d": day, "p": key[1], "s": key[2], "m": key[3], "src": source, "n": 0,
                             **dict.fromkeys(TOKEN_FIELDS, 0), "last": when}
        r["n"] += 1
        for field in TOKEN_FIELDS:
            r[field] += row.get(field) or 0
        r["last"] = max(r["last"], when)
    out = []
    for r in rows.values():
        t = titles.get(r["s"]) or {}
        out.append({**r, "last": r["last"].isoformat(), "t": t.get("customTitle") or t.get("aiTitle")})
    return out


def cost_meta(cfg, names):
    """What the cost model needs besides the rows: prices, the plan fee, display names."""
    pricing, leave_out = cfg["pricing"], cfg.get("costLeaveOut", {})
    return {
        "currency": pricing["currency"], "asOf": pricing["asOf"],
        "models": pricing["models"], "free": pricing["free"], "cacheWriteMultiplier": pricing["cacheWriteMultiplier"],
        "plan": {"monthlyFee": cfg["plan"]["monthlyFee"]} if cfg.get("plan", {}).get("monthlyFee") else None,
        "leftOut": {k: leave_out[k] for k in ("label", "paths")} if leave_out.get("paths") else None,
        "recentDays": cfg["windows"]["recentDays"], "topSessions": cfg["ui"]["costSessions"],
        "names": names,
    }


def token_projects(cfg):
    """Every project folder that has token usage, so names can be made once for all sections."""
    return {row.get("project") for row in ledger_rows(cfg, "tokens")} - {None}
