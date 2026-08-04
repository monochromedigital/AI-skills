#!/usr/bin/env python3
"""
build_data.py - Generator half of the interactive report.

Reads the project folder's `project.json`, `findings.json` and screenshots, and
writes `report-data.json`: the renderer's input. `build_site.py` turns that
into HTML and nothing else.

The split matters because the two halves fail differently. Missing screenshots,
findings without ids, a marker outside the image - those are data problems, and
they belong here, where the message can name the JSON path. Layout, routing and
degradation are rendering problems and belong in the renderer. Before the split
a screenshot typo surfaced as an empty panel in a report someone had already
sent.

Project contract §4: **this script reads findings.json and never writes it.**
Ids are stamped by `finding_ids.py`; if any are missing this run fails and says
so rather than deriving them in memory, which would leave findings.json without
the ids every other document references.

Usage:
  python3 build_data.py --project audit/
  python3 build_data.py --project audit/ --out audit/report-data.json
"""

import argparse
import json
import re
import sys
from collections import OrderedDict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import brandkit                       # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BRAND_DEFAULT = ROOT / "assets" / "brand.json"

SCHEMA = 1
ID_RE = re.compile(r"^f-[0-9a-f]{10}$")

IDENTITY_FIELDS = ("client", "url", "audience", "site_type")


def slugify(text, fallback="page"):
    s = re.sub(r"[^a-z0-9]+", "-", str(text or "").lower()).strip("-")
    return s or fallback


def resolve_image(slide, root):
    """Raw screenshot first - the report draws its own browser chrome, so the
    device-framed PNG is only a fallback for slides captured for the deck."""
    tried = []
    for key, framed in (("screenshot", False), ("framed", True)):
        rel = slide.get(key)
        if not rel:
            continue
        p = Path(rel)
        p = p if p.is_absolute() else (root / rel)
        if p.exists():
            try:
                return p.relative_to(root).as_posix(), framed, None
            except ValueError:
                return p.as_posix(), framed, None
        tried.append("%s = %r" % (key, rel))
    if tried:
        return None, False, "%s does not exist" % " and ".join(tried)
    return None, False, None


def marker_xy(finding, slide, used_framed):
    """Marker fractions are of the LIVE screenshot. If the framed PNG is what
    ends up on screen, map through screen_rect to account for the bezel."""
    m = finding.get("marker") or {}
    x, y = float(m.get("x", 0.5)), float(m.get("y", 0.5))
    if used_framed:
        sr = slide.get("screen_rect") or {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0}
        x = sr["x"] + sr["w"] * x
        y = sr["y"] + sr["h"] * y
    return round(x, 5), round(y, 5)


def load_brand(project_dir, project, agency=None):
    """Delegates to brandkit so the deck, the report and the board cannot
    resolve branding three different ways. Returns the brand only; the caller
    that needs the logo takes the second value from brandkit.resolve.

    Retained as a named function because the resolution order is contract
    behaviour (§2) and deserves one documented entry point per skill.
    """
    brand, _info = brandkit.resolve(project_dir, project, agency)
    return brand


def merge_meta(meta, project):
    """project.json is the identity card (contract §2). Where both name the
    same thing and disagree, project.json wins and the mismatch is reported -
    two documents calling the client different names is the bug."""
    out = dict(meta)
    for field in IDENTITY_FIELDS:
        pv = project.get(field)
        if not pv:
            continue
        mv = meta.get(field)
        if mv and str(mv).strip() != str(pv).strip():
            print("WARNING: %s differs - project.json says %r, findings.json says %r. "
                  "Using project.json." % (field, pv, mv), file=sys.stderr)
        out[field] = pv
    return out


