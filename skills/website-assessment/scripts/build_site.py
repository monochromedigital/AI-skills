#!/usr/bin/env python3
"""
build_site.py - Renderer half of the interactive report.

Reads `report-data.json` (written by build_data.py) plus `ia.json` if the
sitemap-ia-board skill has run on this project, and writes the HTML. It reads;
it never writes either input - project contract §4.

Views degrade with the data (contract §8):

  findings + ia   six views: Home · Audit · Summary · Personas · Sitemap · Actions
  findings only   four views: Home · Audit · Summary · Actions

In the four-view build the Personas and Sitemap nav items and their Home cover
cards are *removed*, not disabled. A tab a user can see is a tab they expect to
work, and one that opens an empty view reads as a broken report.

Every cross-document reference is validated first (contract §6). A build that
would produce a broken document fails non-zero with the JSON path of each
problem and writes nothing - a half-valid report is worse than no report,
because it gets sent.

Two delivery modes:
  inline  (default)  one self-contained .html, images as data URLs, opens from
                     a file:// URL with no server. ~1 MB per 6 screens.
  folder             index.html + assets/*.png + robots.txt, images lazy
                     loaded. The only viable mode above ~20 screens.

Usage:
  python3 build_site.py --project audit/ --out audit/out/report.html
  python3 build_site.py --project audit/ --out audit/out/report/ --mode folder
  python3 build_site.py --project audit/ --out audit/out/report.html --no-ia
  python3 build_site.py ... --cost-bands "S=$500-1k,M=$1-3k,L=$3k+"
"""

import argparse
import base64
import json
import mimetypes
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA_SCHEMA = 1
IA_SCHEMA = 1
ID_RE = re.compile(r"^f-[0-9a-f]{10}$")
ALLOWED_CHIPS = {"UX", "CRO", "SEO", "LEAD"}
LANG_CHIP_RE = re.compile(r"^[A-Z]{2}(-[A-Z]{2})?$")

FONT_FACES = [
    ("Urbanist", 300, "Urbanist-Light.ttf"),
    ("Urbanist", 400, "Urbanist-Regular.ttf"),
    ("Urbanist", 500, "Urbanist-Medium.ttf"),
    ("Urbanist", 600, "Urbanist-SemiBold.ttf"),
]

INLINE_SCREEN_WARN = 20


# ---------------------------------------------------------------- helpers
def slugify(text, fallback="item"):
    s = re.sub(r"[^a-z0-9]+", "-", str(text or "").lower()).strip("-")
    return s or fallback


def b64_font(path):
    return base64.b64encode(path.read_bytes()).decode("ascii")


def data_uri(path):
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return "data:%s;base64,%s" % (mime, base64.b64encode(path.read_bytes()).decode("ascii"))


def parse_cost_bands(raw):
    """'S=$500-1k,M=$1-3k,L=$3k+' -> {'S': '$500-1k', ...}"""
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

    by_id = {}
    counted = 0
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
    """Contract §6.7 and §7. Every reference resolves, or the build fails."""
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
        ph = p.get("phase", 1)
        if ph not in (1, 2):
            errors.append("ia.json: pages[%d].phase = %r must be 1 or 2" % (i, ph))
        for j, s in enumerate(p.get("sections", []) or []):
            base = "ia.json: pages[%d].sections[%d]" % (i, j)
            sph = s.get("phase", 1)
            if sph not in (1, 2):
                errors.append("%s.phase = %r must be 1 or 2" % (base, sph))
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


