"""Loads config.json and turns its paths into absolute Paths.

Every path, port, window and threshold the dashboard uses lives in
config.json, so nothing else in this folder carries a literal. Relative paths
in config.json resolve against this folder, which is what lets
`repoSkills: ../../skills` find the repo's skills wherever the repo is cloned.
"""

import json
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
CONFIG_FILE = TOOL_DIR / "config.json"


def _resolve(value):
    path = Path(value).expanduser()
    return path if path.is_absolute() else (TOOL_DIR / path).resolve()


def load_config():
    cfg = json.loads(CONFIG_FILE.read_text())
    paths = {key: _resolve(value) for key, value in cfg["paths"].items()}
    home = paths["claudeHome"]
    data = paths["dataDir"]
    paths.update(
        projects=home / "projects",
        personalSkills=home / "skills",
        syncedSkills=home / "skills" / "synced",
        plugins=home / "plugins",
        settings=home / "settings.json",
        events=data / "events.jsonl",
        sessions=data / "sessions.json",
        tokens=data / "tokens.jsonl",
        cloudTokens=data / "cloud-tokens.jsonl",  # pulled from the console: cloud sessions
        cloudEvents=data / "cloud-events.jsonl",
        secrets=data / "secrets.json",
        machine=data / "machine.json",
        cloudState=data / "cloud-state.json",
        seen=data / "seen.json",
        groups=data / "groups.json",
        state=data / "state.json",
        lockFile=data / "sync.lock",
        remoteCache=data / "remote-cache.json",
        mcpStatus=data / "mcp-status.json",
        trash=data / "trash",
        web=TOOL_DIR / "web",
    )
    cfg["paths"] = paths
    return cfg
