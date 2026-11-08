#!/usr/bin/env python3
"""Writes the console page into cloud/public for `wrangler deploy`.
The page reads its data from /api/report, which the Worker serves only to
people Cloudflare Access has signed in. Run by `npm run deploy` in cloud/."""

import sys

sys.dont_write_bytecode = True

from config import TOOL_DIR, load_config
from export import write_site

if __name__ == "__main__":
    cfg = load_config()
    write_site(cfg, TOOL_DIR / "cloud" / "public", cfg["cloud"]["dataPath"])
