"""What your Claude Code usage would cost at Anthropic API list prices.

Each line of tokens.jsonl is one Claude reply with its token counts. Its cost:

    input × input price
  + output × output price
  + cache writes × input price × 1.25 (5-minute cache) or × 2 (1-hour cache)
  + cache reads × cache-read price

all per million tokens, from `pricing` in config.json (dated, with its
source). On a Claude subscription you pay a flat fee, so this is what the same
work would cost on the API: a fair way to compare projects and sessions, not
a bill. Replies from a model with no listed price are counted as "unpriced"
and shown, never silently priced at zero; `pricing.free` names models that
really cost nothing (Claude Code's "<synthetic>" placeholder replies).
Folders in `costLeaveOut` (and everything under them) are left out entirely:
work someone else pays for. Skill uses there still count elsewhere.
"""

import json
import os
from collections import defaultdict
from datetime import datetime, timedelta

TOKEN_KINDS = ("input", "output", "cacheWrite", "cacheRead")


def _when(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None


def reply_cost(row, price, multiplier):
    """Dollar cost of one reply, split by token kind."""
    m = 1_000_000
    return {
        "input": row.get("in", 0) * price["input"] / m,
        "output": row.get("out", 0) * price["output"] / m,
        "cacheWrite": (row.get("cw5m", 0) * multiplier["5m"] + row.get("cw1h", 0) * multiplier["1h"]) * price["input"] / m,
        "cacheRead": row.get("cr", 0) * price["cacheRead"] / m,
    }


def left_out(cfg):
    """A test for projects kept out of cost: the `costLeaveOut` folders and their subfolders.
    Takes absolute or ~-shortened paths, since uploads are shortened first."""
    roots = [os.path.expanduser(p).rstrip("/") for p in cfg.get("costLeaveOut", {}).get("paths", [])]

    def test(project):
        path = os.path.expanduser(project or "")
        return bool(project) and any(path == r or path.startswith(r + "/") for r in roots)
    return test


def _bucket():
    return {"cost": 0.0, "tokens": 0, "replies": 0, "last": None, "sessions": set()}


def _add(bucket, cost, tokens, when, session):
    bucket["cost"] += cost
    bucket["tokens"] += tokens
    bucket["replies"] += 1
    bucket["last"] = max(bucket["last"] or when, when)
    if session:
        bucket["sessions"].add(session)


def token_projects(cfg):
    """Every project folder that has token usage, so names can be made once for all sections."""
    paths = set()
    try:
        with open(cfg["paths"]["tokens"], encoding="utf-8") as f:
            for line in f:
                try:
                    paths.add(json.loads(line).get("project"))
                except ValueError:
                    continue
    except OSError:
        pass
    paths.discard(None)
    return paths


def build_cost(cfg, names, titles, now):
    """The cost section of the report. `names` maps project paths to display names."""
    pricing, win = cfg["pricing"], cfg["windows"]
    recent_from = now - timedelta(days=win["recentDays"])
    previous_from = recent_from - timedelta(days=win["recentDays"])
    chart_from = (now - timedelta(days=win["chartDays"] - 1)).astimezone().date()
    month_start = now.astimezone().date().replace(day=1)

    totals = {"all": 0.0, "recent": 0.0, "previous": 0.0, "month": 0.0}
    kinds = dict.fromkeys(TOKEN_KINDS, 0.0)
    daily = defaultdict(float)
    projects, sessions, models = defaultdict(_bucket), defaultdict(_bucket), defaultdict(_bucket)
    unpriced = defaultdict(int)
    skip = left_out(cfg)

    try:
        lines = cfg["paths"]["tokens"].read_text(encoding="utf-8").splitlines()
    except OSError:
        lines = []
    for line in lines:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        when = _when(row.get("ts"))
        model = row.get("model") or "unknown"
        if not when or model in pricing["free"] or skip(row.get("project")):
            continue
        price = pricing["models"].get(model)
        if not price:
            unpriced[model] += 1
            continue
        split = reply_cost(row, price, pricing["cacheWriteMultiplier"])
        cost = sum(split.values())
        tokens = sum(row.get(k, 0) for k in ("in", "out", "cw5m", "cw1h", "cr"))
        for kind, value in split.items():
            kinds[kind] += value
        totals["all"] += cost
        if when >= recent_from:
            totals["recent"] += cost
        elif when >= previous_from:
            totals["previous"] += cost
        day = when.astimezone().date()
        if day >= month_start:
            totals["month"] += cost
        if day >= chart_from:
            daily[day] += cost
        session = row.get("session")
        _add(projects[row.get("project") or ""], cost, tokens, when, session)
        if session:
            _add(sessions[session], cost, tokens, when, session)
            sessions[session].setdefault("project", row.get("project"))
        _add(models[model], cost, tokens, when, session)

    def rows(buckets, limit=None, **extra):
        ordered = sorted(buckets.items(), key=lambda kv: -kv[1]["cost"])[:limit]
        return [{"cost": round(b["cost"], 4), "tokens": b["tokens"], "replies": b["replies"],
                 "sessions": len(b["sessions"]), "lastUsed": b["last"].isoformat(), **extra_fields(key, b, extra)}
                for key, b in ordered]

    def extra_fields(key, bucket, extra):
        kind = extra.get("kind")
        if kind == "project":
            return {"path": key, "name": names.get(key, key or "—")}
        if kind == "session":
            t = titles.get(key) or {}
            return {"id": key, "title": t.get("customTitle") or t.get("aiTitle"),
                    "project": names.get(bucket.get("project"), bucket.get("project"))}
        return {"model": key}

    days = [chart_from + timedelta(days=i) for i in range(win["chartDays"])]
    return {
        "currency": pricing["currency"], "asOf": pricing["asOf"],
        "totals": {k: round(v, 4) for k, v in totals.items()},
        "byKind": {k: round(v, 4) for k, v in kinds.items()},
        "daily": [{"date": d.isoformat(), "cost": round(daily.get(d, 0.0), 4)} for d in days],
        "projects": rows(projects, kind="project"),
        "sessions": rows(sessions, cfg["ui"]["costSessions"], kind="session"),
        "models": rows(models, kind="model"),
        "unpriced": dict(unpriced),
        "leftOut": {k: cfg["costLeaveOut"][k] for k in ("label", "paths")} if cfg.get("costLeaveOut", {}).get("paths") else None,
    }
