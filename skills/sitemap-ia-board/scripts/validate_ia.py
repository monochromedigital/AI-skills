#!/usr/bin/env python3
"""
validate_ia.py - Checks ia.json before anything renders it.

Implements project contract §5 (shape), §6 (validation) and §7 (references).
`build_site.py` in the website-assessment skill runs the same checks on the
same file; this script exists so the board can be validated on its own, before
a renderer is involved, and so a greenfield project - which has no audit and no
renderer - still gets checked.

Every failure prints the JSON path of the offending node. The two that actually
bite:

  * a `fid` that does not resolve. Usually a finding was deleted or the id was
    typed rather than copied.
  * a `fid` written when no findings.json exists. Never invent one - a
    greenfield board emits no fid anywhere.

Usage:
  python3 validate_ia.py --ia <project>/ia.json
  python3 validate_ia.py --ia <project>/ia.json --findings <project>/findings.json
  python3 validate_ia.py --ia <project>/ia.json --board <project>/out/sitemap.html
"""

import argparse
import json
import re
import sys
from pathlib import Path

IA_SCHEMA = 1
ID_RE = re.compile(r"^f-[0-9a-f]{10}$")
ALLOWED_CHIPS = {"UX", "CRO", "SEO", "LEAD"}
LANG_CHIP_RE = re.compile(r"^[A-Z]{2}(-[A-Z]{2})?$")
FID_IN_HTML = re.compile(r'class="fid"[^>]*>\s*([^<\s]+)\s*<')


def load_finding_ids(path):
    """Returns (set_of_ids, exists). An absent findings.json is not an error -
    it means greenfield, and then no fid may appear anywhere."""
    if not path or not Path(path).exists():
        return set(), False
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    ids = set()
    for slide in data.get("slides", []) or []:
        for f in slide.get("findings", []) or []:
            fid = (f.get("id") or "").strip()
            if fid:
                ids.add(fid)
    return ids, True


def check_fid(where, fid, known, has_audit, errors):
    if not fid:
        return
    if not ID_RE.match(fid):
        errors.append("%s = %r is not a valid finding id (expected f-<10 hex>)" % (where, fid))
        return
    if not has_audit:
        errors.append("%s = %r but this project has no findings.json. A greenfield board "
                      "emits no fid anywhere - never invent one." % (where, fid))
        return
    if fid not in known:
        errors.append("%s = %r does not resolve against findings.json" % (where, fid))


def validate(ia, known, has_audit):
    errors = []

    if ia.get("schema") != IA_SCHEMA:
        errors.append("schema = %r, expected %d" % (ia.get("schema"), IA_SCHEMA))
        return errors

    page_ids = {}
    for i, p in enumerate(ia.get("pages", []) or []):
        pid = (p.get("id") or "").strip()
        if not pid:
            errors.append("pages[%d].id is missing" % i)
        elif pid in page_ids:
            errors.append("pages[%d].id = %r duplicates pages[%d].id" % (i, pid, page_ids[pid]))
        else:
            page_ids[pid] = i
        if not (p.get("name") or "").strip():
            errors.append("pages[%d].name is missing" % i)
        if not (p.get("plain") or "").strip():
            errors.append("pages[%d].plain is missing - every column needs an "
                          "In-plain-words box" % i)
        if p.get("phase", 1) not in (1, 2):
            errors.append("pages[%d].phase = %r must be 1 or 2" % (i, p.get("phase")))

        sections = p.get("sections", []) or []
        if not sections:
            errors.append("pages[%d].sections is empty - a page with no sections is a "
                          "placeholder, not a plan" % i)
        for j, s in enumerate(sections):
            base = "pages[%d].sections[%d]" % (i, j)
            if not (s.get("t") or "").strip():
                errors.append("%s.t is missing" % base)
            if not (s.get("d") or "").strip():
                errors.append("%s.d is missing - a card must say why the section earns its "
                              "place" % base)
            chips = s.get("chips", []) or []
            if not chips:
                errors.append("%s.chips is empty - a card that earns no chip earns no "
                              "place" % base)
            for k, chip in enumerate(chips):
                c = str(chip).strip()
                if c not in ALLOWED_CHIPS and not LANG_CHIP_RE.match(c):
                    errors.append("%s.chips[%d] = %r is not an allowed chip "
                                  "(UX, CRO, SEO, LEAD, or a language code)" % (base, k, chip))
            if s.get("phase", 1) not in (1, 2):
                errors.append("%s.phase = %r must be 1 or 2" % (base, s.get("phase")))
            check_fid("%s.fid" % base, (s.get("fid") or "").strip(), known, has_audit, errors)

    persona_ids = {}
    for i, pr in enumerate(ia.get("personas", []) or []):
        prid = (pr.get("id") or "").strip()
        if not prid:
            errors.append("personas[%d].id is missing" % i)
        elif prid in persona_ids:
            errors.append("personas[%d].id = %r duplicates personas[%d].id"
                          % (i, prid, persona_ids[prid]))
        else:
            persona_ids[prid] = i
        for field in ("name", "role", "weight", "context"):
            if not (pr.get(field) or "").strip():
                errors.append("personas[%d].%s is missing" % (i, field))
        for j, b in enumerate(pr.get("blocked_by", []) or []):
            if not (b.get("text") or "").strip():
                errors.append("personas[%d].blocked_by[%d].text is missing" % (i, j))
            check_fid("personas[%d].blocked_by[%d].fid" % (i, j),
                      (b.get("fid") or "").strip(), known, has_audit, errors)
        for key in ("journey", "needs_pages"):
            for j, ref in enumerate(pr.get(key, []) or []):
                if str(ref).strip() not in page_ids:
                    errors.append("personas[%d].%s[%d] = %r does not resolve to a pages[].id"
                                  % (i, key, j, ref))
        # A persona that does not change the IA does not belong in the document.
        if not (pr.get("needs_pages") or []):
            errors.append("personas[%d].needs_pages is empty - a persona that does not change "
                          "the IA does not belong in the document" % i)

    for i, f in enumerate(ia.get("funnels", []) or []):
        t = (f.get("temp") or "").strip().lower()
        if t and t not in ("hot", "warm", "cold"):
            errors.append("funnels[%d].temp = %r must be hot, warm or cold" % (i, t))
        if not (f.get("path") or "").strip():
            errors.append("funnels[%d].path is missing" % i)

    if has_audit and not (ia.get("evidence") or {}).get("note"):
        errors.append("evidence.note is missing - say what the personas are grounded in. "
                      "\"No primary research\" is an acceptable answer; silence is not.")

    return errors


