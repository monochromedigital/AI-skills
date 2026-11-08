#!/usr/bin/env python3
"""Sends this Mac's data to the online console (Cloudflare Worker + D1).

What goes up, each run:
  - new lines of events.jsonl (skill uses) and tokens.jsonl (token usage),
    counted from where the last run stopped (cloud-state.json);
  - every session title (a few hundred short rows);
  - a fresh read-only dashboard snapshot (see export.snapshot_report).

Rows are re-sendable: the database ignores ids it already has, so a run that
stops halfway loses nothing and the next run simply carries on. Uploads are
split into chunks of cloud.chunkBytes so each request stays well inside the
Worker's limits.

Each Mac gets a random id once (machine.json), so two laptops never mix their
rows. The upload token lives in ~/.claude/skill-usage/secrets.json (owner-only
permissions), never in the repo.

Run daily by the Claude app's scheduled task; run by hand any time.
"""

import sys

sys.dont_write_bytecode = True

import json
import platform
import subprocess
import time
import urllib.parse
import urllib.error
import urllib.request
import uuid

from cloud_pull import pull
from config import load_config
from cost import left_out
from export import shorten_home, snapshot_report
from inventory import _ssl_context


def machine_identity(cfg):
    path = cfg["paths"]["machine"]
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        pass
    try:
        name = subprocess.run(["scutil", "--get", "ComputerName"], capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        name = ""
    machine = {"id": uuid.uuid4().hex, "name": name or platform.node()}
    path.write_text(json.dumps(machine))
    return machine


def chunks(records, limit):
    batch, size = [], 2
    for record in records:
        line = json.dumps(record, separators=(",", ":"))
        if batch and size + len(line) + 1 > limit:
            yield batch
            batch, size = [], 2
        batch.append(record)
        size += len(line) + 1
    if batch:
        yield batch


def main():
    cfg = load_config()
    cloud, paths = cfg["cloud"], cfg["paths"]
    token = json.loads(paths["secrets"].read_text())["cloud"]["ingestToken"]
    machine = machine_identity(cfg)
    context = _ssl_context(cfg["updates"]["caBundles"])
    log = lambda m: print(f"{time.strftime('%H:%M:%S')}  {m}", flush=True)

    def post(kind, body):
        request = urllib.request.Request(
            f"{cloud['ingestUrl']}/api/ingest/{kind}", data=body.encode(), method="POST",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                     "X-Machine-Id": machine["id"], "X-Machine-Name": urllib.parse.quote(machine["name"]),
                     "User-Agent": "monochrome-console-sync"})
        try:
            with urllib.request.urlopen(request, timeout=cloud["timeoutSeconds"], context=context) as response:
                return json.loads(response.read())["written"]
        except urllib.error.HTTPError as error:  # the Worker says why in its JSON body
            raise RuntimeError(f"{kind} upload refused ({error.code}): {error.read().decode(errors='replace')[:300]}") from None

    try:
        pull(cfg, log)  # cloud-session usage first, so the snapshot includes it
    except Exception as error:  # the Mac's own upload still matters if the pull fails
        log(f"cloud sessions: pull failed ({error})")
    report = snapshot_report(cfg, machine, log=log)  # also syncs the local ledger first
    try:
        state = json.loads(paths["cloudState"].read_text())
    except (OSError, ValueError):
        state = {}

    # Token rows from costLeaveOut folders never leave this Mac. They are dropped inside
    # each batch so `start` still counts lines, which is what the next run resumes from.
    skip = left_out(cfg)
    keep = {"events": lambda row: True, "tokens": lambda row: not skip(row.get("project"))}
    for kind, path in (("events", paths["events"]), ("tokens", paths["tokens"])):
        lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
        start = state.get(kind, 0)
        new = [json.loads(shorten_home(line)) for line in lines[start:] if line.strip()]
        written = 0
        for batch in chunks(new, cloud["chunkBytes"]):
            payload = [row for row in batch if keep[kind](row)]
            if payload:
                written += post(kind, json.dumps(payload, separators=(",", ":")))
            start += len(batch)
            state[kind] = start
            paths["cloudState"].write_text(json.dumps(state))
        log(f"{kind}: {len(new)} new, {written} stored")

    # Only new or renamed sessions: every row written counts against the database's daily limit.
    titles = json.loads(paths["sessions"].read_text()) if paths["sessions"].exists() else {}
    sent = state.get("sessions", {})
    sessions = [{"id": sid, "title": t.get("customTitle") or t.get("aiTitle"), "custom": int(bool(t.get("customTitle")))}
                for sid, t in titles.items()]
    changed = [s for s in sessions if sent.get(s["id"]) != [s["title"], s["custom"]]]
    for batch in chunks(changed, cloud["chunkBytes"]):
        post("sessions", json.dumps(batch, separators=(",", ":")))
        sent.update({s["id"]: [s["title"], s["custom"]] for s in batch})
        state["sessions"] = sent
        paths["cloudState"].write_text(json.dumps(state))
    log(f"sessions: {len(changed)} new or renamed, of {len(sessions)}")

    post("snapshot", json.dumps(report, separators=(",", ":")))
    log(f"snapshot sent for {machine['name']} ({len(report['skills'])} skills)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"FAILED: {exc}", flush=True)
        sys.exit(1)
