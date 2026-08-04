#!/usr/bin/env python3
"""
build_site.py - Renders the audit report.

A thin wrapper around `render_report.py`, which both this skill and
`sitemap-ia-board` carry byte-identically. This file owns three things the
renderer does not: validation, image delivery, and the CLI. Everything visual
lives in the renderer, so an audit report and a greenfield IA board cannot
drift into looking like two different agencies.

Reads `report-data.json` (from build_data.py) plus `ia.json` if the sitemap
skill has run on this project. It reads; it never writes either input -
project contract §4.

Views follow the data (contract §8):

  findings only          Home · Audit · Summary · Action items
  findings + ia          adds Personas · Sitemap, plus Database and Glossary
                         when ia.json carries them

Tabs with no data behind them are absent from the nav and from the Home cards,
not disabled. Their routes resolve to Home, because people paste links.

Every cross-reference is validated before anything is written (contract §6).
A build that would produce a broken document fails non-zero with the JSON path
of each problem and writes nothing - a half-valid report is worse than no
report, because it gets sent.

Usage:
  python3 build_site.py --project audit/ --out audit/out/report.html
  python3 build_site.py --project audit/ --out audit/out/report/ --mode folder
  python3 build_site.py --project audit/ --out audit/out/report.html --no-ia
  python3 build_site.py ... --cost-bands "S=$500-1k,M=$1-3k,L=$3k+"
"""

import argparse
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_report as R          # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA_SCHEMA = 1
IA_SCHEMA = 1
ID_RE = re.compile(r"^f-[0-9a-f]{10}$")
ALLOWED_CHIPS = {"UX", "CRO", "SEO", "LEAD"}
LANG_CHIP_RE = re.compile(r"^[A-Z]{2}(-[A-Z]{2})?$")
INLINE_SCREEN_WARN = 20


def parse_cost_bands(raw):
    bands = {}
    for part in (raw or "").split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            bands[k.strip().upper()] = v.strip()
    return bands


