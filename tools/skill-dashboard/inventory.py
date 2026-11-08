"""Skill inventory: every skill on this Mac, where it came from, and whether a
newer copy exists somewhere.

Each source answers "is there an update?" differently:

  plugin    ~/.claude/plugins/installed_plugins.json. Compared with the
            marketplace's catalogue twice: the copy Claude Code keeps on disk,
            and (when updates.checkRemote is on) the catalogue on GitHub. The
            second matters because the local copy only refreshes when someone
            runs `claude plugin marketplace update`; one marketplace here had
            not refreshed in six weeks while its plugins moved five minor
            versions. Plugins with no version number are compared by content.
  personal  ~/.claude/skills/<name>. Nothing records where these came from, so
            the only update sources are this repo (same skill name) and any
            GitHub path listed under updates.upstream in config.json.
  account   ~/.claude/skills/synced — skills enabled on claude.ai. Claude Code
            re-syncs these itself; the only check is against this repo.
  repo      skills/ in this repo; listed as not installed when no installed
            skill shares its name.

The server returns reason codes and raw values only. Every sentence the
dashboard shows is written in web/content.js.
"""

import hashlib
import json
import os
import re
import ssl
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

IGNORED = {".DS_Store", "__pycache__", ".git", "node_modules"}
SKILL_FILE = "SKILL.md"
BLOCK_SCALARS = {">", "|", ">-", "|-", ">+", "|+"}
SEMVER = re.compile(r"^v?\d+(\.\d+)*$")
MANIFEST = ".claude-plugin/marketplace.json"
PLUGIN_MANIFEST = ".claude-plugin/plugin.json"


# ── small file helpers ──────────────────────────────────────────────────────

def _json(path, default=None):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return default


def _iso(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if epoch else None


def _files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in IGNORED)
        for name in sorted(filenames):
            if name not in IGNORED:
                yield Path(dirpath) / name


def tree_digest(root):
    """Content hash of a folder: same files, same bytes, same digest."""
    root = Path(root)
    if not root.is_dir():
        return None
    h = hashlib.sha256()
    for path in _files(root):
        h.update(str(path.relative_to(root)).encode() + b"\0")
        h.update(path.read_bytes() + b"\0")
    return h.hexdigest()


def created(path):
    """When a folder appeared on this Mac (birth time on macOS, ctime elsewhere)."""
    try:
        st = Path(path).stat()
    except OSError:
        return None
    return _iso(getattr(st, "st_birthtime", None) or st.st_ctime)


def last_changed(root):
    newest = 0.0
    for path in _files(root):
        try:
            newest = max(newest, path.stat().st_mtime)
        except OSError:
            continue
    return newest


def read_frontmatter(skill_md):
    """Just enough YAML for name, description and version (top-level or metadata.version)."""
    try:
        lines = Path(skill_md).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return {}
    if not lines or lines[0].strip() != "---":
        return {}
    meta, folding, in_metadata = {}, None, False
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if not line.strip():
            continue
        if not line[0].isspace():
            key, _, value = line.partition(":")
            key, value = key.strip(), value.strip()
            in_metadata, folding = key == "metadata", None
            if value in BLOCK_SCALARS:
                folding, meta[key] = key, ""
            elif not in_metadata:
                meta[key] = value.strip("'\"")
        elif in_metadata:
            key, _, value = line.strip().partition(":")
            if key.strip() == "version":
                meta["metadataVersion"] = value.strip().strip("'\"")
        elif folding:
            meta[folding] = (meta[folding] + " " + line.strip()).strip()
    meta["version"] = meta.get("version") or meta.get("metadataVersion")
    return meta


def _version_key(value):
    return tuple(int(n) for n in re.findall(r"\d+", value)) if value and SEMVER.match(value) else None


def is_newer(latest, current):
    a, b = _version_key(latest), _version_key(current)
    return a > b if a is not None and b is not None else None


def _record(**fields):
    base = {"kind": "skill", "enabled": True, "update": {"status": "unknown"}}
    base.update(fields)
    return base


def _skill_dirs(root):
    root = Path(root)
    if not root.is_dir():
        return []
    return sorted(p.parent for p in root.glob(f"*/{SKILL_FILE}"))


def _command_files(root):
    """Command markdown files; a leading underscore marks shared partials, not commands."""
    root = Path(root)
    if not root.is_dir():
        return []
    return sorted(p for p in root.glob("*.md") if not p.name.startswith("_"))


# ── remote catalogues and upstream files, cached ────────────────────────────

