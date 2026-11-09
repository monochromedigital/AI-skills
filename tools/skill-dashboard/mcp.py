"""MCP servers: what is configured, whether each one connects, and sign-in.

There is no machine-readable status API, so this parses `claude mcp list`,
which health-checks every server (it starts stdio servers and calls HTTP
ones). That takes several seconds, so results are cached in dataDir and the
dashboard asks for a fresh check only when you press the button.

`claude mcp list` answers for the folder it runs in: project-scoped servers
(a repo's .mcp.json, local-scope servers) only show from inside that project.
mcp.checkFromDir in config.json picks the folder; the default, your home
folder, shows user-scope servers, plugin servers and claude.ai connectors.

Status is read from the words in each line, not the glyphs, because the
glyphs have changed between releases (✓ / ✔).
"""

import json
import os
import pty
import re
import select
import subprocess
import time
from pathlib import Path

ACCOUNT_PREFIX = "claude.ai "
PLUGIN_PREFIX = "plugin:"
STATUS_WORDS = (
    ("needs authentication", "needs-auth"),
    ("failed", "failed"),
    ("pending", "pending"),
    ("disabled", "disabled"),
    ("connected", "connected"),
)


def _classify(name):
    if name.startswith(ACCOUNT_PREFIX):
        return {"source": "account", "label": name[len(ACCOUNT_PREFIX):]}
    if name.startswith(PLUGIN_PREFIX):
        parts = name.split(":")
        return {"source": "plugin", "plugin": parts[1] if len(parts) > 1 else None, "label": parts[-1]}
    return {"source": "config", "label": name}


def parse_list(text):
    servers = []
    for line in text.splitlines():
        line = line.strip()
        if ": " not in line or " - " not in line:
            continue  # the "Checking MCP server health…" banner and blank lines
        name, rest = line.split(": ", 1)
        target, status_text = rest.rsplit(" - ", 1)
        lowered = status_text.lower()
        status = next((code for word, code in STATUS_WORDS if word in lowered), "unknown")
        transport = "http" if "(HTTP)" in target or target.startswith("http") else "sse" if "(SSE)" in target else "stdio"
        servers.append({
            "name": name, "target": target.replace("(HTTP)", "").replace("(SSE)", "").strip(),
            "transport": transport, "status": status,
            "statusText": status_text.lstrip("✔✓✗!⏸ ").strip(), **_classify(name),
        })
    return servers


def _claude(cfg, *args, timeout):
    cwd = Path(cfg["mcp"]["checkFromDir"]).expanduser()
    return subprocess.run(
        [cfg["cli"]["claude"], *args], cwd=cwd, capture_output=True, text=True,
        timeout=timeout, stdin=subprocess.DEVNULL,
    )


def check(cfg):
    """Run the health check and cache it. Raises on a CLI failure so the job shows the error."""
    done = _claude(cfg, "mcp", "list", timeout=cfg["mcp"]["checkTimeoutSeconds"])
    if done.returncode != 0:
        raise RuntimeError((done.stderr or done.stdout).strip() or f"claude mcp list exited {done.returncode}")
    result = {"checkedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "checkedFrom": str(Path(cfg["mcp"]["checkFromDir"]).expanduser()),
              "servers": parse_list(done.stdout)}
    cfg["paths"]["mcpStatus"].write_text(json.dumps(result, indent=1))
    return result


def cached(cfg):
    try:
        return json.loads(cfg["paths"]["mcpStatus"].read_text())
    except (OSError, ValueError):
        return None


ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


def login(cfg, name, extra=()):
    """Opens the browser for the server's sign-in and waits for it to finish.

    `claude mcp login` refuses to run without a terminal ("stdin isn't a
    terminal"), and the dashboard runs it from a background server. So it runs
    on a pseudo-terminal: the CLI sees a terminal, opens the browser as usual,
    and finishes when the browser's redirect reaches its local callback.
    """
    master, slave = pty.openpty()
    proc = subprocess.Popen([cfg["cli"]["claude"], "mcp", "login", name, *extra],
                            stdin=slave, stdout=slave, stderr=slave, close_fds=True,
                            cwd=Path(cfg["mcp"]["checkFromDir"]).expanduser())
    os.close(slave)
    chunks, deadline = [], time.monotonic() + cfg["mcp"]["loginTimeoutSeconds"]
    try:
        while proc.poll() is None and time.monotonic() < deadline:
            ready, _, _ = select.select([master], [], [], 0.5)
            if ready:
                try:
                    chunks.append(os.read(master, 4096))
                except OSError:  # the CLI closed its side
                    break
        if proc.poll() is None:
            proc.kill()
        proc.wait()
    finally:
        os.close(master)
    text = ANSI.sub("", b"".join(chunks).decode(errors="replace")).replace("\r", "")
    return subprocess.CompletedProcess(proc.args, proc.returncode, stdout=text, stderr="")
