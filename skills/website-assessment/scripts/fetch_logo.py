#!/usr/bin/env python3
"""
fetch_logo.py - Pulls a *client's* logo from Brandfetch into a project folder.

Deliberately scoped to the client, not the agency. The four agency logos are
fixed, few, and yours: they are committed files under assets/brands/<slug>/,
correct by construction and available offline. Fetching those from a third
party every build would trade certainty for a network call.

The client changes every project, and hunting down a usable logo is the sort
of ten-minute errand worth automating. That is what this is for.

Two things to know before relying on it:

1. **Brandfetch's terms ask that logo links be embedded live**, hitting their
   CDN from the page. This script downloads and caches instead, because the
   report is a single self-contained file that has to open on a plane, in an
   email client, and three years from now when the CDN link has rotted. That
   is a deliberate departure - read their current terms and decide whether it
   suits how you deliver. `--link-only` prints the live URL instead of
   downloading, if you would rather stay inside the intended usage.

2. **What comes back is not always the wordmark.** For a large brand it is
   excellent. For a nine-person contractor in Jounieh it may be a scraped
   favicon. Always look at what landed before it goes in front of the client.
   Nothing here is a substitute for asking them for their brand kit.

Setup: a free client ID from the Brandfetch developer portal, then either
`export BRANDFETCH_CLIENT_ID=...` or pass `--client-id`.

Usage:
  python3 fetch_logo.py --project audit/ --domain tavolina.com
  python3 fetch_logo.py --project audit/ --domain tavolina.com --type symbol
  python3 fetch_logo.py --domain tavolina.com --link-only
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

CDN = "https://cdn.brandfetch.io"
TYPES = ("logo", "symbol", "icon")
THEMES = ("light", "dark")
FORMATS = ("svg", "png", "webp")
UA = "website-assessment-skill/1.0"


def build_url(domain, client_id, kind="logo", theme="dark", fmt="svg", w=None, h=None):
    """Path-segment API. The type prefix on the domain avoids the auto-detect
    order (domain -> ticker -> isin -> crypto) resolving a client's domain to
    something unrelated - rare, but silent when it happens."""
    parts = [CDN, "domain", domain]
    if w:
        parts += ["w", str(w)]
    if h:
        parts += ["h", str(h)]
    parts.append("%s.%s" % (kind, fmt) if fmt else kind)
    url = "/".join(parts)
    sep = "&" if "?" in url else "?"
    return "%s%stheme=%s&c=%s" % (url, sep, theme, client_id)


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type", "")


def run(project, domain, client_id, kind, formats, link_only, out_name):
    if not client_id and not link_only:
        print("fetch_logo.py: no client id. Set BRANDFETCH_CLIENT_ID or pass "
              "--client-id. Register free at the Brandfetch developer portal.",
              file=sys.stderr)
        sys.exit(2)

    if link_only:
        for theme in THEMES:
            print("%s: %s" % (theme, build_url(domain, client_id or "YOUR_CLIENT_ID",
                                               kind, theme)))
        return {"mode": "link-only", "domain": domain}

    project_dir = Path(project)
    logos_dir = project_dir / "logos"
    logos_dir.mkdir(parents=True, exist_ok=True)

    written, failed = [], []
    for theme in THEMES:
        got = False
        for fmt in formats:
            url = build_url(domain, client_id, kind, theme, fmt)
            try:
                body, ctype = fetch(url)
            except urllib.error.HTTPError as e:
                failed.append("%s/%s: HTTP %s" % (theme, fmt, e.code))
                continue
            except Exception as e:                       # noqa: BLE001
                failed.append("%s/%s: %s" % (theme, fmt, e))
                continue

            # A CDN that has nothing for a domain can still answer 200 with a
            # placeholder. A few hundred bytes of PNG is not a logo.
            if len(body) < 300 and fmt != "svg":
                failed.append("%s/%s: %d bytes, looks like a placeholder"
                              % (theme, fmt, len(body)))
                continue

            ext = "svg" if "svg" in (ctype or fmt) else fmt
            name = "%s-%s.%s" % (out_name, theme, ext)
            (logos_dir / name).write_bytes(body)
            written.append({"theme": theme, "format": ext, "bytes": len(body),
                            "path": str(logos_dir / name)})
            got = True
            break
        if not got:
            failed.append("%s: nothing usable" % theme)

    if not written:
        print("fetch_logo.py: nothing retrieved for %s. Ask the client for "
              "their brand kit - that is the better source anyway." % domain,
              file=sys.stderr)
        for f in failed:
            print("  " + f, file=sys.stderr)
        sys.exit(1)

    print("Retrieved %d file(s). LOOK AT THEM before using - Brandfetch returns "
          "a scraped favicon for small brands as readily as a real wordmark."
          % len(written), file=sys.stderr)

    return {"domain": domain, "type": kind, "written": written, "failed": failed,
            "dir": str(logos_dir)}


def main():
    ap = argparse.ArgumentParser(
        description="fetch a client logo from Brandfetch into <project>/logos/")
    ap.add_argument("--project", default=".", help="the project folder (contract §1)")
    ap.add_argument("--domain", required=True, help="the client's domain, e.g. example.com")
    ap.add_argument("--client-id", default=os.environ.get("BRANDFETCH_CLIENT_ID", ""))
    ap.add_argument("--type", dest="kind", default="logo", choices=TYPES,
                    help="logo = full wordmark, symbol = brand mark, icon = square")
    ap.add_argument("--format", dest="fmt", default="",
                    choices=("",) + FORMATS,
                    help="default: try svg, then png")
    ap.add_argument("--name", default="client", help="output filename stem")
    ap.add_argument("--link-only", action="store_true",
                    help="print live CDN URLs instead of downloading")
    a = ap.parse_args()
    formats = [a.fmt] if a.fmt else ["svg", "png"]
    print(json.dumps(run(a.project, a.domain, a.client_id, a.kind, formats,
                         a.link_only, a.name), indent=2))


if __name__ == "__main__":
    main()
