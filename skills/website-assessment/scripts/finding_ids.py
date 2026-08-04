#!/usr/bin/env python3
"""
finding_ids.py - Stamps stable, content-derived ids into findings.json.

This is the one script allowed to write findings.json (project contract §4:
one writer per file). Everything downstream - build_data.py, build_deck.py,
the Figma plugin, and every `fid` in ia.json - reads the ids it puts there.

Contract §3:

    key = normalise(page) + US + normalise(section) + US + normalise(observation)
    id  = "f-" + sha256(key).hexdigest()[:10]

    normalise = NFKC, casefold, collapse whitespace, strip

Generated once, then frozen. A finding that already carries an `id` keeps it,
even if its observation is later reworded - the derivation is how the id is
born, not a checksum re-verified on every build. An id that changed when
someone fixed a typo would break every reference pointing at it.

A collision means two findings share a page, a section and an observation.
That is a duplicate, not a hash accident, so the run fails rather than
silently merging them.

Usage:
  python3 finding_ids.py --findings audit/findings.json           # stamp in place
  python3 finding_ids.py --findings audit/findings.json --check   # verify only
"""

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

ID_RE = re.compile(r"^f-[0-9a-f]{10}$")
US = "\x1f"


def normalise(text):
    s = unicodedata.normalize("NFKC", str(text or "")).casefold()
    return re.sub(r"\s+", " ", s).strip()


def derive(page, section, observation):
    key = US.join((normalise(page), normalise(section), normalise(observation)))
    return "f-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:10]


def walk(data):
    """Yield (slide_index, finding_index, slide, finding)."""
    for si, slide in enumerate(data.get("slides", [])):
        for fi, f in enumerate(slide.get("findings", [])):
            yield si, fi, slide, f


def stamp(data, check_only=False):
    """Returns (added, kept, errors). Mutates `data` unless check_only."""
    seen = {}
    added = kept = 0
    errors = []

    for si, fi, slide, f in walk(data):
        where = "slides[%d].findings[%d]" % (si, fi)
        fid = (f.get("id") or "").strip()

        if fid:
            if not ID_RE.match(fid):
                errors.append("%s.id = %r is not a valid finding id (expected f-<10 hex>)"
                              % (where, fid))
                continue
            kept += 1
        else:
            if check_only:
                errors.append("%s.id is missing" % where)
                continue
            if not (f.get("observation") or "").strip():
                errors.append("%s has no observation, so no id can be derived from it" % where)
                continue
            fid = derive(slide.get("page"), slide.get("section"), f.get("observation"))
            f["id"] = fid
            added += 1

        if fid in seen:
            errors.append(
                "%s.id = %r collides with %s - same page, section and observation. "
                "These are duplicate findings; delete one or make them distinct."
                % (where, fid, seen[fid]))
        else:
            seen[fid] = where

    return added, kept, errors


def main():
    ap = argparse.ArgumentParser(description="stamp stable finding ids into findings.json")
    ap.add_argument("--findings", required=True)
    ap.add_argument("--check", action="store_true",
                    help="verify ids exist and are unique; write nothing")
    a = ap.parse_args()

    path = Path(a.findings)
    data = json.loads(path.read_text(encoding="utf-8"))
    added, kept, errors = stamp(data, check_only=a.check)

    if errors:
        print("finding ids: %d problem%s" % (len(errors), "" if len(errors) == 1 else "s"),
              file=sys.stderr)
        for e in errors:
            print("  %s: %s" % (path.name, e), file=sys.stderr)
        sys.exit(1)

    if not a.check and added:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"file": str(path), "added": added, "kept": kept,
                      "total": added + kept, "wrote": bool(added and not a.check)}, indent=2))


if __name__ == "__main__":
    main()
