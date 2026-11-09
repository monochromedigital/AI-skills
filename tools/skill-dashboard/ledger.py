#!/usr/bin/env python3
"""Skill usage ledger: copies every skill invocation out of Claude Code's
transcripts into a log that nothing prunes.

Why a ledger instead of counting straight from transcripts: Claude Code
deletes CLI transcripts after `cleanupPeriodDays` (30 by default). Counting
from transcripts alone would quietly forget older usage and the totals would
shrink over time. Events copied into ~/.claude/skill-usage/events.jsonl stay.

What counts as one use:
  - the model calling the Skill tool (an assistant `tool_use` named "Skill")
  - you typing /skill-name (a user message that opens with <command-name>)
Built-in slash commands (/model, /mcp, ...) are recorded as well and dropped
later by report.py, which matches names against the skill inventory. That
keeps a list of built-in commands out of this file.

Token usage comes along too, for the cost view: every Claude reply records
its model and token counts (input, output, cache writes, cache reads). A
reply split over several transcript lines repeats the same counts on each,
so each reply is kept once, keyed by its message id, in tokens.jsonl. Like
skill uses, they are copied out before Claude Code prunes the transcript.

Session titles come along on the same pass: the transcript records your own
title for a session ("custom-title") and the one Claude Code generates
("ai-title"). They go to sessions.json so the dashboard can say which session
a skill was used in by name, not by id.

Transcripts are append-only, so the byte offset reached in each file is kept
in state.json and only new lines are read next time. Re-reading is harmless
anyway: events are keyed by tool_use id or message uuid. Bumping
LEDGER_VERSION makes the next sync re-read everything once, which is how a
field added later (like titles) reaches transcripts already read.

Runs from the SessionStart hook (`--quiet`) and from server.py on each load.
A lock file stops the two from writing at the same time.
"""

import sys

sys.dont_write_bytecode = True  # keep __pycache__ out of the repo folder

import fcntl
import json
import os
import re
import time

from config import load_config

LEDGER_VERSION = 3
SLASH = re.compile(r"<command-name>/?([^<\s]+)</command-name>")
# Cheap byte test before json.loads: almost no transcript line mentions any of these.
NEEDLES = (b'"Skill"', b"<command-name>", b'"custom-title"', b'"ai-title"', b'"usage"')
TITLE_FIELDS = {"custom-title": "customTitle", "ai-title": "aiTitle"}
SUBAGENT_DIR = "subagents"


def _base(obj, path):
    return {
        "ts": obj.get("timestamp"),
        "session": obj.get("sessionId"),
        "project": obj.get("cwd"),
        "subagent": bool(obj.get("isSidechain")) or SUBAGENT_DIR in path.parts,
        "entrypoint": obj.get("entrypoint"),
    }


def extract_events(obj, path):
    """Yield the skill events one transcript record carries."""
    kind = obj.get("type")
    content = (obj.get("message") or {}).get("content")
    if kind == "assistant" and isinstance(content, list):
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use" and block.get("name") == "Skill":
                skill = (block.get("input") or {}).get("skill")
                if skill and block.get("id"):
                    yield {**_base(obj, path), "id": block["id"], "skill": skill, "via": "model"}
    elif kind == "user":
        if isinstance(content, str):
            texts = [content]
        else:
            texts = [b.get("text", "") for b in content or [] if isinstance(b, dict) and b.get("type") == "text"]
        for text in texts:
            # Only a message that opens with the command tags is a typed command;
            # pasted text that merely mentions one is not.
            if not text.lstrip().startswith("<command-"):
                continue
            match = SLASH.search(text)
            if match and obj.get("uuid"):
                yield {**_base(obj, path), "id": obj["uuid"], "skill": match.group(1), "via": "slash"}
                return


def extract_usage(obj, path):
    """One compact usage record for an assistant reply, or None."""
    message = obj.get("message") or {}
    usage = message.get("usage") if isinstance(message, dict) else None
    if obj.get("type") != "assistant" or not usage or not message.get("id"):
        return None
    writes = usage.get("cache_creation") or {}
    tools = usage.get("server_tool_use") or {}
    write_total = usage.get("cache_creation_input_tokens") or 0
    write_1h = writes.get("ephemeral_1h_input_tokens") or 0
    return {
        **_base(obj, path), "id": message["id"], "model": message.get("model"),
        "in": usage.get("input_tokens") or 0, "out": usage.get("output_tokens") or 0,
        "cw5m": writes.get("ephemeral_5m_input_tokens", write_total - write_1h) or 0, "cw1h": write_1h,
        "cr": usage.get("cache_read_input_tokens") or 0,
        "search": tools.get("web_search_requests") or 0,
    }


