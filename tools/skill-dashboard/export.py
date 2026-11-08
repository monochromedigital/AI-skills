#!/usr/bin/env python3
"""The read-only form of the dashboard, for the online console.

Two pieces, kept apart on purpose:
  - snapshot_report() builds the data: the same report the local page shows,
    with readOnly set (no update, uninstall, sign-in or bulk controls: nothing
    online can reach this Mac), your home folder written as "~", and the trash
    list left out. cloud_sync.py sends it to the database.
  - write_site() builds the page: the web/ folder plus an index.html that
    names where the data comes from. build_site.py writes it for the Worker.
    The page carries no data of its own, so nothing private is ever deployed.

The update check and the MCP health check run fresh for a snapshot, because
the point of a daily snapshot is to say what changed since yesterday.
"""

import sys

sys.dont_write_bytecode = True

import json
import shutil
from pathlib import Path

import mcp
from config import load_config
from inventory import build_inventory
from ledger import sync
from report import build_report

TOKEN_META = '<meta name="dashboard-token" content="{{DASHBOARD_TOKEN}}">'
DATA_META = '<meta name="dashboard-data" content="{url}">\n  <meta name="robots" content="noindex, nofollow">'
MACHINES_META = '\n  <meta name="dashboard-machines" content="{url}">'


def shorten_home(text):
    return text.replace(str(Path.home()), "~")


def snapshot_report(cfg, machine, check_mcp=True, log=print):
    result = sync(cfg)
    if check_mcp:
        try:
            log(f"MCP: {len(mcp.check(cfg)['servers'])} servers checked")
        except Exception as exc:  # keep the last MCP status rather than fail the snapshot
            log(f"MCP check failed, using the last result: {exc}")
    records, meta = build_inventory(cfg, force_remote=True)
    report = build_report(cfg, records, meta, result)
    report.update(readOnly=True, trash=[], machine=machine)
    return json.loads(shorten_home(json.dumps(report)))


def write_site(cfg, site_dir, data_url, machines_url=None, log=print):
    web = cfg["paths"]["web"]
    index = (web / "index.html").read_text()
    if TOKEN_META not in index:
        raise RuntimeError("web/index.html no longer has the token meta tag write_site replaces")
    site = Path(site_dir)
    shutil.rmtree(site / "web", ignore_errors=True)  # drop files the page no longer uses
    shutil.copytree(web, site / "web", ignore=shutil.ignore_patterns("index.html", ".DS_Store"))
    metas = DATA_META.format(url=data_url) + (MACHINES_META.format(url=machines_url) if machines_url else "")
    (site / "index.html").write_text(index.replace(TOKEN_META, metas))
    log(f"Page written to {site}")
    return site


if __name__ == "__main__":
    print(json.dumps(snapshot_report(load_config(), {"id": "preview", "name": "preview"}, check_mcp=False))[:400])
