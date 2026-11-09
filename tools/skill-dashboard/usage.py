"""Where skills were used: per-project and per-session breakdowns for report.py.

A project is the folder a session ran in (the transcript's `cwd`). Two
projects can share a folder name ("web", "site"), so a name that repeats is
shown with its parent folder ("CRK-Splash/web") and stays unambiguous.
A session is named by the title you gave it, else the one Claude Code
generated; the page shows "Untitled session" when it has neither.
"""

from collections import Counter, defaultdict
from pathlib import PurePath


def project_names(paths):
    paths = [p for p in set(paths) if p]
    counts = Counter(PurePath(p).name for p in paths)
    names = {}
    for p in paths:
        path = PurePath(p)
        names[p] = path.name if counts[path.name] == 1 else f"{path.parent.name}/{path.name}"
    return names


def session_title(titles, session_id):
    t = titles.get(session_id) or {}
    return t.get("customTitle") or t.get("aiTitle")


def skill_sessions(by_session, session_last, session_project, titles, names, limit):
    """The skill's most recent sessions, newest first."""
    newest = sorted(by_session, key=lambda sid: session_last[sid], reverse=True)[:limit]
    return [{"id": sid, "title": session_title(titles, sid), "uses": by_session[sid],
             "project": names.get(session_project.get(sid)), "lastUsed": session_last[sid].isoformat()}
            for sid in newest]


def projects_summary(events, names, display_name):
    """One row per project: uses, distinct skills, last use and the top skills."""
    acc = defaultdict(lambda: {"uses": 0, "skills": Counter(), "last": None, "sessions": set()})
    for when, skill_id, event in events:
        project = event.get("project")
        if not project:
            continue
        p = acc[project]
        p["uses"] += 1
        p["skills"][skill_id] += 1
        p["sessions"].add(event.get("session"))
        p["last"] = max(p["last"] or when, when)
    rows = [{"path": path, "name": names.get(path, path), "uses": p["uses"], "skills": len(p["skills"]),
             "sessions": len(p["sessions"]), "lastUsed": p["last"].isoformat(),
             "top": [display_name(sid) for sid, _ in p["skills"].most_common(3)]}
            for path, p in acc.items()]
    return sorted(rows, key=lambda r: (-r["uses"], r["name"]))
