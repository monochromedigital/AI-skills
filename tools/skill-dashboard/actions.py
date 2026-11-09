"""The things the dashboard can change, and the checks in front of each one.

Every action takes a target the page names (a plugin key, a skill id, a
server name) and looks it up again in a fresh inventory before touching
anything. A path or command from the browser is never used as given, so a
page can only ask for something that already exists in the listing.

Removal is reversible on purpose. Uninstalling a personal skill moves its
folder to dataDir/trash, and replacing one with the repo copy moves the old
copy there first; the dashboard lists the trash with a Restore button.
Plugins are the exception: they belong to Claude Code's plugin manager, so
they go through `claude plugin ...` and reinstall the same way.

Skills synced from claude.ai have no local action. Claude Code re-downloads
them every few minutes, so deleting the folder would be undone; they are
turned off on claude.ai instead (links.accountSkills).
"""

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import groups
import mcp
from inventory import IGNORED, build_inventory

TRASH_SEPARATOR = "__"
STAMP = "%Y%m%d-%H%M%S-%f"


class ActionError(Exception):
    pass


def _run(cfg, log, *args, timeout=None):
    command = [cfg["cli"]["claude"], *args]
    log("$ " + " ".join(command))
    done = subprocess.run(
        command, capture_output=True, text=True, stdin=subprocess.DEVNULL,
        timeout=timeout or cfg["cli"]["timeoutSeconds"], cwd=Path.home(),
    )
    for stream in (done.stdout, done.stderr):
        if stream.strip():
            log(stream.strip())
    if done.returncode != 0:
        raise ActionError(f"{command[1]} {command[2]} exited with code {done.returncode}")


def _find(cfg, predicate, missing):
    records, _ = build_inventory(cfg)
    match = next((r for r in records if predicate(r)), None)
    if not match:
        raise ActionError(missing)
    return match


def _inside(path, root):
    path, root = Path(path).resolve(), Path(root).resolve()
    return root in path.parents


def _to_trash(cfg, folder, log):
    trash = cfg["paths"]["trash"]
    trash.mkdir(parents=True, exist_ok=True)
    # Microseconds keep two removals in one second apart, and the exists()
    # check backs that up: shutil.move into an existing folder nests the skill
    # inside the older copy instead of failing.
    dest = trash / f"{folder.name}{TRASH_SEPARATOR}{datetime.now().strftime(STAMP)}"
    if dest.exists():
        raise ActionError(f"{dest} already exists")
    shutil.move(str(folder), str(dest))
    log(f"Moved {folder} → {dest}")
    return dest


def _copy_skill(src, dest, log):
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns(*IGNORED))
    log(f"Copied {src} → {dest}")


# ── plugins ─────────────────────────────────────────────────────────────────

def _installed_plugin(cfg, key):
    installed = json.loads((cfg["paths"]["plugins"] / "installed_plugins.json").read_text()).get("plugins", {})
    if key not in installed:
        raise ActionError(f"{key} is not an installed plugin")
    return key.partition("@")[2]


def plugin_update(cfg, key, log):
    marketplace = _installed_plugin(cfg, key)
    _run(cfg, log, "plugin", "marketplace", "update", marketplace)
    _run(cfg, log, "plugin", "update", key)
    return {"restartNeeded": True}


def plugin_uninstall(cfg, key, log):
    _installed_plugin(cfg, key)
    _run(cfg, log, "plugin", "uninstall", key)
    return {"restartNeeded": True}


# ── personal skills ─────────────────────────────────────────────────────────

def _personal(cfg, skill_id):
    record = _find(cfg, lambda r: r["source"] == "personal" and r["id"] == skill_id,
                   f"{skill_id} is not a personal skill")
    folder = Path(record["path"])
    root = cfg["paths"]["personalSkills"]
    if not _inside(folder, root) or _inside(folder, cfg["paths"]["syncedSkills"]):
        raise ActionError(f"{folder} is outside {root}")
    return record, folder


def skill_uninstall(cfg, skill_id, log):
    _, folder = _personal(cfg, skill_id)
    return {"trashed": _to_trash(cfg, folder, log).name}


def skill_update_from_repo(cfg, skill_id, log):
    record, folder = _personal(cfg, skill_id)
    repo = Path(record["update"].get("repoPath") or "")
    if not record.get("inRepo") or not _inside(repo, cfg["paths"]["repoSkills"]):
        raise ActionError(f"{skill_id} has no copy in the repo")
    backup = _to_trash(cfg, folder, log)
    _copy_skill(repo, folder, log)
    return {"trashed": backup.name}


def skill_install_from_repo(cfg, skill_id, log):
    record = _find(cfg, lambda r: r["source"] == "repo" and r["id"] == skill_id,
                   f"{skill_id} is not an uninstalled repo skill")
    repo = Path(record["path"])
    dest = cfg["paths"]["personalSkills"] / repo.name
    if dest.exists():
        raise ActionError(f"{dest} already exists")
    _copy_skill(repo, dest, log)
    return {}


def trash_entries(cfg):
    trash = cfg["paths"]["trash"]
    if not trash.is_dir():
        return []
    entries = []
    for entry in sorted(trash.iterdir(), reverse=True):
        name, _, stamp = entry.name.rpartition(TRASH_SEPARATOR)
        if entry.is_dir() and name:
            try:
                removed = datetime.strptime(stamp, STAMP).isoformat()
            except ValueError:
                removed = None
            entries.append({"entry": entry.name, "name": name, "removedAt": removed})
    return entries