def _ssl_context(bundles):
    """python.org's macOS build ships without CA certificates until someone runs
    its 'Install Certificates' script, so every HTTPS call fails. Fall back to
    the first certificate bundle that exists (macOS keeps one at /etc/ssl)."""
    context = ssl.create_default_context()
    if context.cert_store_stats().get("x509_ca"):
        return context
    for bundle in bundles:
        if Path(bundle).is_file():
            return ssl.create_default_context(cafile=bundle)
    return context


def _fetch(url, timeout, context):
    request = urllib.request.Request(url, headers={"User-Agent": "skill-dashboard"})
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        return response.read()


def remote_lookups(cfg, marketplaces, force=False):
    """Fetch each GitHub marketplace catalogue and each configured upstream SKILL.md.

    Cached in dataDir for updates.cacheHours so a page load does not hit the
    network every time. Failures are recorded, never raised: an offline Mac
    still gets a dashboard, with plugin checks falling back to the local copy.
    """
    upd = cfg["updates"]
    cache_path = cfg["paths"]["remoteCache"]
    cache = _json(cache_path, {}) or {}
    # A failed fetch is retried after retryMinutes, not trusted for cacheHours.
    max_age = upd["retryMinutes"] * 60 if cache.get("errors") else upd["cacheHours"] * 3600
    fresh = time.time() - cache.get("fetchedAt", 0) < max_age
    if not upd["checkRemote"]:
        return {"manifests": {}, "upstream": {}, "errors": {}, "fetchedAt": None, "enabled": False}
    if fresh and not force:
        return {**cache, "enabled": True}

    jobs = {}
    for name, info in marketplaces.items():
        src = info.get("source", {})
        if src.get("source") == "github" and src.get("repo"):
            ref = src.get("ref", "HEAD")
            jobs[("manifest", name)] = f"{upd['rawBase']}/{src['repo']}/{ref}/{src.get('path', MANIFEST)}"
    for skill, spec in upd.get("upstream", {}).items():
        jobs[("upstream", skill)] = f"{upd['rawBase']}/{spec['repo']}/{spec.get('ref', 'HEAD')}/{spec['path']}"

    result = {"manifests": {}, "upstream": {}, "errors": {}, "fetchedAt": time.time()}
    context = _ssl_context(upd["caBundles"])

    def run(item):
        (kind, name), url = item
        try:
            return kind, name, _fetch(url, upd["timeoutSeconds"], context), None
        except Exception as exc:  # network, HTTP, DNS: all just "unavailable"
            return kind, name, None, f"{type(exc).__name__}: {exc}"

    with ThreadPoolExecutor(max_workers=max(1, len(jobs))) as pool:
        for kind, name, body, error in pool.map(run, jobs.items()):
            if error:
                result["errors"][f"{kind}:{name}"] = error
            elif kind == "manifest":
                try:
                    plugins = json.loads(body).get("plugins", [])
                    result["manifests"][name] = {p["name"]: p.get("version") for p in plugins if "name" in p}
                except ValueError as exc:
                    result["errors"][f"{kind}:{name}"] = str(exc)
            else:
                result["upstream"][name] = hashlib.sha256(body).hexdigest()

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(result))
    return {**result, "enabled": True}


# ── plugins ─────────────────────────────────────────────────────────────────

def _local_entry_version(entry, mkt_dir):
    """Latest version the on-disk catalogue knows: its version field, else the plugin's own plugin.json."""
    if not entry:
        return None, None
    if entry.get("version"):
        return entry["version"], None
    src = entry.get("source")
    if isinstance(src, str) and mkt_dir:
        plugin_dir = (mkt_dir / src).resolve()
        version = (_json(plugin_dir / PLUGIN_MANIFEST, {}) or {}).get("version")
        return version, plugin_dir
    if isinstance(src, dict) and src.get("sha"):
        return None, src["sha"]
    return None, None


def plugin_status(key, install, mkt, entry, mkt_dir, remote_version):
    current = install.get("version")
    local_version, extra = _local_entry_version(entry, mkt_dir)
    candidates = [v for v in (remote_version, local_version) if _version_key(v)]
    latest = max(candidates, key=_version_key) if candidates else None
    base = {"pluginKey": key, "marketplace": mkt, "current": current, "latest": latest}

    if latest and _version_key(current):
        if is_newer(latest, current):
            stale_local = remote_version and not is_newer(local_version, current) if local_version else bool(remote_version)
            return {**base, "status": "update", "reason": "plugin-version", "refreshMarketplace": bool(stale_local)}
        return {**base, "status": "current", "reason": "plugin-version"}
    if isinstance(extra, str) and install.get("gitCommitSha"):  # git-subdir source pinned to a sha
        same = install["gitCommitSha"].startswith(extra[:12]) or extra.startswith(install["gitCommitSha"][:12])
        return {**base, "latest": extra[:12], "status": "current" if same else "update", "reason": "plugin-commit"}
    if isinstance(extra, Path):  # no version anywhere: compare the skills themselves
        catalogue, installed = tree_digest(extra / "skills"), tree_digest(Path(install["installPath"]) / "skills")
        if catalogue and installed:
            return {**base, "status": "current" if catalogue == installed else "update", "reason": "plugin-content"}
    return {**base, "status": "unknown", "reason": "plugin-no-version"}