def _read_json(path, default):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, ValueError):
        return default


def _write_json_atomic(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=1))
    os.replace(tmp, path)


def _append(path, records):
    if not records:
        return
    records.sort(key=lambda r: r.get("ts") or "")
    with open(path, "a", encoding="utf-8") as out:
        for record in records:
            out.write(json.dumps(record, separators=(",", ":")) + "\n")


def ledger_rows(cfg, kind):
    """This Mac's rows of `kind` ("events" or "tokens") plus the cloud-session rows pulled by cloud_pull.py."""
    paths = cfg["paths"]
    cloud = {"events": "cloudEvents", "tokens": "cloudTokens"}[kind]
    return read_events(paths[kind]) + read_events(paths[cloud])


def read_events(events_path):
    events = []
    try:
        with open(events_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except ValueError:
                        continue
    except FileNotFoundError:
        pass
    return events


def _scan_file(path, offset, seen, found, titles, usage_seen, usage_found):
    """Read `path` from `offset`; return the offset after the last whole line."""
    pos = offset
    with open(path, "rb") as f:
        f.seek(offset)
        for line in f:
            if not line.endswith(b"\n"):
                break  # still being written; pick it up next time
            pos += len(line)
            if not any(needle in line for needle in NEEDLES):
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            field = TITLE_FIELDS.get(obj.get("type"))
            if field and obj.get("sessionId") and obj.get(field):
                titles.setdefault(obj["sessionId"], {})[field] = obj[field]  # the latest title wins
                continue
            record = extract_usage(obj, path)
            if record and record["id"] not in usage_seen:
                usage_seen.add(record["id"])
                usage_found.append(record)
            for event in extract_events(obj, path):
                if event["id"] not in seen:
                    seen.add(event["id"])
                    found.append(event)
    return pos


def sync(cfg=None, wait=True):
    """Bring the ledger up to date. Returns a summary, or None if another sync holds the lock."""
    cfg = cfg or load_config()
    paths = cfg["paths"]
    paths["dataDir"].mkdir(parents=True, exist_ok=True)

    with open(paths["lockFile"], "w") as lock:
        deadline = time.monotonic() + (cfg["lock"]["waitSeconds"] if wait else 0)
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    return None
                time.sleep(0.2)

        state = _read_json(paths["state"], {"files": {}})
        if state.get("version") != LEDGER_VERSION:
            state["files"] = {}  # re-read every transcript once; event ids prevent double counting
            state["version"] = LEDGER_VERSION
        files = state.setdefault("files", {})
        titles = _read_json(paths["sessions"], {})
        seen = {e.get("id") for e in read_events(paths["events"])}
        usage_seen = {u.get("id") for u in read_events(paths["tokens"])}
        found, usage_found, live = [], [], set()

        for path in paths["projects"].rglob("*.jsonl"):
            key = str(path)
            live.add(key)
            try:
                size = path.stat().st_size
            except FileNotFoundError:
                continue
            offset = files.get(key, {}).get("offset", 0)
            if size < offset:
                offset = 0  # file was rewritten; ids stop double counting
            if size == offset:
                continue
            files[key] = {"offset": _scan_file(path, offset, seen, found, titles, usage_seen, usage_found)}

        # A pruned transcript leaves its events behind, which is the point.
        for key in [k for k in files if k not in live]:
            del files[key]

        if found:
            found.sort(key=lambda e: e.get("ts") or "")
            with open(paths["events"], "a", encoding="utf-8") as out:
                for event in found:
                    out.write(json.dumps(event, separators=(",", ":")) + "\n")

        _append(paths["tokens"], usage_found)
        _write_json_atomic(paths["sessions"], titles)
        state["lastSync"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        _write_json_atomic(paths["state"], state)
        return {"newEvents": len(found), "newUsage": len(usage_found), "transcripts": len(live), "lastSync": state["lastSync"]}


def main(argv):
    quiet = "--quiet" in argv
    result = sync(wait=not quiet)
    if not quiet:
        print(json.dumps(result if result else {"skipped": "another sync is running"}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