# ---------------------------------------------------------------- css
CSS = r"""
__FONTFACES__
*,*::before,*::after{box-sizing:border-box}
:root{
  --bg:__BG__; --panel:__PANEL__; --card:__CARD__; --body:__BODY__;
  --muted:__MUTED__; --eyebrow:__EYEBROW__; --marker:__MARKER__;
  --rule:__RULE__; --footer:__FOOTER__;
  --radius:14px; --gap:18px;
}
html,body{margin:0;padding:0}
body{
  background:var(--bg); color:var(--panel);
  font-family:Urbanist,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  font-size:15px; line-height:1.5; -webkit-font-smoothing:antialiased;
}
a{color:inherit}
button{font:inherit;color:inherit;background:none;border:0;cursor:pointer}

/* ---- header */
header.top{
  position:sticky; top:0; z-index:40; background:var(--bg);
  border-bottom:1px solid rgba(255,255,255,.09);
}
.top-in{display:flex;align-items:center;gap:24px;padding:14px 26px;max-width:1680px;margin:0 auto}
.brandmark{font-weight:600;font-size:15px;white-space:nowrap}
.brandmark small{display:block;font-weight:300;font-size:11.5px;color:var(--footer);letter-spacing:.02em}
nav.views{display:flex;gap:4px;overflow-x:auto;scrollbar-width:none;flex:1}
nav.views::-webkit-scrollbar{display:none}
nav.views a{
  text-decoration:none;padding:7px 14px;border-radius:999px;font-size:13.5px;
  font-weight:500;color:var(--footer);white-space:nowrap
}
nav.views a:hover{color:var(--panel);background:rgba(255,255,255,.06)}
nav.views a.active{color:var(--body);background:var(--panel)}
.top-meta{font-size:12px;color:var(--footer);text-align:right;white-space:nowrap}

/* ---- shell */
main{max-width:1680px;margin:0 auto;padding:26px}
h1{font-weight:300;font-size:34px;margin:.2em 0 .3em;letter-spacing:-.01em}
h2{font-weight:400;font-size:20px;margin:0 0 14px}
.eyebrow{color:var(--eyebrow);font-size:13px;font-weight:500;letter-spacing:.02em}

/* ---- home */
.hero{max-width:760px}
.hero p.lede{color:#CFCACF;font-weight:300;font-size:17px;line-height:1.55}
.statrow{display:flex;flex-wrap:wrap;gap:12px;margin:26px 0 34px}
.stat{background:var(--panel);color:var(--body);border-radius:var(--radius);padding:16px 20px;min-width:132px;flex:1 1 132px}
.stat b{display:block;font-weight:300;font-size:34px;line-height:1.05}
.stat span{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.navcards{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}
.navcard{
  display:block;text-decoration:none;background:var(--panel);color:var(--body);
  border-radius:var(--radius);padding:22px;transition:transform .12s ease
}
.navcard:hover{transform:translateY(-2px)}
.navcard b{display:block;font-size:18px;font-weight:500;margin-bottom:5px}
.navcard span{color:var(--muted);font-size:13.5px}

/* ---- filter bar */
.filters{
  position:sticky; top:57px; z-index:30; background:var(--bg);
  padding:12px 0 14px; border-bottom:1px solid rgba(255,255,255,.09); margin-bottom:18px
}
.chips{display:flex;flex-wrap:wrap;gap:7px;align-items:center}
.chips .lbl{font-size:11px;color:var(--footer);text-transform:uppercase;letter-spacing:.07em;margin-right:2px}
.chip{
  border:1px solid rgba(255,255,255,.22); border-radius:999px; padding:4px 11px;
  font-size:12.5px; font-weight:500; color:#D8D4D8; display:inline-flex; align-items:center; gap:6px
}
.chip:hover{border-color:rgba(255,255,255,.5)}
.chip .dot{width:8px;height:8px;border-radius:50%;background:currentColor;flex:none}
.chip.on{color:var(--body);background:var(--panel);border-color:var(--panel)}
.chip.clear{border-style:dashed}
.countline{font-size:12.5px;color:var(--footer);margin-top:9px}
.countline b{color:var(--panel);font-weight:500}

/* ---- audit layout */
.audit{display:grid;grid-template-columns:190px minmax(0,1fr) 370px;gap:var(--gap);align-items:start}
.rail{position:sticky;top:150px;max-height:calc(100vh - 170px);overflow:auto}
.rail::-webkit-scrollbar{width:7px}
.rail::-webkit-scrollbar-thumb{background:rgba(255,255,255,.16);border-radius:4px}
.pagelist{display:flex;flex-direction:column;gap:3px}
.pagelist button{
  text-align:left;padding:9px 12px;border-radius:9px;font-size:13.5px;color:#C9C5C9;width:100%
}
.pagelist button:hover{background:rgba(255,255,255,.07);color:#fff}
.pagelist button.on{background:var(--panel);color:var(--body);font-weight:500}
.pagelist button i{display:block;font-style:normal;font-size:11px;color:var(--footer)}
.pagelist button.on i{color:var(--muted)}

/* ---- screenshots */
.shot{margin-bottom:26px}
.shot h3{font-size:14px;font-weight:500;margin:0 0 9px;color:#DCD8DC}
.shot h3 em{font-style:normal;color:var(--footer);font-weight:300}
.frame{background:#262426;border-radius:12px;overflow:hidden;border:1px solid rgba(255,255,255,.09)}
.chrome{display:flex;align-items:center;gap:7px;padding:9px 12px;background:#1F1D1F}
.chrome i{width:9px;height:9px;border-radius:50%;background:#413F41;display:block}
.chrome .addr{
  flex:1;margin-left:8px;background:#2C2A2C;border-radius:6px;padding:3px 10px;
  font-size:11px;color:#8F8B8F;overflow:hidden;text-overflow:ellipsis;white-space:nowrap
}
.canvas{position:relative;line-height:0;background:#fff}
.canvas img{width:100%;height:auto;display:block}
.noimg{padding:56px 20px;text-align:center;color:var(--footer);font-size:13px;background:#2A282A;line-height:1.5}
.pin{
  position:absolute;transform:translate(-50%,-50%);width:26px;height:26px;border-radius:50%;
  background:var(--marker);color:#fff;font-size:11.5px;font-weight:600;
  display:flex;align-items:center;justify-content:center;cursor:pointer;
  box-shadow:0 0 0 2px #fff,0 2px 7px rgba(0,0,0,.4);transition:opacity .15s ease,transform .12s ease;
  z-index:2
}
.pin:hover{transform:translate(-50%,-50%) scale(1.14)}
.pin.dim{opacity:.16;pointer-events:none}
.pin.on{outline:3px solid var(--eyebrow);outline-offset:2px;z-index:3}
@keyframes flash{0%,100%{transform:translate(-50%,-50%) scale(1)}35%{transform:translate(-50%,-50%) scale(1.5)}}
.pin.flash{animation:flash .55s ease}

/* ---- finding cards */
.cards{display:flex;flex-direction:column;gap:9px}
.cards .grouphead{font-size:11px;letter-spacing:.07em;text-transform:uppercase;color:var(--footer);margin:10px 0 1px}
.fcard{
  background:var(--panel);color:var(--body);border-radius:11px;padding:13px 14px;
  display:flex;gap:11px;cursor:pointer;transition:opacity .15s ease,box-shadow .12s ease;
  border:2px solid transparent
}
.fcard.dim{opacity:.3}
.fcard.on{border-color:var(--eyebrow);box-shadow:0 6px 20px rgba(0,0,0,.28)}
.fnum{
  flex:none;width:24px;height:24px;border-radius:50%;background:var(--marker);color:#fff;
  font-size:11px;font-weight:600;display:flex;align-items:center;justify-content:center
}
.fbody{min-width:0;flex:1}
.tags{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:7px}
.tag{border-radius:999px;padding:2px 8px;font-size:10.5px;font-weight:500;color:#fff;letter-spacing:.02em}
.tag.ghost{background:none;border:1px solid rgba(0,0,0,.18);color:var(--muted)}
.fcard p{margin:0 0 6px;font-size:13.5px;line-height:1.45}
.fcard p:last-child{margin-bottom:0}
.fcard .lab{font-weight:600}
.fcard .mut{color:var(--muted)}
.fcard .scope{font-weight:600;font-size:12.5px}

/* ---- tooltip */
.tip{
  position:absolute;z-index:60;max-width:330px;background:var(--panel);color:var(--body);
  border-radius:11px;padding:13px 14px;box-shadow:0 12px 34px rgba(0,0,0,.42);
  pointer-events:none;display:none
}
.tip.show{display:block}

/* ---- summary */
.grid2{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:var(--gap);align-items:start}
.sheet{background:var(--panel);color:var(--body);border-radius:var(--radius);padding:24px}
.sheet h2{color:var(--body)}
.sheet p{font-size:14.5px;line-height:1.55}
.countgrid{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:4px}
.cnt{display:flex;align-items:center;justify-content:space-between;background:var(--card);border-radius:9px;padding:10px 13px}
.cnt b{font-weight:300;font-size:26px}
.sevbar{display:flex;height:13px;border-radius:999px;overflow:hidden;margin:6px 0 12px}
.sevbar span{display:block}
.sevkey{display:flex;flex-wrap:wrap;gap:14px;font-size:12.5px;color:var(--muted)}
.sevkey i{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px}
table.metrics{width:100%;border-collapse:collapse;font-size:13.5px}
table.metrics th,table.metrics td{text-align:left;padding:9px 4px;border-bottom:1px solid var(--rule)}
table.metrics th{font-weight:600;color:var(--muted);font-size:11.5px;text-transform:uppercase;letter-spacing:.06em}
table.metrics td.num{text-align:right;font-variant-numeric:tabular-nums}

/* ---- actions */
.trackhead{display:flex;align-items:baseline;gap:11px;margin:26px 0 12px}
.trackhead h2{margin:0}
.trackhead span{color:var(--footer);font-size:13px}
.act{background:var(--panel);color:var(--body);border-radius:11px;padding:14px 16px;margin-bottom:9px;display:flex;gap:13px}
.act.dim{display:none}
.act .rank{flex:none;width:30px;font-weight:300;font-size:20px;color:var(--muted);font-variant-numeric:tabular-nums}
.act .where{font-size:11.5px;color:var(--muted);margin-top:6px}
.badge{border-radius:6px;padding:2px 7px;font-size:10.5px;font-weight:600;letter-spacing:.03em}
.badge.eff{background:var(--card);color:var(--muted);border:1px solid var(--rule)}
.toolbar{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin-bottom:6px}
.btn{border:1px solid rgba(255,255,255,.28);border-radius:999px;padding:6px 15px;font-size:13px;font-weight:500}
.btn:hover{background:rgba(255,255,255,.09)}

/* ---- personas */
.note{
  background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.13);
  border-radius:11px;padding:14px 16px;font-size:13.5px;color:#D2CED2;margin-bottom:20px;
  max-width:900px;line-height:1.55
}
.note b{color:var(--panel);font-weight:600}
.pgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:var(--gap);align-items:start}
.pcard{background:var(--panel);color:var(--body);border-radius:var(--radius);overflow:hidden}
.pcard .bar{height:5px;display:block}
.pcard .in{padding:20px 22px}
.pcard h3{margin:0;font-size:20px;font-weight:500}
.pcard .role{color:var(--muted);font-size:13px;margin-top:2px}
.pcard .weight{
  display:inline-block;margin-top:10px;border-radius:999px;padding:3px 10px;
  font-size:11px;font-weight:600;background:var(--card);color:var(--muted);border:1px solid var(--rule)
}
blockquote.q{
  margin:14px 0 0;padding:11px 0 11px 14px;border-left:3px solid var(--rule);
  font-size:15px;font-weight:300;font-style:italic;line-height:1.45
}
.pcard .ctx{font-size:13.5px;line-height:1.5;margin:13px 0 0}
.plist{margin:8px 0 0;padding:0;list-style:none;font-size:13.5px}
.plist li{padding:6px 0 6px 17px;position:relative;border-bottom:1px solid var(--rule);line-height:1.45}
.plist li:last-child{border-bottom:0}
.plist li::before{content:"";position:absolute;left:2px;top:13px;width:5px;height:5px;border-radius:50%;background:var(--muted)}
.sub{font-size:11px;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);margin:16px 0 2px;font-weight:600}
.jrny{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:8px}
.jrny .step{background:var(--card);border:1px solid var(--rule);border-radius:8px;padding:4px 9px;font-size:12px}
.jrny .arw{color:var(--muted);font-size:12px}
.ev{
  margin-top:6px;border:1px dashed var(--rule);border-radius:9px;background:var(--card);
  padding:9px 11px;font-size:12.5px;color:var(--muted);line-height:1.45
}
.ev .lab{font-weight:600;color:var(--body)}
.ev a{color:var(--eyebrow)}
.evtoggle{font-size:11.5px;color:var(--eyebrow);font-weight:600;padding:0;margin-top:5px}

/* ---- sitemap */
.board{display:flex;gap:14px;overflow-x:auto;padding-bottom:14px;align-items:start}
.board::-webkit-scrollbar{height:9px}
.board::-webkit-scrollbar-thumb{background:rgba(255,255,255,.16);border-radius:5px}
.col{flex:0 0 292px;background:var(--panel);color:var(--body);border-radius:var(--radius);padding:16px;align-self:stretch}
.col.dim{opacity:.28}
.col .ch{border-bottom:1px solid var(--rule);padding-bottom:11px;margin-bottom:11px}
.col .ch b{display:block;font-size:16px;font-weight:600}
.col .ch code{font-size:11.5px;color:var(--muted);font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.col .ch .flags{display:flex;gap:5px;flex-wrap:wrap;margin-top:7px}
.flag{border-radius:6px;padding:2px 7px;font-size:10px;font-weight:600;letter-spacing:.04em;text-transform:uppercase}
.flag.new{background:var(--eyebrow);color:#fff}
.flag.tpl{background:var(--card);color:var(--muted);border:1px solid var(--rule)}
.flag.p2{background:none;color:var(--muted);border:1px dashed var(--muted)}
.plain{background:var(--card);border-radius:9px;padding:11px 12px;font-size:12.5px;line-height:1.5;color:var(--muted);margin-bottom:11px}
.scard{border:1px solid var(--rule);border-radius:9px;padding:10px 11px;margin-bottom:8px;background:#fff}
.scard.p2{border-style:dashed;background:var(--card)}
.scard.dim{opacity:.22}
.scard b{display:block;font-size:13.5px;font-weight:600;margin-bottom:3px}
.scard p{margin:0;font-size:12.5px;line-height:1.45;color:var(--muted)}
.dchips{display:flex;flex-wrap:wrap;gap:4px;margin-top:7px}
.dchip{border-radius:5px;padding:2px 6px;font-size:9.5px;font-weight:700;letter-spacing:.05em;color:#fff}
.funnels{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 20px}
.funnel{background:var(--panel);color:var(--body);border-radius:11px;padding:13px 15px;flex:1 1 250px;min-width:0}
.funnel b{display:block;font-size:14px;font-weight:600}
.funnel .path{font-size:12.5px;color:var(--muted);margin-top:5px;word-break:break-word}
.funnel .fnote{display:block;font-size:12px;color:var(--muted);margin-top:6px;font-style:italic}
.temp{border-radius:999px;padding:2px 8px;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#fff}

footer.bot{max-width:1680px;margin:0 auto;padding:30px 26px 40px;display:flex;justify-content:space-between;gap:16px;color:var(--footer);font-size:11.5px}

/* ---- responsive */
@media (max-width:1000px){
  .audit{grid-template-columns:minmax(0,1fr)}
  .rail{position:static;max-height:none;overflow:visible}
  .pagelist{flex-direction:row;flex-wrap:wrap}
  .pagelist button{width:auto}
  .grid2{grid-template-columns:minmax(0,1fr)}
  .filters{position:static}
}
@media (max-width:820px){
  main{padding:18px}
  .top-in{padding:11px 16px;gap:14px}
  .top-meta{display:none}
  h1{font-size:26px}
  .tip{display:none!important}
  .countgrid{grid-template-columns:1fr}
  .pgrid{grid-template-columns:minmax(0,1fr)}
  .col{flex-basis:262px}
}
@media (pointer:coarse){ .tip{display:none!important} }
"""


