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
from datetime import date, datetime, timedelta

TOKEN_KINDS = ("input", "output", "cacheWrite", "cacheRead")
ALL = "all"  # the all-time period's id; months use "YYYY-MM"


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


class _Period:
    """Everything the page shows for one month, or for all time."""

    def __init__(self):
        self.total = _bucket()
        self.kinds = dict.fromkeys(TOKEN_KINDS, 0.0)
        self.series = defaultdict(float)
        self.projects, self.sessions, self.models = defaultdict(_bucket), defaultdict(_bucket), defaultdict(_bucket)

    def add(self, row, split, cost, tokens, when, slot, model):
        session = row.get("session")
        _add(self.total, cost, tokens, when, session)
        for kind, value in split.items():
            self.kinds[kind] += value
        self.series[slot] += cost
        _add(self.projects[row.get("project") or ""], cost, tokens, when, session)
        if session:
            _add(self.sessions[session], cost, tokens, when, session)
            self.sessions[session].setdefault("project", row.get("project"))
        _add(self.models[model], cost, tokens, when, session)


def _month_days(month, first_day, today):
    """Every day of `month` ("2026-11"), from its first day with data at the earliest, to today at the latest."""
    year, number = map(int, month.split("-"))
    start = max(date(year, number, 1), first_day)
    end = min(date(year + number // 12, number % 12 + 1, 1) - timedelta(days=1), today)
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def _months(first, last):
    """Month ids from `first` to `last` inclusive."""
    out, (year, number) = [], map(int, first.split("-"))
    while f"{year:04d}-{number:02d}" <= last:
        out.append(f"{year:04d}-{number:02d}")
        year, number = (year + 1, 1) if number == 12 else (year, number + 1)
    return out


def build_cost(cfg, names, titles, now):
    """The cost section of the report: one breakdown per month, newest first, then all time.
    `names` maps project paths to display names."""
    pricing, win = cfg["pricing"], cfg["windows"]
    recent_from = now - timedelta(days=win["recentDays"])
    previous_from = recent_from - timedelta(days=win["recentDays"])
    this_month = now.astimezone().strftime("%Y-%m")
    totals = {"all": 0.0, "recent": 0.0, "previous": 0.0, "month": 0.0}
    periods = defaultdict(_Period)
    unpriced = defaultdict(int)
    first_day = None
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
        local = when.astimezone()
        month = local.strftime("%Y-%m")
        first_day = min(first_day or local.date(), local.date())
        totals["all"] += cost
        if when >= recent_from:
            totals["recent"] += cost
        elif when >= previous_from:
            totals["previous"] += cost
        if month == this_month:
            totals["month"] += cost
        periods[month].add(row, split, cost, tokens, when, local.date().isoformat(), model)
        periods[ALL].add(row, split, cost, tokens, when, month, model)

    def rows(buckets, limit=None, kind=None):
        ordered = sorted(buckets.items(), key=lambda kv: -kv[1]["cost"])[:limit]
        return [{"cost": round(b["cost"], 4), "tokens": b["tokens"], "replies": b["replies"],
                 "sessions": len(b["sessions"]), "lastUsed": b["last"].isoformat(), **extra_fields(key, b, kind)}
                for key, b in ordered]

    def extra_fields(key, bucket, kind):
        if kind == "project":
            return {"path": key, "name": names.get(key, key or "—")}
        if kind == "session":
            t = titles.get(key) or {}
            return {"id": key, "title": t.get("customTitle") or t.get("aiTitle"),
                    "project": names.get(bucket.get("project"), bucket.get("project"))}
        return {"model": key}

    def period(pid, slots):
        p = periods[pid]
        return {
            "id": pid, "kind": "all" if pid == ALL else "month",
            "cost": round(p.total["cost"], 4), "tokens": p.total["tokens"], "replies": p.total["replies"],
            "sessionCount": len(p.total["sessions"]),
            "byKind": {k: round(v, 4) for k, v in p.kinds.items()},
            "series": [{"date": slot, "cost": round(p.series.get(slot, 0.0), 4)} for slot in slots],
            "projects": rows(p.projects, kind="project"),
            "sessions": rows(p.sessions, cfg["ui"]["costSessions"], kind="session"),
            "models": rows(p.models, kind="model"),
        }

    months = sorted((m for m in periods if m != ALL), reverse=True)
    today = now.astimezone().date()
    leave_out = cfg.get("costLeaveOut", {})
    return {
        "currency": pricing["currency"], "asOf": pricing["asOf"],
        "plan": {"monthlyFee": cfg["plan"]["monthlyFee"]} if cfg.get("plan", {}).get("monthlyFee") else None,
        "totals": {k: round(v, 4) for k, v in totals.items()},
        "periods": [period(m, [d.isoformat() for d in _month_days(m, first_day, today)]) for m in months]
                   + ([period(ALL, _months(months[-1], months[0]))] if months else []),
        "unpriced": dict(unpriced),
        "leftOut": {k: leave_out[k] for k in ("label", "paths")} if leave_out.get("paths") else None,
    }
