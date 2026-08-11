#!/usr/bin/env python3
"""
build_board.py - Renders the sitemap and IA board.

The greenfield route: a project with an `ia.json` and no audit behind it. It
calls the same `render_report.py` that the assessment skill's `build_site.py`
calls, so a client who gets a board and a client who gets an audit report are
looking at one design system rather than two.

Views follow the data (contract §8):

  ia.json                Home · Personas · Sitemap
  ia.db present          adds Database
  ia.glossary present    adds Glossary

There is no Audit, Summary or Action-items view, because there are no findings.
Those tabs are absent from the nav rather than empty.

**If `findings.json` is in the folder, use `build_site.py` instead.** A project
with a diagnosis attached gets one combined report; building a second board
beside it produces two documents covering the same structure, and the client
reads whichever they opened last.

Usage:
  python3 build_board.py --project <project> --out <project>/out/sitemap.html
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_report as R          # noqa: E402
import brandkit                   # noqa: E402
from validate_ia import validate, load_finding_ids   # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# What this skill calls its deliverable - the hero eyebrow, the HTML <title>
# and the right of every footer. One definition, for the same reason
# build_data.py keeps DELIVERABLE in one place: the label was written out at
# each site it appeared, and a rename that reaches some of them ships a
# document disagreeing with its own title.
DELIVERABLE = "Sitemap & Information Architecture"


def build(project_dir, ia_path, out, agency_slug=None):
    project_dir = Path(project_dir)
    ia_path = Path(ia_path) if ia_path else (project_dir / "ia.json")
    if not ia_path.exists():
        print("build_board.py: %s does not exist. Write ia.json before rendering it."
              % ia_path, file=sys.stderr)
        sys.exit(1)

    findings = project_dir / "findings.json"
    if findings.exists():
        print("build_board.py: %s exists, so this project has an audit attached.\n"
              "Render the combined report with the assessment skill instead:\n"
              "    python3 ../website-assessment/scripts/build_data.py --project %s\n"
              "    python3 ../website-assessment/scripts/build_site.py --project %s --out %s\n"
              "Two documents covering the same structure diverge, and the client reads "
              "whichever they opened last." % (findings, project_dir, project_dir, out),
              file=sys.stderr)
        sys.exit(1)

    ia = json.loads(ia_path.read_text(encoding="utf-8"))
    known, has_audit = load_finding_ids(findings)
    errors = validate(ia, known, has_audit)
    if errors:
        print("build_board.py: %d validation problem%s - nothing was written."
              % (len(errors), "" if len(errors) == 1 else "s"), file=sys.stderr)
        for e in errors:
            print("  ia.json: " + e, file=sys.stderr)
        sys.exit(1)

    project_path = project_dir / "project.json"
    project = json.loads(project_path.read_text(encoding="utf-8")) if project_path.exists() else {}
    try:
        brand, brand_info = brandkit.resolve(project_dir, project, agency_slug)
    except brandkit.BrandError as e:
        print("build_board.py: %s" % e, file=sys.stderr)
        sys.exit(1)
    agency = brand.get("agency", {})

    pages = ia.get("pages", []) or []
    new_pages = sum(1 for p in pages if p.get("isnew"))
    meta = {
        "client": project.get("client") or "Website",
        "url": project.get("url", ""),
        "date": project.get("created") or date.today().isoformat(),
        "kind": DELIVERABLE,
        "lede": "The proposed structure for %s: who it has to serve, the pages that serve them, "
                "and what each section on each page is for. %d pages, %d of them new."
                % (project.get("client") or "the site", len(pages), new_pages),
        "agency": agency.get("name", ""),
        "audience": project.get("audience", ""),
        "site_type": project.get("site_type", ""),
        "footer_left": agency.get("footer_left", "").replace("{year}", str(date.today().year)),
        "footer_right": DELIVERABLE,
        "logo_uri": brand_info.get("logo_uri", ""),
    }

    html = R.render(brand, meta, None, ia, ROOT / "assets")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")

    return {
        "out": str(out),
        "views": R.views_for(None, ia),
        "pages": len(pages),
        "new_pages": new_pages,
        "sections": sum(len(p.get("sections", []) or []) for p in pages),
        "personas": len(ia.get("personas", []) or []),
        "funnels": len(ia.get("funnels", []) or []),
        "glossary": len(ia.get("glossary", []) or []),
        "bytes": out.stat().st_size,
        "mb": round(out.stat().st_size / 1048576.0, 2),
        "agency": agency.get("name", ""),
        "agency_slug": brand_info.get("slug") or "",
        "logo": bool(brand_info.get("logo_uri")),
    }


def main():
    ap = argparse.ArgumentParser(description="ia.json -> standalone sitemap & IA board")
    ap.add_argument("--project", required=True, help="the project folder (contract §1)")
    ap.add_argument("--ia", default="", help="default: <project>/ia.json")
    ap.add_argument("--out", required=True, help="output .html")
    brandkit.add_agency_arg(ap)
    a = ap.parse_args()
    print(json.dumps(build(a.project, a.ia or None, a.out, a.agency or None), indent=2))


if __name__ == "__main__":
    main()