def plugin_records(cfg, remote):
    paths = cfg["paths"]
    installed = (_json(paths["plugins"] / "installed_plugins.json", {}) or {}).get("plugins", {})
    marketplaces = _json(paths["plugins"] / "known_marketplaces.json", {}) or {}
    enabled = (_json(paths["settings"], {}) or {}).get("enabledPlugins", {})
    catalogues = {}

    for key, installs in sorted(installed.items()):
        if not installs:
            continue
        name, _, mkt = key.partition("@")
        install = next((i for i in installs if i.get("scope") == "user"), installs[0])
        location = (marketplaces.get(mkt) or {}).get("installLocation")
        mkt_dir = Path(location) if location else None
        if mkt not in catalogues:
            manifest = _json(mkt_dir / MANIFEST, {}) if mkt_dir else {}
            catalogues[mkt] = {p.get("name"): p for p in (manifest or {}).get("plugins", [])}
        remote_version = remote["manifests"].get(mkt, {}).get(name)
        update = plugin_status(key, install, mkt, catalogues[mkt].get(name), mkt_dir, remote_version)

        shared = dict(plugin=name, source="plugin", version=install.get("version"),
                      lastChanged=install.get("lastUpdated") or install.get("installedAt"),
                      enabled=enabled.get(key, True) is not False, update=update)
        # Plugin folders are rebuilt on every update, so their birth time says
        # nothing; the install record does (lastUpdated for a skill an update added).
        shared["addedHint"] = {"first": install.get("installedAt"), "later": install.get("lastUpdated")}
        ids = set()
        for skill_dir in _skill_dirs(Path(install["installPath"]) / "skills"):
            fm = read_frontmatter(skill_dir / SKILL_FILE)
            skill = fm.get("name") or skill_dir.name
            ids.add(f"{name}:{skill}")
            yield _record(id=f"{name}:{skill}", name=skill, description=fm.get("description", ""),
                          path=str(skill_dir), **shared)
        # Plugin commands (commands/deploy.md -> /vercel:deploy) are invoked the
        # same way skills are, so they are listed and counted alongside them.
        for command in _command_files(Path(install["installPath"]) / "commands"):
            if f"{name}:{command.stem}" in ids:
                continue  # a skill and a command share the name; the skill is what runs
            yield _record(id=f"{name}:{command.stem}", name=command.stem, kind="command",
                          description=read_frontmatter(command).get("description", ""),
                          path=str(command), **shared)


# ── personal, account and repo skills ───────────────────────────────────────

def personal_records(cfg):
    root = cfg["paths"]["personalSkills"]
    synced = cfg["paths"]["syncedSkills"]
    for skill_dir in _skill_dirs(root):
        if skill_dir == synced or skill_dir.name.startswith("."):
            continue
        fm = read_frontmatter(skill_dir / SKILL_FILE)
        name = fm.get("name") or skill_dir.name
        yield _record(
            id=name, name=name, source="personal", description=fm.get("description", ""),
            version=fm.get("version"), path=str(skill_dir), lastChanged=_iso(last_changed(skill_dir)),
            addedHint=created(skill_dir),
            update={"status": "untracked", "reason": "no-source"},
        )


def account_records(cfg):
    """Skills enabled on claude.ai. Several org buckets can hold the same skill; keep the newest."""
    root = cfg["paths"]["syncedSkills"]
    prefix = cfg["synced"]["skillPrefix"]
    newest = {}
    if not root.is_dir():
        return []
    for bucket in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")):
        manifest = {s.get("name"): s for s in (_json(bucket / "manifest.json", {}) or {}).get("skills", [])}
        for skill_dir in _skill_dirs(bucket):
            fm = read_frontmatter(skill_dir / SKILL_FILE)
            name = fm.get("name") or skill_dir.name
            changed = (manifest.get(name) or {}).get("updatedAt") or _iso(last_changed(skill_dir))
            if name not in newest or (changed or "") > (newest[name]["lastChanged"] or ""):
                newest[name] = _record(
                    id=f"{prefix}:{name}", name=name, source="account", description=fm.get("description", ""),
                    version=fm.get("version"), path=str(skill_dir), lastChanged=changed, addedHint=created(skill_dir),
                    update={"status": "managed", "reason": "account-managed"},
                )
    return list(newest.values())