# ---------------------------------------------------------------- js
JS = r"""
'use strict';
var DATA = JSON.parse(document.getElementById('report-data').textContent);
var IA = DATA.ia || null;
var CATS = DATA.brand.categories, SEVS = DATA.brand.severity;
var CATNAMES = Object.keys(CATS);
var SEVNAMES = ['Critical','Moderate','Minor'];
var COST = DATA.costBands || {};

/* Which views exist is a property of the data, not of the router. With no
   ia.json the Personas and Sitemap views are absent from this list, absent
   from the nav, and absent from the Home cards - contract §8. */
var VIEWS = ['home','audit','summary'].concat(IA ? ['personas','sitemap'] : []).concat(['actions']);
var DISCIPLINES = ['UX','CRO','SEO','LEAD'];
var DCOLOR = {UX:'#DF6630', CRO:'#2E8F86', SEO:'#D7586C', LEAD:'#866FBC'};

var ALL = [];
DATA.pages.forEach(function(p){ p.sections.forEach(function(s){ s.findings.forEach(function(f){ ALL.push(f); }); }); });
var BY_ID = {};
ALL.forEach(function(f){ BY_ID[f.id] = f; });

var state = { view:'home', page:(DATA.pages[0]||{}).slug||null, finding:null,
              sev:new Set(), cat:new Set(), track:new Set(),
              disc:new Set(), phase2:true };
var ignoreHash = false;

/* ---------------------------------------------------------- hash */
function readHash(){
  var h = location.hash.replace(/^#/,'');
  var q = ''; var i = h.indexOf('?');
  if(i >= 0){ q = h.slice(i+1); h = h.slice(0,i); }
  var parts = h.split('/').filter(Boolean);
  var want = parts[0] || 'home';
  /* People paste links. A route this build does not have resolves to Home
     rather than rendering nothing. */
  state.view = VIEWS.indexOf(want) >= 0 ? want : 'home';
  if(state.view === 'audit'){
    if(parts[1]) state.page = parts[1];
    state.finding = parts[2] || null;
  } else { state.finding = null; }
  state.sev = new Set(); state.cat = new Set(); state.track = new Set(); state.disc = new Set();
  state.phase2 = true;
  q.split('&').filter(Boolean).forEach(function(kv){
    var p = kv.split('='); var k = p[0];
    var v = decodeURIComponent((p[1]||'').replace(/\+/g,' '));
    if(k === 'phase2'){ state.phase2 = v !== '0'; return; }
    if(!v) return;
    v.split('|').forEach(function(one){
      if(k === 'sev') state.sev.add(one);
      else if(k === 'cat') state.cat.add(one);
      else if(k === 'track') state.track.add(one);
      else if(k === 'disc') state.disc.add(one);
    });
  });
}
function buildHash(){
  var h = '#/' + state.view;
  if(state.view === 'audit'){
    h += '/' + (state.page || '');
    if(state.finding) h += '/' + state.finding;
  }
  var q = [];
  if(state.sev.size) q.push('sev=' + encodeURIComponent(Array.from(state.sev).join('|')));
  if(state.cat.size) q.push('cat=' + encodeURIComponent(Array.from(state.cat).join('|')));
  if(state.track.size) q.push('track=' + encodeURIComponent(Array.from(state.track).join('|')));
  if(state.disc.size) q.push('disc=' + encodeURIComponent(Array.from(state.disc).join('|')));
  if(!state.phase2) q.push('phase2=0');
  return h + (q.length ? '?' + q.join('&') : '');
}
function syncHash(){ ignoreHash = true; location.hash = buildHash(); setTimeout(function(){ ignoreHash = false; }, 0); }

/* ---------------------------------------------------------- utils */
function esc(s){ return String(s == null ? '' : s)
  .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function catColor(c){ return (CATS[c] || {}).color || '#7D797E'; }
function sevColor(s){ return (SEVS[s] || {}).color || '#7D797E'; }
function sevWeight(s){ return (SEVS[s] || {}).weight || 0; }
function effWeight(e){ return e === 'S' ? 1 : e === 'M' ? 2 : e === 'L' ? 3 : 4; }
function costOf(f){ return f.effort ? (COST[f.effort] || null) : null; }
function matches(f){
  if(state.sev.size && !state.sev.has(f.severity)) return false;
  if(state.cat.size && !(f.categories || []).some(function(c){ return state.cat.has(c); })) return false;
  if(state.track.size && !state.track.has(f.track)) return false;
  return true;
}
function visibleCount(){ return ALL.filter(matches).length; }
function findFinding(id){ return BY_ID[id] || null; }

/* ---------------------------------------------------------- shared bits */
/* Track / effort / cost belong to the action-items view - on the walkthrough
   they crowd out the finding itself. */
var PLAIN = {track:false, effort:false, cost:false};
function tagsHtml(f, opts){
  opts = opts || {};
  var h = '<div class="tags">';
  (f.categories || []).forEach(function(c){
    h += '<span class="tag" style="background:' + catColor(c) + '">' + esc(c) + '</span>';
  });
  if(f.severity) h += '<span class="tag" style="background:' + sevColor(f.severity) + '">' + esc(f.severity.toUpperCase()) + '</span>';
  if(f.track && opts.track !== false) h += '<span class="tag ghost">' + esc(f.track === 'now' ? 'Now' : 'Revamp') + '</span>';
  if(f.effort && opts.effort !== false) h += '<span class="tag ghost">Effort ' + esc(f.effort) + '</span>';
  var c = costOf(f);
  if(c && opts.cost !== false) h += '<span class="tag ghost">' + esc(c) + '</span>';
  return h + '</div>';
}
function bodyHtml(f){
  var h = '';
  if(f.observation) h += '<p>' + esc(f.observation) + '</p>';
  if(f.detail) h += '<p class="mut">' + esc(f.detail) + '</p>';
  if(f.fix) h += '<p><span class="lab">Fix:</span> ' + esc(f.fix) + '</p>';
  if(f.benchmark) h += '<p class="mut"><span class="lab">Benchmark:</span> ' + esc(f.benchmark) + '</p>';
  if(f.principle) h += '<p class="mut"><span class="lab">Principle:</span> ' + esc(f.principle) + '</p>';
  if(f.scope) h += '<p class="scope">' + esc(f.scope) + '</p>';
  return h;
}
/* The IA never carries a copy of the audit's words - only the id. The text
   shown here is read live from findings.json at render time, so rewording a
   finding can never leave the two documents disagreeing. Contract §7. */
function evidenceHtml(fid, open){
  var f = findFinding(fid);
  if(!f) return '';
  var h = '<button class="evtoggle" data-ev="' + esc(fid) + '">' +
          (open ? 'Hide the finding' : 'Why: finding ' + esc(f.n) + ' on ' + esc(f.page)) + '</button>';
  if(open){
    h += '<div class="ev"><span class="lab">' + esc(f.severity) + ' · ' + esc(f.section) + '</span><br>' +
         esc(f.observation) +
         ' <a href="#/audit/' + esc(f.pageSlug) + '/' + esc(f.id) + '">see it on the page</a></div>';
  }
  return h;
}
function filterBar(){
  var h = '<div class="filters"><div class="chips"><span class="lbl">Severity</span>';
  SEVNAMES.forEach(function(s){
    h += '<button class="chip' + (state.sev.has(s) ? ' on' : '') + '" data-f="sev" data-v="' + esc(s) + '">' +
         '<i class="dot" style="color:' + sevColor(s) + '"></i>' + esc(s) + '</button>';
  });
  h += '</div><div class="chips" style="margin-top:7px"><span class="lbl">Category</span>';
  CATNAMES.forEach(function(c){
    h += '<button class="chip' + (state.cat.has(c) ? ' on' : '') + '" data-f="cat" data-v="' + esc(c) + '">' +
         '<i class="dot" style="color:' + catColor(c) + '"></i>' + esc(c) + '</button>';
  });
  h += '</div>';
  if(DATA.tracks.length){
    h += '<div class="chips" style="margin-top:7px"><span class="lbl">Track</span>';
    DATA.tracks.forEach(function(t){
      h += '<button class="chip' + (state.track.has(t) ? ' on' : '') + '" data-f="track" data-v="' + esc(t) + '">' +
           esc(t === 'now' ? 'Now' : 'Revamp') + '</button>';
    });
    h += '</div>';
  }
  h += '<div class="countline" id="countline"></div></div>';
  return h;
}
function updateCount(){
  var el = document.getElementById('countline');
  if(!el) return;
  var n = visibleCount(), any = state.sev.size || state.cat.size || state.track.size;
  el.innerHTML = 'Showing <b>' + n + '</b> of <b>' + ALL.length + '</b> findings' +
    (any ? ' &nbsp;·&nbsp; <button class="chip clear" id="clearf">Clear filters</button>' : '');
  var c = document.getElementById('clearf');
  if(c) c.onclick = function(){
    state.sev.clear(); state.cat.clear(); state.track.clear();
    syncHash(); render();
  };
}

/* ---------------------------------------------------------- views */
function viewHome(){
  var s = DATA.stats, m = DATA.meta;
  var h = '<div class="hero"><div class="eyebrow">Website UX/UI Assessment</div><h1>' + esc(m.client) + '</h1>' +
          '<p class="lede">A section-by-section review of ' + esc(m.url || 'the site') +
          ', annotated on the page itself. Every finding is pinned to the element it describes, ' +
          'filterable by discipline and severity, and linkable on its own.</p></div>';
  h += '<div class="statrow">' +
       stat(s.pages, 'Pages audited') + stat(s.screens, 'Screens captured') +
       stat(s.findings, 'Findings') + stat(s.critical, 'Critical') + '</div>';

  h += '<div class="navcards">' +
       card('#/audit', 'Audit', 'The annotated walkthrough — screenshots with numbered pins and the finding behind each one.') +
       card('#/summary', 'Summary', 'The diagnosis, the pattern across pages, and counts by category and severity.');
  if(IA){
    h += card('#/personas', 'Personas', 'Who the site is for, what stops them today, and the route each one takes through the proposed structure.') +
         card('#/sitemap', 'Sitemap', 'The proposed information architecture, section by section, with the finding behind each decision.');
  }
  h += card('#/actions', 'Action items', 'Every fix, ordered by severity and effort, exportable as CSV.') +
       '</div>';
  return h;
  function stat(v, l){ return '<div class="stat"><b>' + v + '</b><span>' + l + '</span></div>'; }
  function card(href, t, d){ return '<a class="navcard" href="' + href + '"><b>' + t + '</b><span>' + d + '</span></a>'; }
}

function viewAudit(){
  var page = null;
  for(var i=0;i<DATA.pages.length;i++) if(DATA.pages[i].slug === state.page) page = DATA.pages[i];
  if(!page){ page = DATA.pages[0]; state.page = page ? page.slug : null; }
  if(!page) return '<p>No pages in this report.</p>';

  var h = filterBar() + '<div class="audit">';

  h += '<div class="rail"><div class="pagelist">';
  DATA.pages.forEach(function(p){
    var n = 0; p.sections.forEach(function(s){ n += s.findings.length; });
    h += '<button data-page="' + esc(p.slug) + '"' + (p.slug === page.slug ? ' class="on"' : '') + '>' +
         esc(p.name) + '<i>' + n + ' finding' + (n === 1 ? '' : 's') + '</i></button>';
  });
  h += '</div></div>';

  h += '<div class="shots">';
  page.sections.forEach(function(s){
    h += '<div class="shot"><h3>' + esc(s.section || 'Section') + ' <em>· ' + s.findings.length + '</em></h3>' +
         '<div class="frame"><div class="chrome"><i></i><i></i><i></i><div class="addr">' +
         esc(DATA.meta.url || '') + '</div></div><div class="canvas">';
    if(s.img){
      h += '<img src="' + esc(s.img) + '" alt="' + esc(s.section) + '" loading="lazy">';
      s.findings.forEach(function(f){
        if(!f.hasMarker) return;
        h += '<button class="pin" data-id="' + esc(f.id) + '" style="left:' + (f.x*100) + '%;top:' + (f.y*100) + '%" ' +
             'aria-label="Finding ' + f.n + '">' + f.n + '</button>';
      });
    } else {
      h += '<div class="noimg">Screenshot unavailable for this section.<br>' +
           'The findings on the right still apply.</div>';
    }
    h += '</div></div></div>';
  });
  h += '</div>';

  h += '<div class="rail"><div class="cards">';
  page.sections.forEach(function(s){
    h += '<div class="grouphead">' + esc(s.section || 'Section') + '</div>';
    s.findings.forEach(function(f){
      h += '<div class="fcard" data-id="' + esc(f.id) + '"><div class="fnum">' + f.n + '</div><div class="fbody">' +
           tagsHtml(f, PLAIN) + bodyHtml(f) + '</div></div>';
    });
  });
  h += '</div></div></div>';
  return h;
}

function viewSummary(){
  var s = DATA.stats;
  var h = '<div class="eyebrow">General</div><h1>Summary</h1><div class="grid2">';

  h += '<div class="sheet">';
  (DATA.summary.narrative || []).forEach(function(p){ h += '<p>' + esc(p) + '</p>'; });
  if(!(DATA.summary.narrative || []).length) h += '<p class="mut">No summary narrative was recorded.</p>';
  h += '<h2 style="margin-top:22px">Severity</h2><div class="sevbar">';
  var tot = s.findings || 1;
  SEVNAMES.forEach(function(n){
    var v = s.severity[n] || 0;
    if(v) h += '<span style="width:' + (v/tot*100) + '%;background:' + sevColor(n) + '" title="' + n + ': ' + v + '"></span>';
  });
  h += '</div><div class="sevkey">';
  SEVNAMES.forEach(function(n){
    h += '<span><i style="background:' + sevColor(n) + '"></i>' + n + ' — ' + (s.severity[n] || 0) + '</span>';
  });
  h += '</div></div>';

  h += '<div><div class="sheet"><h2>Findings by category</h2><div class="countgrid">';
  Object.keys(s.categories).sort(function(a,b){ return (s.categories[b]||0)-(s.categories[a]||0); }).forEach(function(c){
    h += '<div class="cnt"><span class="tag" style="background:' + catColor(c) + '">' + esc(c) + '</span><b>' +
         s.categories[c] + '</b></div>';
  });
  h += '</div></div>';

  h += '<div class="sheet" style="margin-top:var(--gap)"><h2>At a glance</h2><table class="metrics">' +
       '<tr><th>Metric</th><th class="num" style="text-align:right">Value</th></tr>' +
       row('Pages audited', s.pages) + row('Screens captured', s.screens) +
       row('Total findings', s.findings) + row('Critical', s.severity.Critical || 0) +
       row('Moderate', s.severity.Moderate || 0) + row('Minor', s.severity.Minor || 0);
  if(IA) h += row('Pages proposed', (IA.pages || []).length) + row('Personas', (IA.personas || []).length);
  if(DATA.meta.site_type) h += '<tr><td>Site type</td><td class="num">' + esc(DATA.meta.site_type) + '</td></tr>';
  if(DATA.meta.audience) h += '<tr><td>Audience</td><td class="num">' + esc(DATA.meta.audience) + '</td></tr>';
  h += '<tr><td>Audited on</td><td class="num">' + esc(DATA.meta.audited_on) + '</td></tr>';
  h += '</table></div></div></div>';
  return h;
  function row(l, v){ return '<tr><td>' + l + '</td><td class="num">' + v + '</td></tr>'; }
}

var openEvidence = new Set();

function viewPersonas(){
  if(!IA) return viewHome();
  var ev = IA.evidence || {};
  var people = IA.personas || [];
  var pageName = {};
  (IA.pages || []).forEach(function(p){ pageName[p.id] = p.name; });

  var h = '<div class="eyebrow">Who this is for</div><h1>Personas</h1>';
  if(ev.note) h += '<div class="note">' + esc(ev.note) + '</div>';
  if(!people.length) return h + '<p style="color:var(--footer)">No personas were recorded for this project.</p>';

  h += '<div class="pgrid">';
  people.forEach(function(p){
    var colour = p.colour || DCOLOR.UX;
    h += '<div class="pcard"><span class="bar" style="background:' + esc(colour) + '"></span><div class="in">' +
         '<h3>' + esc(p.name) + '</h3><div class="role">' + esc(p.role || '') + '</div>';
    if(p.weight) h += '<span class="weight">' + esc(p.weight) + '</span>';
    if(p.quote) h += '<blockquote class="q">“' + esc(p.quote) + '”</blockquote>';
    if(p.context) h += '<p class="ctx">' + esc(p.context) + '</p>';

    if((p.wants || []).length){
      h += '<div class="sub">What they need</div><ul class="plist">';
      p.wants.forEach(function(w){ h += '<li>' + esc(w) + '</li>'; });
      h += '</ul>';
    }
    if((p.blocked_by || []).length){
      h += '<div class="sub">What stops them today</div><ul class="plist">';
      p.blocked_by.forEach(function(b){
        h += '<li>' + esc(b.text || '');
        if(b.fid) h += '<br>' + evidenceHtml(b.fid, openEvidence.has(b.fid));
        h += '</li>';
      });
      h += '</ul>';
    }
    if((p.journey || []).length){
      h += '<div class="sub">Their route through the proposed site</div><div class="jrny">';
      p.journey.forEach(function(id, i){
        if(i) h += '<span class="arw">→</span>';
        h += '<span class="step">' + esc(pageName[id] || id) + '</span>';
      });
      h += '</div>';
    }
    h += '</div></div>';
  });
  return h + '</div>';
}

function sectionVisible(s){
  if(!state.phase2 && (s.phase || 1) === 2) return false;
  if(state.disc.size && !(s.chips || []).some(function(c){ return state.disc.has(c); })) return false;
  return true;
}

function viewSitemap(){
  if(!IA) return viewHome();
  var pages = IA.pages || [];

  var h = '<div class="filters"><div class="chips"><span class="lbl">Discipline</span>';
  DISCIPLINES.forEach(function(d){
    h += '<button class="chip' + (state.disc.has(d) ? ' on' : '') + '" data-f="disc" data-v="' + d + '">' +
         '<i class="dot" style="color:' + DCOLOR[d] + '"></i>' + d + '</button>';
  });
  h += '</div><div class="chips" style="margin-top:7px"><span class="lbl">Scope</span>' +
       '<button class="chip' + (state.phase2 ? ' on' : '') + '" id="phasetog">Show Phase 2</button>' +
       '</div><div class="countline" id="iacount"></div></div>';

  h += '<div class="eyebrow">Proposed</div><h1>Sitemap &amp; information architecture</h1>';

  if((IA.funnels || []).length){
    h += '<div class="funnels">';
    IA.funnels.forEach(function(f){
      var t = (f.temp || '').toLowerCase();
      var col = t === 'hot' ? '#D7586C' : t === 'warm' ? '#DF6630' : '#1E8FD9';
      h += '<div class="funnel"><b>' + esc(f.name || 'Funnel') +
           (t ? ' <span class="temp" style="background:' + col + '">' + esc(t) + '</span>' : '') + '</b>' +
           '<div class="path">' + esc(f.path || '') + '</div>' +
           (f.note ? '<span class="fnote">' + esc(f.note) + '</span>' : '') + '</div>';
    });
    h += '</div>';
  }

  h += '<div class="board">';
  pages.forEach(function(p){
    var secs = (p.sections || []);
    h += '<div class="col" data-page-id="' + esc(p.id) + '"><div class="ch"><b>' + esc(p.name) + '</b>' +
         '<code>' + esc(p.slug || '') + '</code><div class="flags">';
    if(p.isnew) h += '<span class="flag new">New</span>';
    if(p.template) h += '<span class="flag tpl">Template</span>';
    if((p.phase || 1) === 2) h += '<span class="flag p2">Phase 2</span>';
    h += '</div></div>';
    if(p.plain) h += '<div class="plain">' + esc(p.plain) + '</div>';
    secs.forEach(function(s, si){
      var p2 = (s.phase || 1) === 2;
      h += '<div class="scard' + (p2 ? ' p2' : '') + '" data-sec="' + esc(p.id) + ':' + si + '">' +
           '<b>' + esc(s.t || '') + '</b><p>' + esc(s.d || '') + '</p><div class="dchips">';
      (s.chips || []).forEach(function(c){
        h += '<span class="dchip" style="background:' + (DCOLOR[c] || '#7D797E') + '">' + esc(c) + '</span>';
      });
      if(p2) h += '<span class="flag p2">Phase 2</span>';
      h += '</div>';
      if(s.fid) h += evidenceHtml(s.fid, openEvidence.has(s.fid));
      h += '</div>';
    });
    h += '</div>';
  });
  return h + '</div>';
}

function applyIaFilters(){
  var shown = 0, tot = 0;
  document.querySelectorAll('.col').forEach(function(col){
    var any = false;
    col.querySelectorAll('.scard').forEach(function(el){
      var ref = (el.dataset.sec || '').split(':');
      var page = null;
      (IA.pages || []).forEach(function(p){ if(p.id === ref[0]) page = p; });
      var s = page ? (page.sections || [])[+ref[1]] : null;
      var ok = s ? sectionVisible(s) : true;
      tot += 1;
      if(ok){ shown += 1; any = true; }
      el.classList.toggle('dim', !ok);
    });
    col.classList.toggle('dim', !any);
  });
  var el = document.getElementById('iacount');
  if(el){
    var any = state.disc.size || !state.phase2;
    el.innerHTML = 'Showing <b>' + shown + '</b> of <b>' + tot + '</b> sections across <b>' +
      ((IA.pages || []).length) + '</b> pages' +
      (any ? ' &nbsp;·&nbsp; <button class="chip clear" id="cleari">Clear filters</button>' : '');
    var c = document.getElementById('cleari');
    if(c) c.onclick = function(){ state.disc.clear(); state.phase2 = true; syncHash(); render(); };
  }
}

function viewActions(){
  var items = ALL.filter(function(f){ return f.fix || f.observation; }).slice();
  items.sort(function(a,b){
    var d = sevWeight(b.severity) - sevWeight(a.severity);
    if(d) return d;
    d = effWeight(a.effort) - effWeight(b.effort);
    if(d) return d;
    return a.id < b.id ? -1 : 1;
  });

  var h = filterBar() + '<div class="eyebrow">Prioritised</div><h1>Action items</h1>' +
          '<div class="toolbar"><button class="btn" id="csv">Export CSV</button>' +
          '<span style="color:var(--footer);font-size:12.5px">Ordered by severity, then effort.</span></div>';

  if(DATA.tracks.length){
    ['now','revamp'].forEach(function(t){
      if(DATA.tracks.indexOf(t) < 0) return;
      var group = items.filter(function(f){ return f.track === t; });
      h += '<div class="trackhead"><h2>' + (t === 'now' ? 'Now — against the current build' :
           'Revamp — needs a new foundation') + '</h2><span>' + group.length + ' item' +
           (group.length === 1 ? '' : 's') + '</span></div>' + list(group);
    });
    var untracked = items.filter(function(f){ return !f.track; });
    if(untracked.length){
      h += '<div class="trackhead"><h2>Unassigned</h2><span>' + untracked.length + '</span></div>' + list(untracked);
    }
  } else {
    h += list(items);
  }
  return h;

  function list(arr){
    if(!arr.length) return '<p style="color:var(--footer)">Nothing in this track.</p>';
    var out = '';
    arr.forEach(function(f, i){
      out += '<div class="act" data-id="' + esc(f.id) + '"><div class="rank">' + (i+1) + '</div><div class="fbody">' +
             tagsHtml(f) +
             '<p>' + esc(f.fix || f.observation) + '</p>' +
             '<div class="where">' + esc(f.page) + ' · ' + esc(f.section) +
             ' &nbsp;<a href="#/audit/' + esc(f.pageSlug) + '/' + esc(f.id) + '" style="color:var(--eyebrow)">see it on the page</a></div>' +
             '</div></div>';
    });
    return out;
  }
}

/* ---------------------------------------------------------- csv */
function exportCsv(){
  var cols = ['Id','Page','Section','No','Severity','Categories','Track','Effort','Cost band',
              'Observation','Fix','Scope','Benchmark','Principle'];
  var rows = [cols];
  ALL.filter(matches).forEach(function(f){
    rows.push([f.id, f.page, f.section, f.n, f.severity, (f.categories||[]).join('; '),
               f.track || '', f.effort || '', costOf(f) || '',
               f.observation, f.fix, f.scope, f.benchmark, f.principle]);
  });
  var csv = rows.map(function(r){
    return r.map(function(v){ return '"' + String(v == null ? '' : v).replace(/"/g,'""') + '"'; }).join(',');
  }).join('\r\n');
  var blob = new Blob(['﻿' + csv], {type:'text/csv;charset=utf-8'});
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = (DATA.meta.client || 'assessment').replace(/[^a-z0-9]+/gi,'-').toLowerCase() + '-action-items.csv';
  document.body.appendChild(a); a.click();
  setTimeout(function(){ URL.revokeObjectURL(a.href); a.remove(); }, 400);
}

/* ---------------------------------------------------------- filters + focus */
function applyFilters(){
  document.querySelectorAll('.pin').forEach(function(el){
    var f = findFinding(el.dataset.id);
    el.classList.toggle('dim', !(f && matches(f)));
  });
  document.querySelectorAll('.fcard').forEach(function(el){
    var f = findFinding(el.dataset.id);
    el.classList.toggle('dim', !(f && matches(f)));
  });
  document.querySelectorAll('.act').forEach(function(el){
    var f = findFinding(el.dataset.id);
    el.classList.toggle('dim', !(f && matches(f)));
  });
  updateCount();
}
function applyFocus(opts){
  opts = opts || {};
  var id = state.finding;
  document.querySelectorAll('.pin.on,.fcard.on').forEach(function(el){ el.classList.remove('on'); });
  hideTip();
  if(!id) return;
  var pin = document.querySelector('.pin[data-id="' + id + '"]');
  var card = document.querySelector('.fcard[data-id="' + id + '"]');
  if(pin){
    pin.classList.add('on');
    if(opts.scrollPin){
      pin.scrollIntoView({block:'center', behavior:'smooth'});
      pin.classList.remove('flash');
      void pin.offsetWidth;
      pin.classList.add('flash');
    }
  }
  if(card){
    card.classList.add('on');
    if(opts.scrollCard) card.scrollIntoView({block:'nearest', behavior:'smooth'});
  }
}

/* ---------------------------------------------------------- tooltip */
var tip = document.createElement('div');
tip.className = 'tip';
document.body.appendChild(tip);
function showTip(pin, f){
  if(window.matchMedia('(max-width:820px)').matches || window.matchMedia('(pointer:coarse)').matches) return;
  tip.innerHTML = tagsHtml(f, PLAIN) + bodyHtml(f);
  tip.classList.add('show');
  var r = pin.getBoundingClientRect();
  var top = r.bottom + window.scrollY + 10;
  var left = r.left + window.scrollX + r.width/2 - tip.offsetWidth/2;
  left = Math.max(10, Math.min(left, document.documentElement.clientWidth - tip.offsetWidth - 10));
  if(top + tip.offsetHeight > window.scrollY + window.innerHeight - 10){
    top = r.top + window.scrollY - tip.offsetHeight - 10;
  }
  tip.style.top = top + 'px';
  tip.style.left = left + 'px';
}
function hideTip(){ tip.classList.remove('show'); }

/* ---------------------------------------------------------- keyboard */
function stepPin(dir){
  var pins = Array.prototype.slice.call(document.querySelectorAll('.pin:not(.dim)'));
  if(!pins.length) return;
  var idx = -1;
  for(var i=0;i<pins.length;i++) if(pins[i].dataset.id === state.finding) idx = i;
  idx = idx < 0 ? (dir > 0 ? 0 : pins.length-1) : (idx + dir + pins.length) % pins.length;
  state.finding = pins[idx].dataset.id;
  syncHash();
  applyFocus({scrollPin:true, scrollCard:true});
}
document.addEventListener('keydown', function(e){
  if(e.key === 'Escape'){ state.finding = null; syncHash(); applyFocus(); return; }
  if(state.view !== 'audit') return;
  var t = e.target && e.target.tagName;
  if(t === 'INPUT' || t === 'TEXTAREA') return;
  if(e.key === 'ArrowDown'){ e.preventDefault(); stepPin(1); }
  else if(e.key === 'ArrowUp'){ e.preventDefault(); stepPin(-1); }
});

/* ---------------------------------------------------------- render */
var RENDERERS = {
  home: viewHome, audit: viewAudit, summary: viewSummary,
  personas: viewPersonas, sitemap: viewSitemap, actions: viewActions
};

function render(){
  var app = document.getElementById('app');
  var key = VIEWS.indexOf(state.view) >= 0 ? state.view : 'home';
  state.view = key;
  app.innerHTML = (RENDERERS[key] || viewHome)();

  /* Compare an explicit view key. classList.toggle(cls, force) with `force`
     evaluating to undefined does NOT clear the class - it silently falls back
     to a plain flip, which is how a report ends up with two active tabs after
     a re-render. Never pass an expression that can yield undefined. */
  document.querySelectorAll('nav.views a').forEach(function(a){
    a.classList.toggle('active', a.getAttribute('data-view') === key);
  });

  if(key === 'sitemap') applyIaFilters();
  else applyFilters();
  applyFocus({scrollPin:!!state.finding, scrollCard:!!state.finding});
  window.scrollTo({top:0});
}

document.addEventListener('click', function(e){
  var ev = e.target.closest && e.target.closest('[data-ev]');
  if(ev){
    var fid = ev.dataset.ev;
    if(openEvidence.has(fid)) openEvidence.delete(fid); else openEvidence.add(fid);
    render(); return;
  }
  var tog = e.target.closest && e.target.closest('#phasetog');
  if(tog){ state.phase2 = !state.phase2; syncHash(); render(); return; }
  var chip = e.target.closest && e.target.closest('.chip[data-f]');
  if(chip){
    var set = state[chip.dataset.f];
    if(set.has(chip.dataset.v)) set.delete(chip.dataset.v); else set.add(chip.dataset.v);
    chip.classList.toggle('on');
    syncHash();
    if(chip.dataset.f === 'disc') applyIaFilters(); else applyFilters();
    return;
  }
  var pb = e.target.closest && e.target.closest('[data-page]');
  if(pb){ state.page = pb.dataset.page; state.finding = null; syncHash(); render(); return; }
  var pin = e.target.closest && e.target.closest('.pin');
  if(pin){
    state.finding = (state.finding === pin.dataset.id) ? null : pin.dataset.id;
    syncHash(); applyFocus({scrollCard:true}); return;
  }
  var fc = e.target.closest && e.target.closest('.fcard');
  if(fc){
    state.finding = (state.finding === fc.dataset.id) ? null : fc.dataset.id;
    syncHash(); applyFocus({scrollPin:true}); return;
  }
  if(e.target.id === 'csv'){ exportCsv(); return; }
});
document.addEventListener('mouseover', function(e){
  var pin = e.target.closest && e.target.closest('.pin');
  if(pin){ var f = findFinding(pin.dataset.id); if(f) showTip(pin, f); }
});
document.addEventListener('mouseout', function(e){
  var pin = e.target.closest && e.target.closest('.pin');
  if(pin && !state.finding) hideTip();
  else if(pin && state.finding !== pin.dataset.id) hideTip();
});
window.addEventListener('hashchange', function(){
  if(ignoreHash) return;
  readHash(); render();
});

/* render() runs LAST, after every view function above it is defined. A cold
   load straight to #/sitemap with this call placed earlier dies in the
   temporal dead zone before it paints anything. */
readHash();
render();
"""


