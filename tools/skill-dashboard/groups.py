"""Skill groups (SEO, Front-end, Marketing, ...).

Two layers decide a skill's group:
  1. your own choices, made on the dashboard and kept in dataDir/groups.json
     ({"groups": [{"id", "name"}], "assign": {skill id: group id}});
  2. the starting rules in config.json `groups`: the first rule with a
     pattern matching the skill id wins (shell-style: "seo-*", "vercel:*").
A skill neither covers lands in "other".

Your choices live in dataDir rather than config.json so that moving a skill
between groups never rewrites a file in the repo, and a `git pull` of new
default rules never undoes them.
"""

import json
import re
from fnmatch import fnmatchcase

OTHER = "other"
SLUG = re.compile(r"[^a-z0-9]+")


def _read(cfg):
    try:
        data = json.loads(cfg["paths"]["groups"].read_text())
    except (OSError, ValueError):
        data = {}
    return {"groups": data.get("groups", []), "assign": data.get("assign", {})}


def _write(cfg, data):
    path = cfg["paths"]["groups"]
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1, sort_keys=True))
    tmp.replace(path)


def all_groups(cfg):
    """Every group in display order: rule groups, then your own, then Other."""
    mine = _read(cfg)
    groups = [{"id": g["id"], "name": g["name"], "custom": False} for g in cfg["groups"]]
    known = {g["id"] for g in groups}
    groups += [{"id": g["id"], "name": g["name"], "custom": True} for g in mine["groups"] if g["id"] not in known]
    groups.append({"id": OTHER, "name": cfg["groupsOther"], "custom": False})
    return groups


def resolver(cfg):
    """Return skill id -> group id, reading the files once."""
    mine = _read(cfg)
    valid = {g["id"] for g in all_groups(cfg)}

    def group_of(skill_id):
        chosen = mine["assign"].get(skill_id)
        if chosen in valid:
            return chosen
        for rule in cfg["groups"]:
            if any(fnmatchcase(skill_id, pattern) for pattern in rule["match"]):
                return rule["id"]
        return OTHER

    return group_of


def assign(cfg, skill_ids, group_id):
    if group_id not in {g["id"] for g in all_groups(cfg)}:
        raise ValueError(f"{group_id} is not a group")
    data = _read(cfg)
    for skill_id in skill_ids:
        data["assign"][skill_id] = group_id
    _write(cfg, data)
    return len(skill_ids)


def create(cfg, name):
    name = name.strip()
    if not name:
        raise ValueError("a group needs a name")
    existing = {g["id"]: g for g in all_groups(cfg)}
    for group in existing.values():
        if group["name"].lower() == name.lower():
            return group["id"]
    base = SLUG.sub("-", name.lower()).strip("-") or "group"
    group_id, n = base, 2
    while group_id in existing:
        group_id, n = f"{base}-{n}", n + 1
    data = _read(cfg)
    data["groups"].append({"id": group_id, "name": name})
    _write(cfg, data)
    return group_id