def check_board(board_path, ia, known, has_audit):
    """The standalone board is hand-filled, so its fid badges are checked too -
    a badge is the one place a wrong id survives review by looking right."""
    errors = []
    html = Path(board_path).read_text(encoding="utf-8")
    in_ia = set()
    for p in ia.get("pages", []) or []:
        for s in p.get("sections", []) or []:
            if s.get("fid"):
                in_ia.add(s["fid"])
    for pr in ia.get("personas", []) or []:
        for b in pr.get("blocked_by", []) or []:
            if b.get("fid"):
                in_ia.add(b["fid"])

    for fid in set(FID_IN_HTML.findall(html)):
        where = "%s: .fid badge %r" % (Path(board_path).name, fid)
        if not ID_RE.match(fid):
            errors.append("%s is not a valid finding id" % where)
        elif not has_audit:
            errors.append("%s but this project has no findings.json" % where)
        elif fid not in known:
            errors.append("%s does not resolve against findings.json" % where)
        elif fid not in in_ia:
            errors.append("%s is not in ia.json - the board and the structured record "
                          "disagree" % where)
    return errors


def main():
    ap = argparse.ArgumentParser(description="validate ia.json against the project contract")
    ap.add_argument("--ia", required=True)
    ap.add_argument("--findings", default="",
                    help="default: findings.json beside ia.json, if it exists")
    ap.add_argument("--board", default="", help="optional standalone board HTML to cross-check")
    a = ap.parse_args()

    ia_path = Path(a.ia)
    ia = json.loads(ia_path.read_text(encoding="utf-8"))
    findings_path = a.findings or (ia_path.parent / "findings.json")
    known, has_audit = load_finding_ids(findings_path)

    errors = ["ia.json: " + e for e in validate(ia, known, has_audit)]
    if a.board:
        errors += check_board(a.board, ia, known, has_audit)

    if errors:
        print("validate_ia.py: %d problem%s" % (len(errors), "" if len(errors) == 1 else "s"),
              file=sys.stderr)
        for e in errors:
            print("  " + e, file=sys.stderr)
        sys.exit(1)

    print(json.dumps({
        "ia": str(ia_path),
        "mode": "redesign" if has_audit else "greenfield",
        "pages": len(ia.get("pages", []) or []),
        "sections": sum(len(p.get("sections", []) or []) for p in ia.get("pages", []) or []),
        "personas": len(ia.get("personas", []) or []),
        "funnels": len(ia.get("funnels", []) or []),
        "fids_resolved": sum(1 for p in ia.get("pages", []) or []
                             for s in p.get("sections", []) or [] if s.get("fid")),
    }, indent=2))


if __name__ == "__main__":
    main()
