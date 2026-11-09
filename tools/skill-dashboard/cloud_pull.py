"""Copy cloud-session usage from the online console down to this Mac.

Claude Code cloud sessions report their requests and skill uses to the
console Worker (cloud/src/cloud.js). This pulls the rows it hasn't seen yet
into cloud-tokens.jsonl and cloud-events.jsonl, in the same shape as this
Mac's own rows, so cost and skill counts include them. They live in their own
files so cloud_sync.py never uploads them back as this Mac's usage.
"""

import json
import urllib.request

from inventory import _ssl_context

KINDS = {"tokens": "cloudTokens", "events": "cloudEvents"}
PAGE = 5000  # the Worker returns at most this many rows per request (PULL_LIMIT in cloud.js)


def pull(cfg, log=print):
    """Fetch new cloud rows for each kind; returns {kind: rows added}. Raises on a network or key error."""
    paths, cloud = cfg["paths"], cfg["cloud"]
    token = json.loads(paths["secrets"].read_text())["cloud"]["ingestToken"]
    context = _ssl_context(cfg["updates"]["caBundles"])
    try:
        state = json.loads(paths["cloudState"].read_text())
    except (OSError, ValueError):
        state = {}
    cursors = state.setdefault("cloudPull", {})
    added = {}
    for kind, path_key in KINDS.items():
        added[kind] = 0
        while True:
            request = urllib.request.Request(
                f"{cloud['ingestUrl']}/api/cloud/{kind}?after={cursors.get(kind, 0)}",
                headers={"Authorization": f"Bearer {token}", "User-Agent": "monochrome-console-sync"})
            with urllib.request.urlopen(request, timeout=cloud["timeoutSeconds"], context=context) as response:
                rows = json.loads(response.read())
            if not rows:
                break
            with open(paths[path_key], "a", encoding="utf-8") as out:
                for row in rows:
                    out.write(json.dumps({k: v for k, v in row.items() if k != "cursor"}, separators=(",", ":")) + "\n")
            cursors[kind] = max(row["cursor"] for row in rows)
            added[kind] += len(rows)
            paths["cloudState"].write_text(json.dumps(state))
            if len(rows) < PAGE:
                break
    log(f"cloud sessions: {added['tokens']} requests, {added['events']} skill uses pulled")
    return added
