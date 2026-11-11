"""Joins the ledger, the inventory and the MCP status into the one JSON payload
the page renders.

Matching a logged name to an installed skill: an exact id first
("vercel:deploy", "cro"), then a bare name when exactly one installed skill
carries it, since the model sometimes calls a plugin skill without its prefix.
A model call that matches nothing is still counted, under a "not on disk"
row: it was a built-in skill or one since removed. A typed slash command that
matches nothing is dropped, because that is how /model, /mcp and the other
built-in commands fall away without a list of them living here.
"""

import json
from urllib.parse import urlparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePath

import groups
import mcp
from actions import available_actions, trash_entries
from ledger import ledger_rows
from cost import CLOUD_PREFIX, cloud_project_name, cost_meta, cost_rows, token_projects
from usage import project_names, projects_summary, skill_sessions


def _when(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None


def _resolver(records):
    by_id = {r["id"]: r["id"] for r in records}
    names = defaultdict(set)
    for r in records:
        names[r["name"]].add(r["id"])

    def resolve(name):
        if name in by_id:
            return by_id[name]
        bare = name.split(":")[-1]
        ids = names.get(bare, set())
        return next(iter(ids)) if len(ids) == 1 else None

    return resolve


def _update_groups(records):
    """One entry per thing to act on: a plugin with many skills is one update."""
    plugins, skills = {}, []
    for r in records:
        u = r["update"]
        if u["status"] not in ("update", "drift"):
            continue
        if r["source"] == "plugin":
            entry = plugins.setdefault(u["pluginKey"], {
                "kind": "plugin", "plugin": r["plugin"], "skills": 0, "actions": available_actions(r), **u})
            entry["skills"] += 1
        else:
            skills.append({"kind": "skill", "id": r["id"], "name": r["name"], "source": r["source"],
                           "actions": available_actions(r), **u})
    return sorted(plugins.values(), key=lambda p: p["plugin"]) + sorted(skills, key=lambda s: s["name"])


def _read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def _group_counts(all_groups, skills):
    count, uses = Counter(), Counter()
    for s in skills:
        count[s["group"]] += 1
        uses[s["group"]] += s["uses"]
    return [{**g, "skills": count[g["id"]], "uses": uses[g["id"]]} for g in all_groups]


USE_COUNTS = ("uses", "usesRecent", "viaModel", "viaSlash", "viaSubagent")


def _tally(events, recent_from, previous_from, chart_from):
    """Use counts per skill, total uses by period, and uses per local day since chart_from."""
    counts, totals, daily = defaultdict(Counter), Counter(invocations=0, invocationsRecent=0, invocationsPrevious=0), Counter()
    for when, skill_id, event in events:
        c = counts[skill_id]
        c["uses"] += 1
        c["viaModel" if event.get("via") == "model" else "viaSlash"] += 1
        c["viaSubagent"] += 1 if event.get("subagent") else 0
        totals["invocations"] += 1
        if when >= recent_from:
            c["usesRecent"] += 1
            totals["invocationsRecent"] += 1
        elif when >= previous_from:
            totals["invocationsPrevious"] += 1
        if (day := when.astimezone().date()) >= chart_from:
            daily[day] += 1
    return counts, totals, daily


def _cloud_share(events, periods):
    """The counts that came from cloud sessions, in the shape the report gives them."""
    counts, totals, daily = _tally([e for e in events if (e[2].get("project") or "").startswith(CLOUD_PREFIX)], *periods)
    return {"skills": {sid: dict(c) for sid, c in counts.items()}, "kpis": dict(totals),
            "daily": {d.isoformat(): n for d, n in daily.items()}}


def build_report(cfg, records, meta, sync_result):
    win = cfg["windows"]
    now = datetime.now(timezone.utc)
    recent_from = now - timedelta(days=win["recentDays"])
    previous_from = recent_from - timedelta(days=win["recentDays"])
    resolve = _resolver(records)
    rows = {r["id"]: r for r in records}

    events, model_names = [], set()
    logged = ledger_rows(cfg, "events")
    for event in logged:
        if event.get("via") == "model":
            model_names.add(event["skill"])
    for event in logged:
        skill_id = resolve(event["skill"])
        if not skill_id:
            if event.get("via") != "model" and event["skill"] not in model_names:
                continue  # a built-in slash command
            skill_id = event["skill"]
            rows.setdefault(skill_id, {
                "id": skill_id, "name": skill_id.split(":")[-1], "kind": "skill", "source": "builtin", "description": "",
                "version": None, "path": None, "lastChanged": None, "enabled": True,
                "update": {"status": "builtin", "reason": "not-on-disk"}})
        when = _when(event.get("ts"))
        if when:
            events.append((when, skill_id, event))

    stats = defaultdict(lambda: {"byProject": Counter(), "bySession": Counter(), "sessionLast": {}, "first": None, "last": None})
    session_project = {}
    chart_from = (now - timedelta(days=win["chartDays"] - 1)).astimezone().date()
    periods = (recent_from, previous_from, chart_from)
    counts, totals, daily = _tally(events, *periods)
    for when, skill_id, event in events:
        s = stats[skill_id]
        if event.get("project"):
            s["byProject"][event["project"]] += 1
        sid = event.get("session")
        if sid:
            s["bySession"][sid] += 1
            s["sessionLast"][sid] = max(s["sessionLast"].get(sid, when), when)
            session_project.setdefault(sid, event.get("project"))
        s["first"] = min(s["first"] or when, when)
        s["last"] = max(s["last"] or when, when)

    names = project_names({e.get("project") for _, _, e in events} | token_projects(cfg))
    names.update({path: cloud_project_name(path) for path in names if path and path.startswith(CLOUD_PREFIX)})
    titles = _read_json(cfg["paths"]["sessions"])
    group_of = groups.resolver(cfg)
    per_skill = cfg["ui"]["sessionsPerSkill"]
    skills = []
    for skill_id, r in rows.items():
        s = stats.get(skill_id)
        skills.append({
            **{k: r.get(k) for k in ("id", "name", "kind", "plugin", "source", "description", "version",
                                     "lastChanged", "addedAt", "enabled", "update", "inRepo")},
            "group": group_of(skill_id),
            "byProject": dict(s["byProject"]) if s else {},
            "sessions": skill_sessions(s["bySession"], s["sessionLast"], session_project, titles, names, per_skill) if s else [],
            **{k: counts[skill_id][k] for k in USE_COUNTS},
            "projects": len(s["byProject"]) if s else 0,
            "firstUsed": s["first"].isoformat() if s else None,
            "lastUsed": s["last"].isoformat() if s else None,
            "actions": available_actions(r),
        })
    skills.sort(key=lambda x: (-x["uses"], x["name"]))

    installed = [x for x in skills if x["source"] in ("plugin", "personal", "account")]
    updates = _update_groups(records)
    mcp_status = mcp.cached(cfg)
    servers = (mcp_status or {}).get("servers", [])
    days = [chart_from + timedelta(days=i) for i in range(win["chartDays"])]
    recent = sorted(events, key=lambda e: e[0], reverse=True)[: win["recentEvents"]]
    first_event = min((e[0] for e in events), default=None)

    return {
        "generatedAt": now.isoformat(),
        "windows": win,
        "links": cfg["links"],
        # What the cloud setup guide names; never the key itself.
        "cloudSetup": {"host": urlparse(cfg["cloud"]["ingestUrl"]).hostname,
                       "envFile": str(cfg["paths"]["cloudEnvFile"]).replace(str(Path.home()), "~")},
        "ui": cfg["ui"],
        "paths": {"trash": str(cfg["paths"]["trash"]).replace(str(Path.home()), "~", 1)},
        "kpis": {
            "installed": len(installed),
            "used": sum(1 for x in installed if x["uses"]),
            "unused": sum(1 for x in installed if not x["uses"]),
            "builtinUsed": sum(1 for x in skills if x["source"] == "builtin" and x["uses"]),
            **totals,
            "updates": sum(1 for u in updates if u["status"] == "update"),
            "mcpTotal": len(servers),
            "mcpAttention": sum(1 for s in servers if s["status"] != "connected"),
        },
        "daily": [{"date": d.isoformat(), "count": daily.get(d, 0)} for d in days],
        "recent": [{"ts": when.isoformat(), "id": skill_id, "name": rows[skill_id]["name"],
                    "source": rows[skill_id]["source"], "via": event.get("via"),
                    "subagent": bool(event.get("subagent")),
                    "project": PurePath(event["project"]).name if event.get("project") else None}
                   for when, skill_id, event in recent],
        "skills": skills,
        "projects": projects_summary(events, names, lambda sid: rows[sid]["name"]),
        # Priced in the page (web/cost-model.js); online, live rows from the console replace these.
        "costRows": (rows := cost_rows(cfg, titles)),
        "costMeta": cost_meta(cfg, {r["p"]: names.get(r["p"], r["p"]) for r in rows}),
        # The cloud sessions' part of the counts above. Every Mac pulls the same cloud
        # sessions, so web/combine.js keeps them from one Mac when it adds Macs together.
        "cloudShare": _cloud_share(events, periods),
        "groups": _group_counts(groups.all_groups(cfg), skills),
        "updates": updates,
        "mcp": mcp_status,
        "trash": trash_entries(cfg),
        "coverage": {
            "since": first_event.isoformat() if first_event else None,
            "transcripts": (sync_result or {}).get("transcripts"),
            "lastSync": (sync_result or {}).get("lastSync"),
            **meta,
        },
    }


if __name__ == "__main__":
    import sys
    sys.dont_write_bytecode = True
    from config import load_config
    from inventory import build_inventory
    from ledger import sync
    cfg = load_config()
    result = sync(cfg)
    recs, info = build_inventory(cfg)
    print(json.dumps(build_report(cfg, recs, info, result), indent=1)[:4000])