def die(errors):
    print("build_site.py: %d validation problem%s - nothing was written."
          % (len(errors), "" if len(errors) == 1 else "s"), file=sys.stderr)
    for e in errors:
        print("  " + e, file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------- validation (§6)
def validate_data(model, project_dir):
    errors = []
    if model.get("schema") != DATA_SCHEMA:
        errors.append("report-data.json: schema = %r, expected %d. Rebuild with build_data.py."
                      % (model.get("schema"), DATA_SCHEMA))
        return errors, {}

    by_id, counted = {}, 0
    for pi, page in enumerate(model.get("pages", [])):
        for si, sec in enumerate(page.get("sections", [])):
            where_s = "pages[%d].sections[%d]" % (pi, si)
            img = sec.get("img")
            if img:
                p = Path(img)
                p = p if p.is_absolute() else (project_dir / img)
                if not p.exists():
                    errors.append("report-data.json: %s.img = %r does not exist" % (where_s, img))
            for fi, f in enumerate(sec.get("findings", [])):
                where = "%s.findings[%d]" % (where_s, fi)
                counted += 1
                fid = f.get("id") or ""
                if not ID_RE.match(fid):
                    errors.append("report-data.json: %s.id = %r is not a valid finding id"
                                  % (where, fid))
                    continue
                if fid in by_id:
                    errors.append("report-data.json: %s.id = %r duplicates %s"
                                  % (where, fid, by_id[fid]["_where"]))
                    continue
                if f.get("hasMarker"):
                    x, y = f.get("x"), f.get("y")
                    if not (isinstance(x, (int, float)) and isinstance(y, (int, float))
                            and 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
                        errors.append("report-data.json: %s marker (%r, %r) falls outside the "
                                      "screenshot" % (where, x, y))
                rec = dict(f)
                rec["_where"] = where
                by_id[fid] = rec

    stated = (model.get("stats") or {}).get("findings")
    if stated is not None and stated != counted:
        errors.append("report-data.json: stats.findings = %d but %d findings are present"
                      % (stated, counted))
    return errors, by_id


def validate_ia(ia, by_id):
    """Contract §6.7 and §7. Every reference resolves, or the build fails.
    `validate_ia.py` in sitemap-ia-board runs the same checks on the same file;
    keep the two in step."""
    errors = []
    if ia.get("schema") != IA_SCHEMA:
        errors.append("ia.json: schema = %r, expected %d" % (ia.get("schema"), IA_SCHEMA))
        return errors

    page_ids = {}
    for i, p in enumerate(ia.get("pages", []) or []):
        pid = (p.get("id") or "").strip()
        if not pid:
            errors.append("ia.json: pages[%d].id is missing" % i)
            continue
        if pid in page_ids:
            errors.append("ia.json: pages[%d].id = %r duplicates pages[%d].id"
                          % (i, pid, page_ids[pid]))
        else:
            page_ids[pid] = i

    for i, p in enumerate(ia.get("pages", []) or []):
        if p.get("phase", 1) not in (1, 2):
            errors.append("ia.json: pages[%d].phase = %r must be 1 or 2" % (i, p.get("phase")))
        for j, s in enumerate(p.get("sections", []) or []):
            base = "ia.json: pages[%d].sections[%d]" % (i, j)
            if s.get("phase", 1) not in (1, 2):
                errors.append("%s.phase = %r must be 1 or 2" % (base, s.get("phase")))
            for k, chip in enumerate(s.get("chips", []) or []):
                c = str(chip).strip()
                if c not in ALLOWED_CHIPS and not LANG_CHIP_RE.match(c):
                    errors.append("%s.chips[%d] = %r is not an allowed chip "
                                  "(UX, CRO, SEO, LEAD, or a language code)" % (base, k, chip))
            fid = (s.get("fid") or "").strip()
            if fid and fid not in by_id:
                errors.append("%s.fid = %r does not resolve against findings.json" % (base, fid))

    persona_ids = {}
    for i, pr in enumerate(ia.get("personas", []) or []):
        prid = (pr.get("id") or "").strip()
        if not prid:
            errors.append("ia.json: personas[%d].id is missing" % i)
        elif prid in persona_ids:
            errors.append("ia.json: personas[%d].id = %r duplicates personas[%d].id"
                          % (i, prid, persona_ids[prid]))
        else:
            persona_ids[prid] = i
        for j, b in enumerate(pr.get("blocked_by", []) or []):
            fid = (b.get("fid") or "").strip()
            if fid and fid not in by_id:
                errors.append("ia.json: personas[%d].blocked_by[%d].fid = %r does not resolve "
                              "against findings.json" % (i, j, fid))
        for key in ("journey", "needs_pages"):
            for j, ref in enumerate(pr.get(key, []) or []):
                if str(ref).strip() not in page_ids:
                    errors.append("ia.json: personas[%d].%s[%d] = %r does not resolve to a "
                                  "pages[].id" % (i, key, j, ref))

    for i, f in enumerate(ia.get("funnels", []) or []):
        t = (f.get("temp") or "").strip().lower()
        if t and t not in ("hot", "warm", "cold"):
            errors.append("ia.json: funnels[%d].temp = %r must be hot, warm or cold" % (i, t))
    return errors


# ---------------------------------------------------------------- build
def build(project_dir, data_path, ia_path, out, mode, cost_bands, use_ia=True):
    project_dir = Path(project_dir)
    data_path = Path(data_path) if data_path else (project_dir / "report-data.json")
    if not data_path.exists():
        print("build_site.py: %s does not exist. Run build_data.py first." % data_path,
              file=sys.stderr)
        sys.exit(1)

    model = json.loads(data_path.read_text(encoding="utf-8"))
    errors, by_id = validate_data(model, project_dir)

    ia = None
    if use_ia:
        p = Path(ia_path) if ia_path else (project_dir / "ia.json")
        if p.exists():
            ia = json.loads(p.read_text(encoding="utf-8"))
            errors += validate_ia(ia, by_id)
        elif ia_path:
            errors.append("ia.json: %s does not exist" % p)

    if errors:
        die(errors)

    if mode == "inline" and model["stats"]["screens"] > INLINE_SCREEN_WARN:
        print("WARNING: %d screens inlined as data URLs. Over ~%d the file gets too heavy to "
              "open comfortably - rebuild with --mode folder."
              % (model["stats"]["screens"], INLINE_SCREEN_WARN), file=sys.stderr)

    # images: data URLs inline, copied files in folder mode
    assets = []
    for si, page in enumerate(model["pages"]):
        for sj, sec in enumerate(page["sections"]):
            rel = sec.get("img")
            if not rel:
                continue
            src = Path(rel)
            src = src if src.is_absolute() else (project_dir / rel)
            if mode == "folder":
                name = "%02d%02d-%s.png" % (si, sj, R.slugify(sec.get("section"), "section"))
                assets.append((src, name))
                sec["img"] = "assets/" + name
            else:
                sec["img"] = R.data_uri(src)

    m = model["meta"]
    meta = {
        "client": m.get("client", "Website"),
        "url": m.get("url", ""),
        "date": m.get("audited_on") or date.today().isoformat(),
        "kind": "Website UX/UI Assessment",
        "lede": "A section-by-section review of %s, annotated on the page itself. Every finding "
                "is pinned to the element it describes, filterable by discipline and severity, "
                "and linkable on its own." % (m.get("url") or "the site"),
        "agency": m.get("agency", ""),
        "audience": m.get("audience", ""),
        "site_type": m.get("site_type", ""),
        "footer_left": m.get("footer_left", ""),
        "footer_right": m.get("footer_right", ""),
    }
    brand = json.loads((ROOT / "assets" / "brand.json").read_text(encoding="utf-8"))
    brand["categories"] = model["brand"]["categories"]
    brand["severity"] = model["brand"]["severity"]
    html = R.render(brand, meta, model, ia, ROOT / "assets", cost_bands)

    out = Path(out)
    if mode == "folder":
        out.mkdir(parents=True, exist_ok=True)
        adir = out / "assets"
        adir.mkdir(exist_ok=True)
        for src, name in assets:
            shutil.copyfile(src, adir / name)
        (out / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
        index = out / "index.html"
        index.write_text(html, encoding="utf-8")
        size = index.stat().st_size + sum((adir / n).stat().st_size for _, n in assets)
        target = str(index)
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        size = out.stat().st_size
        target = str(out)

    return {
        "out": target, "mode": mode,
        "views": R.views_for(model, ia),
        "ia": bool(ia),
        "personas": len((ia or {}).get("personas", [])),
        "proposed_pages": len((ia or {}).get("pages", [])),
        "pages": model["stats"]["pages"], "screens": model["stats"]["screens"],
        "findings": model["stats"]["findings"], "critical": model["stats"]["critical"],
        "tracks": model["tracks"], "efforts": model["efforts"],
        "bytes": size, "mb": round(size / 1048576.0, 2),
    }


def main():
    ap = argparse.ArgumentParser(description="report-data.json (+ ia.json) -> interactive report")
    ap.add_argument("--project", required=True, help="the project folder (contract §1)")
    ap.add_argument("--data", default="", help="default: <project>/report-data.json")
    ap.add_argument("--ia", default="", help="default: <project>/ia.json if it exists")
    ap.add_argument("--no-ia", action="store_true",
                    help="force the audit-only build even if ia.json is present")
    ap.add_argument("--out", required=True, help="output .html (inline) or folder (folder mode)")
    ap.add_argument("--mode", default="inline", choices=["inline", "folder"])
    ap.add_argument("--cost-bands", default="",
                    help="optional effort->band map, e.g. \"S=$500-1k,M=$1-3k,L=$3k+\"")
    a = ap.parse_args()
    print(json.dumps(build(a.project, a.data or None, a.ia or None, a.out, a.mode,
                           parse_cost_bands(a.cost_bands), use_ia=not a.no_ia), indent=2))


if __name__ == "__main__":
    main()