def repo_records(cfg):
    root = cfg["paths"]["repoSkills"]
    for skill_dir in _skill_dirs(root):
        fm = read_frontmatter(skill_dir / SKILL_FILE)
        name = fm.get("name") or skill_dir.name
        yield {"name": name, "path": skill_dir, "description": fm.get("description", ""),
               "version": fm.get("version"), "changed": last_changed(skill_dir)}


def _compare_with_repo(record, repo, dist_dir):
    installed_path = Path(record["path"])
    same = tree_digest(installed_path) == tree_digest(repo["path"])
    installed_changed = last_changed(installed_path)
    if record["source"] == "account" and record.get("lastChanged"):
        try:
            installed_changed = datetime.fromisoformat(record["lastChanged"].replace("Z", "+00:00")).timestamp()
        except ValueError:
            pass
    info = {"repoPath": str(repo["path"]), "installedPath": str(installed_path),
            "distFile": str(dist_dir / f"{repo['name']}.skill"), "skill": repo["name"]}
    if same:
        status, reason = "current", "matches-repo"
    elif repo["changed"] > installed_changed:
        status, reason = "update", "repo-newer"
    else:
        status, reason = "drift", "installed-newer"
    record["update"] = {**info, "status": status, "reason": reason, "target": record["source"]}
    record["inRepo"] = True


def _apply_upstream(record, spec, remote):
    digest = remote["upstream"].get(record["id"])
    if not digest:
        record["update"] = {"status": "unknown", "reason": "upstream-unreachable", "repo": spec["repo"]}
        return
    local = hashlib.sha256((Path(record["path"]) / SKILL_FILE).read_bytes()).hexdigest()
    record["update"] = {"status": "current" if local == digest else "update", "reason": "upstream",
                        "repo": spec["repo"], "upstreamPath": spec["path"]}


def stamp_added(cfg, records):
    """Give every skill an addedAt that never moves once recorded.

    seen.json keeps the first date each id was seen. On the very first run it
    is seeded from the folder's birth time or the plugin's install date, so
    skills installed before the dashboard existed still sort correctly; after
    that, an id that appears is new as of its plugin update or of today.
    """
    path = cfg["paths"]["seen"]
    first_run = not path.exists()
    seen = _json(path, {}) or {}
    now = _iso(time.time())
    for record in records:
        hint = record.pop("addedHint", None)
        if record["id"] not in seen:
            if isinstance(hint, dict):
                hint = hint["first"] if first_run else hint["later"]
            seen[record["id"]] = hint or now
        record["addedAt"] = seen[record["id"]]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(seen, indent=1, sort_keys=True))


def build_inventory(cfg, force_remote=False):
    paths = cfg["paths"]
    marketplaces = _json(paths["plugins"] / "known_marketplaces.json", {}) or {}
    remote = remote_lookups(cfg, marketplaces, force=force_remote)

    records = list(plugin_records(cfg, remote)) + list(personal_records(cfg)) + account_records(cfg)
    by_name = {}
    for record in records:
        if record["source"] in ("personal", "account"):
            by_name.setdefault(record["name"], []).append(record)

    for spec_id, spec in cfg["updates"].get("upstream", {}).items():
        for record in records:
            if record["id"] == spec_id:
                _apply_upstream(record, spec, remote)

    for repo in repo_records(cfg):
        matches = by_name.get(repo["name"], [])
        for record in matches:
            _compare_with_repo(record, repo, paths["repoDist"])
        if not matches:
            records.append(_record(
                id=repo["name"], name=repo["name"], source="repo", description=repo["description"],
                version=repo["version"], path=str(repo["path"]), lastChanged=_iso(repo["changed"]),
                addedHint=created(repo["path"]), inRepo=True, update={"status": "not-installed", "reason": "repo-only",
                                     "repoPath": str(repo["path"]), "skill": repo["name"],
                                     "distFile": str(paths["repoDist"] / f"{repo['name']}.skill")},
            ))

    stamp_added(cfg, records)
    meta = {"remoteEnabled": remote.get("enabled", False), "remoteFetchedAt": _iso(remote.get("fetchedAt")),
            "remoteErrors": remote.get("errors", {})}
    return records, meta