# ---------------------------------------------------------------- html
HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive,nosnippet">
<meta name="referrer" content="no-referrer">
<title>__TITLE__</title>
<style>__CSS__</style>
</head>
<body>
<header class="top"><div class="top-in">
  <div class="brandmark">__CLIENT__<small>__AGENCY__ · Website UX/UI Assessment</small></div>
  <nav class="views">__NAV__</nav>
  <div class="top-meta">__URL__<br>__DATE__</div>
</div></header>
<main id="app"></main>
<footer class="bot"><span>__FOOTL__</span><span>__FOOTR__</span></footer>
<script type="application/json" id="report-data">__DATA__</script>
<script>__JS__</script>
</body>
</html>
"""

NAV_LABELS = [
    ("home", "Home"),
    ("audit", "Audit"),
    ("summary", "Summary"),
    ("personas", "Personas"),
    ("sitemap", "Sitemap"),
    ("actions", "Action items"),
]


def nav_html(has_ia):
    """Contract §8: the tabs a build does not have are absent from the DOM,
    not present-and-disabled."""
    out = []
    for key, label in NAV_LABELS:
        if key in ("personas", "sitemap") and not has_ia:
            continue
        out.append('<a href="#/%s" data-view="%s">%s</a>' % (key, key, label))
    return "\n    ".join(out)


def font_faces():
    d = ROOT / "assets" / "fonts"
    out = []
    for fam, weight, fname in FONT_FACES:
        p = d / fname
        if not p.exists():
            continue
        out.append(
            "@font-face{font-family:'%s';font-style:normal;font-weight:%d;font-display:swap;"
            "src:url(data:font/ttf;base64,%s) format('truetype')}" % (fam, weight, b64_font(p))
        )
    return "\n".join(out)


def render_css(colors):
    css = CSS.replace("__FONTFACES__", font_faces())
    for token, key in (("__BG__", "background"), ("__PANEL__", "panel"), ("__CARD__", "card"),
                       ("__BODY__", "body"), ("__MUTED__", "body_muted"), ("__EYEBROW__", "eyebrow"),
                       ("__MARKER__", "marker"), ("__RULE__", "rule"), ("__FOOTER__", "footer")):
        css = css.replace(token, colors[key])
    return css


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

    # images: data URLs for inline, copied files for folder
    assets = []
    for si, page in enumerate(model["pages"]):
        for sj, sec in enumerate(page["sections"]):
            rel = sec.get("img")
            if not rel:
                continue
            src = Path(rel)
            src = src if src.is_absolute() else (project_dir / rel)
            if mode == "folder":
                name = "%02d%02d-%s.png" % (si, sj, slugify(sec.get("section"), "section"))
                assets.append((src, name))
                sec["img"] = "assets/" + name
            else:
                sec["img"] = data_uri(src)

    model["ia"] = ia
    model["costBands"] = cost_bands

    payload = json.dumps(model, ensure_ascii=False).replace("</", "<\\/")
    m = model["meta"]
    html = (HTML
            .replace("__CSS__", render_css(model["brand"]["colors"]))
            .replace("__NAV__", nav_html(bool(ia)))
            .replace("__JS__", JS)
            .replace("__DATA__", payload)
            .replace("__TITLE__", "%s — Website UX/UI Assessment" % m["client"])
            .replace("__CLIENT__", m["client"])
            .replace("__AGENCY__", m["agency"])
            .replace("__URL__", m["url"])
            .replace("__DATE__", m["audited_on"])
            .replace("__FOOTL__", m["footer_left"])
            .replace("__FOOTR__", m["footer_right"]))

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
        "out": target,
        "mode": mode,
        "views": 6 if ia else 4,
        "ia": bool(ia),
        "personas": len(ia.get("personas", [])) if ia else 0,
        "proposed_pages": len(ia.get("pages", [])) if ia else 0,
        "pages": model["stats"]["pages"],
        "screens": model["stats"]["screens"],
        "findings": model["stats"]["findings"],
        "critical": model["stats"]["critical"],
        "tracks": model["tracks"],
        "efforts": model["efforts"],
        "bytes": size,
        "mb": round(size / 1048576.0, 2),
    }


def main():
    ap = argparse.ArgumentParser(description="report-data.json (+ ia.json) -> interactive report")
    ap.add_argument("--project", required=True, help="the project folder (contract §1)")
    ap.add_argument("--data", default="", help="default: <project>/report-data.json")
    ap.add_argument("--ia", default="", help="default: <project>/ia.json if it exists")
    ap.add_argument("--no-ia", action="store_true",
                    help="force the four-view build even if ia.json is present")
    ap.add_argument("--out", required=True, help="output .html (inline) or folder (folder mode)")
    ap.add_argument("--mode", default="inline", choices=["inline", "folder"])
    ap.add_argument("--cost-bands", default="",
                    help="optional effort->band map, e.g. \"S=$500-1k,M=$1-3k,L=$3k+\"")
    a = ap.parse_args()
    print(json.dumps(build(a.project, a.data or None, a.ia or None, a.out, a.mode,
                           parse_cost_bands(a.cost_bands), use_ia=not a.no_ia), indent=2))


if __name__ == "__main__":
    main()
