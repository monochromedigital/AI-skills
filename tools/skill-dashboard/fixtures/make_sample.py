#!/usr/bin/env python3
"""Make fixtures/sample-report.json: a made-up report for previewing the page
where there's no Claude Code history to read (a cloud session, a new Mac).

It starts from this Mac's real report so every field has a realistic shape,
then replaces whatever could identify work: every project path and name,
session id and title, cloud environment and repository, MCP server, machine
and file path, and scales every token count by a random factor per project.
Skill and plugin names are kept: they are installable packages, not work.

Before writing, it searches the result for every original project path, name,
session title and environment, and for the home folder. If any survived, it
stops without writing. Run again whenever the report's shape changes:

    python3 tools/skill-dashboard/fixtures/make_sample.py
"""

import json
import random
import sys
from pathlib import Path

sys.dont_write_bytecode = True
TOOL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOL_DIR))

from config import load_config  # noqa: E402
from export import snapshot_report  # noqa: E402

OUT = TOOL_DIR / "fixtures" / "sample-report.json"
SEED = 7  # fixed, so re-running gives the same fake names
MIN_LEN_TO_CHECK = 4  # shorter originals ("ai", "web") would match innocent words
SCALE = (0.3, 1.7)


def main():
    cfg = load_config()
    real = snapshot_report(cfg, {"id": "sample", "name": "Sample Mac"}, check_mcp=False, log=lambda *a: None)
    rng = random.Random(SEED)
    paths, sessions, envs, servers = {}, {}, {}, {}

    def path(p):
        if not p:
            return p
        if p not in paths:
            parts = p.split("/")
            if p.startswith("cloud/"):
                env = envs.setdefault(parts[1], f"env-{len(envs) + 1}") if len(parts) > 1 else "unnamed"
                paths[p] = "/".join(["cloud", env] + ([f"repo-{len(paths) + 1}"] if len(parts) > 2 else []))
            else:
                paths[p] = f"~/work/sample/project-{len(paths) + 1}"
        return paths[p]

    name = lambda p: (f"{path(p).split('/')[-1]} (cloud)" if p and p.startswith("cloud/") else path(p).split("/")[-1]) if p else p
    sid = lambda s: sessions.setdefault(s, f"session-{len(sessions) + 1}") if s else s
    title = lambda s: f"Sample session {sid(s).split('-')[1]}" if s else None
    scale = {}
    factor = lambda p: scale.setdefault(p, rng.uniform(*SCALE))

    r = real
    originals = set()
    for row in r.get("costRows", []):
        originals |= {row["p"], row.get("t") or ""}
        f = factor(row["p"])
        for k in ("in", "out", "cw5m", "cw1h", "cr"):
            row[k] = int(row[k] * f)
        row.update(p=path(row["p"]), s=sid(row["s"]), t=title(row["s"]) if row.get("t") else None)
    r["costMeta"]["names"] = {path(p): name(p) for p in r["costMeta"]["names"]}
    if r["costMeta"].get("leftOut"):
        r["costMeta"]["leftOut"] = {"label": "client work", "paths": ["~/work/clients"]}
    for s in r["skills"]:
        s["byProject"] = {path(p): n for p, n in s.get("byProject", {}).items()}
        for x in s.get("sessions", []):
            originals |= {x.get("title") or "", x.get("project") or ""}
            x.update(id=sid(x["id"]), title=title(x["id"]), project=name(next((p for p in paths if paths[p] and name(p) == x.get("project")), "")) or "project")
        for holder in (s, s.get("update") or {}):
            for k in ("path", "repoPath", "installedPath", "distFile"):
                if holder.get(k):
                    holder[k] = f"~/sample/{s['id'].split(':')[-1]}"
    for p in r["projects"]:
        originals |= {p["path"], p["name"]}
        p.update(path=path(p["path"]), name=name(p["path"]))
    for e in r["recent"]:
        originals.add(e.get("project") or "")
        e["project"] = "project"
    for u in r.get("updates", []):
        for k in ("repoPath", "installedPath", "distFile"):
            if u.get(k):
                u[k] = f"~/sample/{u.get('skill') or u.get('id')}"
    if r.get("mcp"):
        r["mcp"]["checkedFrom"] = "~"
        for m in r["mcp"]["servers"]:
            originals |= {m["name"], m.get("target") or ""}
            fake = servers.setdefault(m["name"], f"server-{len(servers) + 1}")
            m.update(name=fake, label=fake, target=f"https://mcp.example.com/{fake}")
    originals |= set(envs)
    r.update(machine={"id": "sample", "name": "Sample Mac"}, paths={"trash": "~/sample/trash"}, trash=[], readOnly=True)

    text = json.dumps(r, indent=1)
    home = str(Path.home())
    # Skill ids, names and descriptions are kept on purpose; search everything else.
    kept = ("id", "name", "description", "plugin", "kind", "source", "version", "group")
    checked = json.dumps({**r, "projects": [{k: v for k, v in x.items() if k != "top"} for x in r["projects"]], "skills": [{k: v for k, v in s.items() if k not in kept} for s in r["skills"]],
                          "groups": [], "recent": [{k: v for k, v in e.items() if k not in kept} for e in r["recent"]],
                          "updates": [{k: v for k, v in u.items() if k not in kept + ("skill", "target")} for u in r.get("updates", [])]})
    leaks = sorted(o for o in originals if len(o) >= MIN_LEN_TO_CHECK and o in checked)
    if "~/Desktop" in text:
        leaks.append("~/Desktop")
    if home in text or leaks:
        sys.exit(f"Not written: {len(leaks)} real names survived, e.g. {leaks[:3]}" + (" and the home folder" if home in text else ""))
    OUT.write_text(text + "\n")
    print(f"Wrote {OUT.relative_to(TOOL_DIR)}: {len(paths)} projects, {len(sessions)} sessions, {len(r['skills'])} skills")


if __name__ == "__main__":
    main()