def skill_restore(cfg, entry, log):
    trash = cfg["paths"]["trash"]
    known = {e["entry"]: e for e in trash_entries(cfg)}
    if entry not in known:
        raise ActionError(f"{entry} is not in the trash")
    dest = cfg["paths"]["personalSkills"] / known[entry]["name"]
    if dest.exists():
        raise ActionError(f"{dest} already exists — remove or rename it first")
    shutil.move(str(trash / entry), str(dest))
    log(f"Restored {dest}")
    return {}


# ── MCP servers ─────────────────────────────────────────────────────────────

def mcp_check(cfg, _target, log):
    result = mcp.check(cfg)
    log(f"Checked {len(result['servers'])} servers")
    return {}


def mcp_login(cfg, name, log):
    status = mcp.cached(cfg) or mcp.check(cfg)
    if name not in {s["name"] for s in status["servers"]}:
        raise ActionError(f"{name} is not a configured MCP server")
    log(f"$ {cfg['cli']['claude']} mcp login {name}")
    done = mcp.login(cfg, name)
    for stream in (done.stdout, done.stderr):
        if stream.strip():
            log(stream.strip())
    mcp.check(cfg)  # refresh so the page shows the new state either way
    if done.returncode != 0:
        raise ActionError(f"mcp login exited with code {done.returncode}")
    return {}


# ── groups ──────────────────────────────────────────────────────────────────

def _spec(target, *keys):
    if not isinstance(target, dict) or any(k not in target for k in keys):
        raise ActionError(f"expected {', '.join(keys)}")
    return [target[k] for k in keys]


def group_assign(cfg, target, log):
    ids, group_id = _spec(target, "ids", "group")
    known = {r["id"] for r in build_inventory(cfg)[0]}
    ids = [i for i in ids if isinstance(i, str) and i in known]
    try:
        count = groups.assign(cfg, ids, group_id)
    except ValueError as exc:
        raise ActionError(str(exc))
    log(f"Moved {count} skill(s) to {group_id}")
    return {"count": count}


def group_create(cfg, target, log):
    (name,) = _spec(target, "name")
    try:
        group_id = groups.create(cfg, str(name))
    except ValueError as exc:
        raise ActionError(str(exc))
    log(f"Group {group_id} ready")
    ids = target.get("ids") or []
    return {"group": group_id, **(group_assign(cfg, {"ids": ids, "group": group_id}, log) if ids else {})}


# ── bulk ────────────────────────────────────────────────────────────────────

BULKABLE = {"plugin-update", "plugin-uninstall", "skill-uninstall", "skill-update-from-repo", "skill-install-from-repo"}


def bulk(cfg, target, log):
    """Run many actions in one job: {"items": [{"action": ..., "target": ...}]}.

    Each item goes through the same function, and so the same checks, as a
    single click. One failure is logged and the rest carry on. Duplicates are
    dropped, because five skills from one plugin mean one plugin update."""
    (items,) = _spec(target, "items")
    if not isinstance(items, list):
        raise ActionError("items must be a list")
    done, failed, restart, pairs = 0, [], False, []
    # Check the shape before de-duplicating: a target that isn't a string
    # can't be a dict key, and is never a valid target anyway.
    for i in items:
        if isinstance(i, dict) and i.get("action") in BULKABLE and isinstance(i.get("target"), str):
            pairs.append((i["action"], i["target"]))
        else:
            failed.append(str(i)[:80])
            log(f"✗ {str(i)[:80]}: not allowed in bulk")
    for action, item in dict.fromkeys(pairs):
        try:
            result = ACTIONS[action][0](cfg, item, log) or {}
            restart = restart or bool(result.get("restartNeeded"))
            done += 1
        except Exception as exc:  # report and continue
            failed.append(item)
            log(f"✗ {item}: {exc}")
    if failed and not done:
        raise ActionError(f"all {len(failed)} failed")
    return {"done": done, "failed": failed, "restartNeeded": restart}


# Which lock each action takes: a browser sign-in can sit open for minutes and
# must not block a plugin update, so MCP work and skill work queue separately.
ACTIONS = {
    "plugin-update": (plugin_update, "skills"),
    "plugin-uninstall": (plugin_uninstall, "skills"),
    "skill-uninstall": (skill_uninstall, "skills"),
    "skill-update-from-repo": (skill_update_from_repo, "skills"),
    "skill-install-from-repo": (skill_install_from_repo, "skills"),
    "skill-restore": (skill_restore, "skills"),
    "mcp-check": (mcp_check, "mcp"),
    "mcp-login": (mcp_login, "mcp"),
    "group-assign": (group_assign, "groups"),
    "group-create": (group_create, "groups"),
    "bulk": (bulk, "skills"),
}


def available_actions(record):
    """The action codes the page may offer for one skill row."""
    source, status = record["source"], record["update"]["status"]
    if source == "plugin":
        return (["plugin-update"] if status == "update" else []) + ["plugin-uninstall"]
    if source == "personal":
        repo_newer = record["update"].get("reason") == "repo-newer"
        return (["skill-update-from-repo"] if repo_newer else []) + ["skill-uninstall"]
    if source == "repo":
        return ["skill-install-from-repo"]
    return []