def build(project_dir, out_path, agency=None):
    project_dir = Path(project_dir)
    findings_path = project_dir / "findings.json"
    project_path = project_dir / "project.json"

    if not findings_path.exists():
        print("build_data.py: %s does not exist. Write the audit before building the report."
              % findings_path, file=sys.stderr)
        sys.exit(1)

    data = json.loads(findings_path.read_text(encoding="utf-8"))
    project = json.loads(project_path.read_text(encoding="utf-8")) if project_path.exists() else {}
    try:
        brand, brand_info = brandkit.resolve(project_dir, project, agency)
    except brandkit.BrandError as e:
        print("build_data.py: %s" % e, file=sys.stderr)
        sys.exit(1)

    cats = brand["categories"]
    errors = []
    meta = merge_meta(data.get("meta", {}) or {}, project)

    pages = OrderedDict()
    screens = 0
    total = crit = 0
    derived_counts = {}
    sev_counts = {"Critical": 0, "Moderate": 0, "Minor": 0}
    tracks_used, efforts_used = set(), set()
    seen_ids = {}

    for si, slide in enumerate(data.get("slides", [])):
        page_name = slide.get("page") or "Page"
        pslug = slugify(page_name)
        pages.setdefault(pslug, {"slug": pslug, "name": page_name, "sections": []})

        img, used_framed, img_err = resolve_image(slide, project_dir)
        if img_err:
            errors.append("slides[%d].%s" % (si, img_err))
        if img:
            screens += 1

        findings = []
        for fi, f in enumerate(slide.get("findings", []) or []):
            where = "slides[%d].findings[%d]" % (si, fi)
            total += 1

            fid = (f.get("id") or "").strip()
            if not fid:
                errors.append("%s.id is missing - run scripts/finding_ids.py --findings %s"
                              % (where, findings_path.name))
            elif not ID_RE.match(fid):
                errors.append("%s.id = %r is not a valid finding id (expected f-<10 hex>)"
                              % (where, fid))
            elif fid in seen_ids:
                errors.append("%s.id = %r duplicates %s" % (where, fid, seen_ids[fid]))
            else:
                seen_ids[fid] = where

            sv = f.get("severity") or "Minor"
            sev_counts[sv] = sev_counts.get(sv, 0) + 1
            if sv == "Critical":
                crit += 1
            for c in f.get("categories", []) or []:
                if c not in cats:
                    errors.append("%s.categories contains %r, which is not in brand.json" % (where, c))
                derived_counts[c] = derived_counts.get(c, 0) + 1

            tr = (f.get("track") or "").strip().lower() or None
            ef = (f.get("effort") or "").strip().upper() or None
            if tr and tr not in ("now", "revamp"):
                errors.append("%s.track = %r must be \"now\" or \"revamp\"" % (where, tr))
            if ef and ef not in ("S", "M", "L"):
                errors.append("%s.effort = %r must be S, M or L" % (where, ef))
            if tr:
                tracks_used.add(tr)
            if ef:
                efforts_used.add(ef)

            mx, my = marker_xy(f, slide, used_framed)
            if f.get("marker") and not (0.0 <= mx <= 1.0 and 0.0 <= my <= 1.0):
                errors.append("%s.marker = (%.3f, %.3f) falls outside the screenshot"
                              % (where, mx, my))

            findings.append({
                "id": fid,
                "n": fi + 1,
                "page": page_name,
                "pageSlug": pslug,
                "section": slide.get("section") or "",
                "categories": f.get("categories", []) or [],
                "severity": sv,
                "observation": f.get("observation", ""),
                "detail": f.get("detail", ""),
                "fix": f.get("fix", ""),
                "benchmark": f.get("benchmark", ""),
                "principle": f.get("principle", ""),
                "scope": f.get("scope", ""),
                "track": tr,
                "effort": ef,
                "x": mx, "y": my,
                "hasMarker": bool(f.get("marker")),
            })

        pages[pslug]["sections"].append({
            "id": "s%d" % si,
            "section": slide.get("section") or "",
            "img": img,
            "framed": used_framed,
            "findings": findings,
        })

    if errors:
        print("build_data.py: %d problem%s in %s"
              % (len(errors), "" if len(errors) == 1 else "s", findings_path.name), file=sys.stderr)
        for e in errors:
            print("  findings.json: %s" % e, file=sys.stderr)
        sys.exit(1)

    summary = data.get("summary", {}) or {}
    counts = summary.get("counts") or derived_counts
    agency = brand.get("agency", {})

    model = {
        "schema": SCHEMA,
        "generated_by": "build_data.py",
        "meta": {
            "client": meta.get("client") or "Website",
            "url": meta.get("url", ""),
            "audited_on": meta.get("audited_on") or date.today().isoformat(),
            "audience": meta.get("audience", ""),
            "site_type": meta.get("site_type", ""),
            "languages": project.get("languages", []),
            "footer_left": agency.get("footer_left", "").replace("{year}", str(date.today().year)),
            "footer_right": meta.get("footer_right") or agency.get("footer_right", ""),
            "agency": agency.get("name", ""),
            # The slug, not just the display name. build_site re-resolves from
            # it so the report and this file cannot disagree about which
            # agency the run belongs to (contract §2).
            "agency_slug": brand_info.get("slug") or "",
        },
        "brand": {"categories": cats, "severity": brand["severity"], "colors": brand["colors"]},
        "pages": list(pages.values()),
        "summary": {"narrative": summary.get("narrative", []), "counts": counts},
        "stats": {
            "pages": len(pages),
            "screens": screens,
            "findings": total,
            "critical": crit,
            "severity": sev_counts,
            "categories": counts,
        },
        "tracks": sorted(tracks_used),
        "efforts": sorted(efforts_used),
    }

    out_path = Path(out_path) if out_path else (project_dir / "report-data.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "out": str(out_path),
        "pages": len(pages),
        "screens": screens,
        "findings": total,
        "critical": crit,
        "tracks": model["tracks"],
        "efforts": model["efforts"],
    }


def main():
    ap = argparse.ArgumentParser(
        description="project folder -> report-data.json (renderer input)")
    ap.add_argument("--project", required=True, help="the project folder (contract §1)")
    ap.add_argument("--out", default="", help="default: <project>/report-data.json")
    brandkit.add_agency_arg(ap)
    a = ap.parse_args()
    print(json.dumps(build(a.project, a.out or None, a.agency or None), indent=2))


if __name__ == "__main__":
    main()
