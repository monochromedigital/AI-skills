#!/usr/bin/env python3
"""
render_report.py - The one renderer. Carried byte-identically by every skill
that produces a client-facing report.

`website-assessment/scripts/build_site.py` and
`sitemap-ia-board/scripts/build_board.py` are both thin wrappers around
`render()` in this file. That is deliberate: an audit report and a greenfield
IA board are the same document with different sections present, and the moment
they were two codebases they started looking like two agencies.

Which views exist is decided by the data, never by a flag:

  findings.json present   Home · Audit · Summary · Action items
  ia.json present         Personas · Sitemap
  ia.db present           Database
  ia.glossary present     Glossary

A view with no data behind it is absent from the nav and absent from the Home
cards - not greyed out, not present-and-empty. Its route resolves to Home,
because people paste links.

Every colour comes from brand.json. Never hard-code a hex here.
"""

import base64
import json
import mimetypes
import re
from datetime import date
from pathlib import Path

SCHEMA = 1

FONT_FACES = [
    ("Urbanist", 300, "Urbanist-Light.ttf"),
    ("Urbanist", 400, "Urbanist-Regular.ttf"),
    ("Urbanist", 500, "Urbanist-Medium.ttf"),
    ("Urbanist", 600, "Urbanist-SemiBold.ttf"),
]

NAV_LABELS = [
    ("home", "Home"),
    ("audit", "Audit"),
    ("summary", "Summary"),
    ("personas", "Personas"),
    ("sitemap", "Sitemap &amp; IA"),
    ("database", "Database"),
    ("glossary", "Glossary"),
    ("actions", "Action items"),
]

COLOR_TOKENS = (
    ("__BG__", "background"), ("__PANEL__", "panel"), ("__CARD__", "card"),
    ("__BODY__", "body"), ("__MUTED__", "body_muted"), ("__EYEBROW__", "eyebrow"),
    ("__MARKER__", "marker"), ("__RULE__", "rule"), ("__FOOTER__", "footer"),
    ("__SURFACE__", "surface"), ("__SUNKEN__", "surface_sunken"),
    ("__BORDER__", "border"), ("__BORDERS__", "border_strong"),
    ("__DASHED__", "border_dashed"), ("__ONDARK__", "on_dark"),
    ("__ONDARKM__", "on_dark_muted"),
)


# ---------------------------------------------------------------- helpers
def slugify(text, fallback="item"):
    s = re.sub(r"[^a-z0-9]+", "-", str(text or "").lower()).strip("-")
    return s or fallback


def data_uri(path):
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return "data:%s;base64,%s" % (mime, base64.b64encode(path.read_bytes()).decode("ascii"))


def font_faces(assets_dir):
    out = []
    for fam, weight, fname in FONT_FACES:
        p = Path(assets_dir) / "fonts" / fname
        if not p.exists():
            continue
        b64 = base64.b64encode(p.read_bytes()).decode("ascii")
        out.append("@font-face{font-family:'%s';font-style:normal;font-weight:%d;"
                   "font-display:swap;src:url(data:font/ttf;base64,%s) format('truetype')}"
                   % (fam, weight, b64))
    return "\n".join(out)


def views_for(model, ia):
    """The single source of truth for which views exist. Python computes it,
    embeds it, and the nav and the router both read the same list - two places
    computing this independently is how a build ends up with a tab that routes
    nowhere."""
    v = ["home"]
    if model and model.get("pages"):
        v += ["audit", "summary"]
    if ia:
        if ia.get("personas"):
            v.append("personas")
        if ia.get("pages"):
            v.append("sitemap")
        if (ia.get("db") or {}).get("groups"):
            v.append("database")
        if ia.get("glossary"):
            v.append("glossary")
    if model and model.get("pages"):
        v.append("actions")
    return v


def nav_html(views):
    return "\n    ".join(
        '<a href="#/%s" data-view="%s">%s</a>' % (k, k, label)
        for k, label in NAV_LABELS if k in views)


# ---------------------------------------------------------------- css
CSS = r"""
__FONTFACES__
*,*::before,*::after{box-sizing:border-box}
:root{
  --bg:__BG__; --surface:__SURFACE__; --sunken:__SUNKEN__;
  --panel:__PANEL__; --card:__CARD__; --body:__BODY__; --muted:__MUTED__;
  --eyebrow:__EYEBROW__; --marker:__MARKER__; --rule:__RULE__;
  --footer:__FOOTER__; --border:__BORDER__; --borders:__BORDERS__;
  --dashed:__DASHED__; --ondark:__ONDARK__; --ondarkm:__ONDARKM__;
  --radius:14px; --gap:18px;
}
html,body{margin:0;padding:0}
body{background:var(--bg);color:var(--panel);
  font-family:Urbanist,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  font-size:15px;line-height:1.5;-webkit-font-smoothing:antialiased}
a{color:inherit}
button{font:inherit;color:inherit;background:none;border:0;cursor:pointer}

/* ---- header */
header.top{position:sticky;top:0;z-index:40;background:var(--bg);border-bottom:1px solid var(--border)}
.top-in{display:flex;align-items:center;gap:24px;padding:14px 26px;max-width:1680px;margin:0 auto}
.brandmark{font-weight:600;font-size:15px;white-space:nowrap}
.brandmark small{display:block;font-weight:300;font-size:11.5px;color:var(--footer);letter-spacing:.02em}
nav.views{display:flex;gap:4px;overflow-x:auto;scrollbar-width:none;flex:1}
nav.views::-webkit-scrollbar{display:none}
nav.views a{text-decoration:none;padding:7px 14px;border-radius:999px;font-size:13.5px;
  font-weight:500;color:var(--footer);white-space:nowrap}
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
.hero p.lede{color:var(--ondark);font-weight:300;font-size:17px;line-height:1.55}
.statrow{display:flex;flex-wrap:wrap;gap:12px;margin:26px 0 34px}
.stat{background:var(--panel);color:var(--body);border-radius:var(--radius);padding:16px 20px;min-width:132px;flex:1 1 132px}
.stat b{display:block;font-weight:300;font-size:34px;line-height:1.05}
.stat span{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.navcards{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}
.navcard{display:block;text-decoration:none;background:var(--panel);color:var(--body);
  border-radius:var(--radius);padding:22px;transition:transform .12s ease}
.navcard:hover{transform:translateY(-2px)}
.navcard b{display:block;font-size:18px;font-weight:500;margin-bottom:5px}
.navcard span{color:var(--muted);font-size:13.5px}

/* ---- filter bar */
.filters{position:sticky;top:57px;z-index:30;background:var(--bg);padding:12px 0 14px;
  border-bottom:1px solid var(--border);margin-bottom:18px}
.frow{display:flex;flex-wrap:wrap;gap:7px;align-items:center}
.frow+.frow{margin-top:7px}
.frow .lbl{font-size:11px;color:var(--footer);text-transform:uppercase;letter-spacing:.07em;margin-right:2px}
.frow .grow{margin-left:auto;font-size:12.5px;color:var(--footer)}
.frow .grow b{color:var(--panel);font-weight:500}
.chip{border:1px solid var(--borders);border-radius:999px;padding:4px 12px;font-size:12.5px;
  font-weight:500;color:var(--ondark);display:inline-flex;align-items:center;gap:6px}
.chip:hover{border-color:var(--ondarkm);color:#fff}
.chip .dot{width:8px;height:8px;border-radius:50%;background:currentColor;flex:none}
.chip.on{color:var(--body);background:var(--panel);border-color:var(--panel)}
.chip.clear{border-style:dashed}
.seg{display:inline-flex;border:1px solid var(--borders);border-radius:999px;overflow:hidden}
.seg button{padding:4px 13px;font-size:12.5px;font-weight:500;color:var(--ondark)}
.seg button+button{border-left:1px solid var(--borders)}
.seg button.on{background:var(--panel);color:var(--body)}
.countline{font-size:12.5px;color:var(--footer);margin-top:9px}
.countline b{color:var(--panel);font-weight:500}

/* ---- audit layout */
.audit{display:grid;grid-template-columns:190px minmax(0,1fr) 370px;gap:var(--gap);align-items:start}
.rail{position:sticky;top:150px;max-height:calc(100vh - 170px);overflow:auto}
.rail::-webkit-scrollbar{width:7px}
.rail::-webkit-scrollbar-thumb{background:var(--borders);border-radius:4px}
.pagelist{display:flex;flex-direction:column;gap:3px}
.pagelist button{text-align:left;padding:9px 12px;border-radius:9px;font-size:13.5px;color:var(--ondark);width:100%}
.pagelist button:hover{background:rgba(255,255,255,.07);color:#fff}
.pagelist button.on{background:var(--panel);color:var(--body);font-weight:500}
.pagelist button i{display:block;font-style:normal;font-size:11px;color:var(--footer)}
.pagelist button.on i{color:var(--muted)}

/* ---- screenshots */
.shot{margin-bottom:26px}
.shot h3{font-size:14px;font-weight:500;margin:0 0 9px;color:var(--ondark)}
.shot h3 em{font-style:normal;color:var(--footer);font-weight:300}
.frame{background:var(--surface);border-radius:12px;overflow:hidden;border:1px solid var(--border)}
.chrome{display:flex;align-items:center;gap:7px;padding:9px 12px;background:var(--sunken)}
.chrome i{width:9px;height:9px;border-radius:50%;background:var(--borders);display:block}
.chrome .addr{flex:1;margin-left:8px;background:var(--surface);border-radius:6px;padding:3px 10px;
  font-size:11px;color:var(--ondarkm);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.canvas{position:relative;line-height:0;background:#fff}
.canvas img{width:100%;height:auto;display:block}
.noimg{padding:56px 20px;text-align:center;color:var(--footer);font-size:13px;background:var(--surface);line-height:1.5}
.pin{position:absolute;transform:translate(-50%,-50%);width:26px;height:26px;border-radius:50%;
  background:var(--marker);color:#fff;font-size:11.5px;font-weight:600;display:flex;
  align-items:center;justify-content:center;cursor:pointer;
  box-shadow:0 0 0 2px #fff,0 2px 7px rgba(0,0,0,.4);
  transition:opacity .15s ease,transform .12s ease;z-index:2}
.pin:hover{transform:translate(-50%,-50%) scale(1.14)}
.pin.dim{opacity:.16;pointer-events:none}
.pin.on{outline:3px solid var(--eyebrow);outline-offset:2px;z-index:3}
@keyframes flash{0%,100%{transform:translate(-50%,-50%) scale(1)}35%{transform:translate(-50%,-50%) scale(1.5)}}
.pin.flash{animation:flash .55s ease}

/* ---- finding cards */
.cards{display:flex;flex-direction:column;gap:9px}
.cards .grouphead{font-size:11px;letter-spacing:.07em;text-transform:uppercase;color:var(--footer);margin:10px 0 1px}
.fcard{background:var(--panel);color:var(--body);border-radius:11px;padding:13px 14px;display:flex;
  gap:11px;cursor:pointer;transition:opacity .15s ease,box-shadow .12s ease;border:2px solid transparent}
.fcard.dim{opacity:.3}
.fcard.on{border-color:var(--eyebrow);box-shadow:0 6px 20px rgba(0,0,0,.28)}
.fnum{flex:none;width:24px;height:24px;border-radius:50%;background:var(--marker);color:#fff;
  font-size:11px;font-weight:600;display:flex;align-items:center;justify-content:center}
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
.tip{position:absolute;z-index:60;max-width:330px;background:var(--panel);color:var(--body);
  border-radius:11px;padding:13px 14px;box-shadow:0 12px 34px rgba(0,0,0,.42);pointer-events:none;display:none}
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
.toolbar{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin-bottom:6px}
.btn{border:1px solid var(--borders);border-radius:999px;padding:6px 15px;font-size:13px;font-weight:500}
.btn:hover{background:rgba(255,255,255,.09)}

/* ---- evidence button, shared by personas and sitemap */
.ev{font-size:9.5px;border:1px solid var(--rule);border-radius:4px;padding:2px 7px;
  color:var(--muted);background:none;letter-spacing:.02em}
.ev:hover{border-color:var(--marker);color:var(--marker)}
.evcard{margin-top:7px;background:var(--card);border-radius:7px;padding:9px 10px;font-size:11.5px;line-height:1.5;color:var(--muted)}
.evcard .eh{display:block;font-weight:600;color:var(--body);margin-bottom:3px;font-size:10.5px;letter-spacing:.04em;text-transform:uppercase}
.evcard a{color:var(--eyebrow)}

/* ---- personas */
.note{background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--eyebrow);
  border-radius:12px;padding:16px 20px;color:var(--ondark);font-size:13.2px;line-height:1.6;
  max-width:1100px;margin-bottom:22px}
.note b{color:var(--panel)}
.clusters{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin-bottom:26px}
.clus{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px 18px}
.clus b{display:block;font-weight:300;font-size:32px;line-height:1;color:var(--panel)}
.clus .cn{display:block;font-size:12.5px;color:var(--ondark);margin-top:6px;font-weight:500}
.clus .cm{display:block;font-size:11.5px;color:var(--ondarkm);margin-top:6px;line-height:1.5}
.pgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(390px,1fr));gap:16px;padding-bottom:30px}
.pcard{background:var(--panel);color:var(--body);border-radius:16px;padding:24px 26px 22px;border-top:4px solid}
.pcard .ph{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
.pcard h4{font-size:20px;font-weight:500;margin:0}
.pcard .wt{font-size:10.5px;font-weight:600;letter-spacing:.04em;color:#fff;border-radius:5px;padding:3px 8px}
.pcard .role{color:var(--muted);font-size:12.8px;margin:5px 0 0;line-height:1.45}
blockquote.q{margin:14px 0 14px;padding:2px 0 2px 13px;border-left:3px solid var(--rule);
  font-size:14.5px;font-weight:300;font-style:italic;line-height:1.5}
.pcard .ctx{font-size:13px;line-height:1.55;margin:0 0 16px}
.sub{font-size:10px;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);font-weight:600;margin:0 0 6px}
.needs{list-style:none;margin:0 0 16px;padding:0}
.needs li{font-size:12.6px;line-height:1.5;padding:4px 0 4px 15px;position:relative}
.needs li::before{content:"";position:absolute;left:2px;top:11px;width:5px;height:5px;border-radius:50%;background:var(--muted)}
.blk{border-top:1px solid var(--rule);padding-top:13px}
.blk .bi{display:flex;gap:9px;align-items:flex-start;margin-bottom:10px}
.blk .bi>i{width:6px;height:6px;border-radius:50%;flex:none;margin-top:6px}
.blk .bt{flex:1;font-size:12.4px;line-height:1.5}
.jrn{display:flex;gap:5px;flex-wrap:wrap;align-items:center;border-top:1px solid var(--rule);padding-top:13px;margin-top:4px}
.jrn span{font-size:11px;background:var(--card);border-radius:5px;padding:3px 8px}
.jrn em{font-style:normal;color:var(--muted);font-size:11px}

/* ---- sitemap board */
.legend{display:flex;gap:16px;flex-wrap:wrap;align-items:center;color:var(--ondarkm);font-size:11.5px;margin-bottom:16px}
.legend .k{display:inline-flex;align-items:center;gap:6px}
.legend .dash{width:22px;height:12px;border:1px dashed var(--dashed);border-radius:3px;display:inline-block}
.funnels{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px;margin-bottom:22px}
.funnel{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px 16px}
.funnel b{display:block;font-size:14px;font-weight:600}
.funnel .path{font-size:12.5px;color:var(--ondark);margin-top:6px;line-height:1.5}
.funnel .fn{display:block;font-size:11.5px;color:var(--ondarkm);margin-top:7px;font-style:italic;line-height:1.5}
.temp{border-radius:999px;padding:2px 8px;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#fff}
.board{display:flex;gap:14px;overflow-x:auto;padding:2px 26px 30px;margin:0 -26px;align-items:stretch;scroll-snap-type:x proximity}
.board::-webkit-scrollbar{height:9px}
.board::-webkit-scrollbar-thumb{background:var(--borders);border-radius:5px}
.board::-webkit-scrollbar-track{background:var(--surface);border-radius:5px}
.col{flex:0 0 308px;background:var(--surface);border:1px solid var(--border);border-radius:14px;
  padding:15px 15px 8px;scroll-snap-align:start}
.col.gone{display:none}
.col .cn{display:flex;align-items:baseline;gap:7px;flex-wrap:wrap}
.col .cn b{font-size:15.5px;font-weight:500}
.badge{font-size:8.5px;font-weight:600;letter-spacing:.05em;border-radius:4px;padding:2px 6px;
  background:var(--eyebrow);color:#fff;text-transform:uppercase}
.badge.tpl{background:var(--borders)}
.badge.p2{background:none;border:1px dashed var(--dashed);color:var(--ondarkm)}
.col .slug{font-size:11px;color:var(--ondarkm);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;margin:3px 0 11px}
.plain{background:var(--sunken);border-left:3px solid var(--eyebrow);border-radius:8px;
  padding:11px 12px;font-size:11.9px;color:var(--ondark);line-height:1.55;margin-bottom:11px}
.plain em{font-style:normal;color:var(--ondarkm);display:block;font-size:9.5px;letter-spacing:.07em;
  text-transform:uppercase;margin-bottom:5px}
.scard{background:var(--panel);color:var(--body);border-radius:10px;padding:11px 12px;margin-bottom:8px}
.scard.hide{display:none}
.scard b{font-size:12.6px;font-weight:600;display:block;margin-bottom:4px;line-height:1.35}
.scard p{font-size:11.6px;margin:0 0 8px;line-height:1.45;color:var(--muted)}
.scard.p2{background:none;border:1px dashed var(--dashed)}
.scard.p2 b{color:var(--ondark)}
.scard.p2 p{color:var(--ondarkm)}
.scard.p2 .ev{border-color:var(--dashed);color:var(--ondarkm)}
.scard.p2 .evcard{background:var(--sunken);color:var(--ondark)}
.scard.p2 .evcard .eh{color:var(--ondark)}
.dchips{display:flex;flex-wrap:wrap;gap:4px;align-items:center}
.dchip{border-radius:5px;padding:2px 6px;font-size:9.5px;font-weight:700;letter-spacing:.05em;color:#fff}

/* ---- database */
.dbgroup{margin-bottom:30px}
.dbgroup h2{font-size:13px;text-transform:uppercase;letter-spacing:.07em;color:var(--footer);margin-bottom:12px}
.dbgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}
.tbl{background:var(--panel);color:var(--body);border-radius:11px}
.tbl.p2{background:none;border:1px dashed var(--dashed)}
.tbl .th{background:var(--body);color:#fff;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  font-size:12px;font-weight:700;padding:9px 13px;display:flex;justify-content:space-between;
  align-items:center;gap:10px;border-radius:11px 11px 0 0}
.tbl.p2 .th{border-radius:10px 10px 0 0}
.tbl .th small{font-weight:400;color:var(--ondarkm);font-size:10px;font-family:Urbanist,sans-serif}
.tbl.p2 .th{background:var(--sunken);color:var(--ondark)}
.tbl ul{list-style:none;margin:0;padding:9px 13px}
.tbl li{font-size:11px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;padding:3px 0;
  border-bottom:1px dashed var(--rule);color:var(--body)}
.tbl li:last-child{border-bottom:0}
.tbl.p2 li{color:var(--ondark);border-color:var(--dashed)}
.tbl li .fk{color:var(--eyebrow);font-weight:700}
.tbl li .loc{color:var(--marker);font-weight:700}
.rel{background:var(--surface);border:1px solid var(--border);border-radius:11px;padding:14px 18px;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;line-height:2;color:var(--ondark)}
.dbnotes{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}
.dbnote{background:var(--surface);border:1px solid var(--border);border-radius:11px;padding:13px 16px;
  font-size:12.5px;line-height:1.55;color:var(--ondark)}
.dbnote b{display:block;color:var(--panel);margin-bottom:4px;font-size:13px}

/* ---- glossary */
.glgroup{margin-bottom:26px}
.glgroup h2{font-size:13px;text-transform:uppercase;letter-spacing:.07em;color:var(--footer);margin-bottom:12px}
.glgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:9px}
.gl{background:var(--panel);color:var(--body);border-radius:10px;padding:11px 14px;font-size:12.5px;line-height:1.5}
.gl b{font-size:13px}
.gl span{color:var(--muted)}

footer.bot{max-width:1680px;margin:0 auto;padding:30px 26px 40px;display:flex;
  justify-content:space-between;gap:16px;color:var(--footer);font-size:11.5px}

/* ---- responsive */
@media (max-width:1000px){
  .audit{grid-template-columns:minmax(0,1fr)}
  .rail{position:static;max-height:none;overflow:visible}
  .pagelist{flex-direction:row;flex-wrap:wrap}
  .pagelist button{width:auto}
  .grid2{grid-template-columns:minmax(0,1fr)}
  .filters{position:static}
  .pgrid{grid-template-columns:minmax(0,1fr)}
}
@media (max-width:820px){
  main{padding:18px}
  .top-in{padding:11px 16px;gap:14px}
  .top-meta{display:none}
  h1{font-size:26px}
  .tip{display:none!important}
  .countgrid{grid-template-columns:1fr}
  .board{padding:2px 18px 26px;margin:0 -18px}
  .col{flex-basis:270px}
  .pcard{padding:20px 20px 18px}
}
@media (pointer:coarse){ .tip{display:none!important} }
"""


# ---------------------------------------------------------------- js
JS = r"""
'use strict';
var DATA = JSON.parse(document.getElementById('report-data').textContent);
var IA = DATA.ia || null;
var HAS_AUDIT = !!(DATA.pages && DATA.pages.length);
var VIEWS = DATA.views;
var CATS = DATA.brand.categories, SEVS = DATA.brand.severity, C = DATA.brand.colors;
var CATNAMES = Object.keys(CATS);
var SEVNAMES = ['Critical','Moderate','Minor'];
var COST = DATA.costBands || {};
var DISCIPLINES = ['UX','CRO','SEO','LEAD'];
var DCOLOR = {UX:'#DF6630', CRO:'#2E8F86', SEO:'#D7586C', LEAD:'#866FBC'};
var TEMPC = {hot:'#D7586C', warm:'#DF6630', cold:'#1E8FD9'};

var ALL = [];
(DATA.pages || []).forEach(function(p){ p.sections.forEach(function(s){
  s.findings.forEach(function(f){ ALL.push(f); }); }); });
var BY_ID = {};
ALL.forEach(function(f){ BY_ID[f.id] = f; });

var state = { view:'home', page:((DATA.pages||[])[0]||{}).slug||null, finding:null,
              sev:new Set(), cat:new Set(), track:new Set(),
              disc:new Set(), phase:'all' };
var openEvidence = new Set();
var ignoreHash = false;

/* ---------------------------------------------------------- hash */
function readHash(){
  var h = location.hash.replace(/^#/,''), q = '', i = h.indexOf('?');
  if(i >= 0){ q = h.slice(i+1); h = h.slice(0,i); }
  var parts = h.split('/').filter(Boolean);
  var want = parts[0] || 'home';
  state.view = VIEWS.indexOf(want) >= 0 ? want : 'home';
  if(state.view === 'audit'){
    if(parts[1]) state.page = parts[1];
    state.finding = parts[2] || null;
  } else { state.finding = null; }
  state.sev = new Set(); state.cat = new Set(); state.track = new Set(); state.disc = new Set();
  state.phase = 'all';
  q.split('&').filter(Boolean).forEach(function(kv){
    var p = kv.split('='), k = p[0];
    var v = decodeURIComponent((p[1]||'').replace(/\+/g,' '));
    if(k === 'phase'){ if(v === '1' || v === '2') state.phase = v; return; }
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
  if(state.sev.size)  q.push('sev='  + encodeURIComponent(Array.from(state.sev).join('|')));
  if(state.cat.size)  q.push('cat='  + encodeURIComponent(Array.from(state.cat).join('|')));
  if(state.track.size)q.push('track='+ encodeURIComponent(Array.from(state.track).join('|')));
  if(state.disc.size) q.push('disc=' + encodeURIComponent(Array.from(state.disc).join('|')));
  if(state.phase !== 'all') q.push('phase=' + state.phase);
  return h + (q.length ? '?' + q.join('&') : '');
}
function syncHash(){ ignoreHash = true; location.hash = buildHash();
  setTimeout(function(){ ignoreHash = false; }, 0); }

/* ---------------------------------------------------------- utils */
function esc(s){ return String(s == null ? '' : s)
  .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function catColor(c){ return (CATS[c] || {}).color || C.body_muted; }
function sevColor(s){ return (SEVS[s] || {}).color || C.body_muted; }
function sevWeight(s){ return (SEVS[s] || {}).weight || 0; }
function effWeight(e){ return e === 'S' ? 1 : e === 'M' ? 2 : e === 'L' ? 3 : 4; }
function costOf(f){ return f.effort ? (COST[f.effort] || null) : null; }
function matches(f){
  if(state.sev.size && !state.sev.has(f.severity)) return false;
  if(state.cat.size && !(f.categories || []).some(function(c){ return state.cat.has(c); })) return false;
  if(state.track.size && !state.track.has(f.track)) return false;
  return true;
}
function findFinding(id){ return BY_ID[id] || null; }

/* ---------------------------------------------------------- shared bits */
var PLAIN = {track:false, effort:false, cost:false};
function tagsHtml(f, opts){
  opts = opts || {};
  var h = '<div class="tags">';
  (f.categories || []).forEach(function(c){
    h += '<span class="tag" style="background:' + catColor(c) + '">' + esc(c) + '</span>'; });
  if(f.severity) h += '<span class="tag" style="background:' + sevColor(f.severity) + '">' +
                      esc(f.severity.toUpperCase()) + '</span>';
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
/* The IA stores an id, never a copy of the finding's words. The text below is
   read live at render time, so rewording a finding cannot leave the two
   documents disagreeing. Contract §7. */
function evidenceHtml(fid){
  var f = findFinding(fid);
  if(!f) return '';
  var open = openEvidence.has(fid);
  var h = '<button class="ev" data-ev="' + esc(fid) + '">Evidence · ' +
          esc(f.section || f.page) + '</button>';
  if(open){
    h += '<div class="evcard"><span class="eh">' + esc(f.severity) + ' · ' +
         esc(f.page) + ' · ' + esc(f.section) + '</span>' + esc(f.observation);
    if(HAS_AUDIT) h += ' <a href="#/audit/' + esc(f.pageSlug) + '/' + esc(f.id) + '">see it on the page</a>';
    h += '</div>';
  }
  return h;
}

/* ---------------------------------------------------------- views */
function viewHome(){
  var m = DATA.meta, h = '';
  h += '<div class="hero"><div class="eyebrow">' + esc(m.kind) + '</div><h1>' + esc(m.client) + '</h1>' +
       '<p class="lede">' + esc(m.lede) + '</p></div>';

  var stats = [];
  if(HAS_AUDIT){
    var s = DATA.stats;
    stats.push([s.pages,'Pages audited'],[s.screens,'Screens captured'],
               [s.findings,'Findings'],[s.critical,'Critical']);
  }
  if(IA){
    if(IA.pages && IA.pages.length){
      var secs = 0;
      IA.pages.forEach(function(p){ secs += (p.sections||[]).length; });
      stats.push([IA.pages.length,'Pages proposed'],[secs,'Sections']);
    }
    if(IA.personas && IA.personas.length) stats.push([IA.personas.length,'Personas']);
  }
  if(stats.length){
    h += '<div class="statrow">';
    stats.forEach(function(s){ h += '<div class="stat"><b>' + s[0] + '</b><span>' + s[1] + '</span></div>'; });
    h += '</div>';
  }

  var blurbs = {
    audit:    ['Audit', 'The annotated walkthrough — screenshots with numbered pins and the finding behind each one.'],
    summary:  ['Summary', 'The diagnosis, the pattern across pages, and counts by category and severity.'],
    personas: ['Personas', 'Who the site has to serve, what stops them today, and the route each one takes.'],
    sitemap:  ['Sitemap &amp; IA', 'The proposed structure, section by section, with the reason each one earns its place.'],
    database: ['Database', 'The content model a developer builds from: tables, fields, relations and the decisions behind them.'],
    glossary: ['Glossary', 'Every specialist term used in this document, in plain language.'],
    actions:  ['Action items', 'Every fix, ordered by severity and effort, exportable as CSV.']
  };
  h += '<div class="navcards">';
  VIEWS.forEach(function(v){
    if(v === 'home' || !blurbs[v]) return;
    h += '<a class="navcard" href="#/' + v + '"><b>' + blurbs[v][0] + '</b><span>' + blurbs[v][1] + '</span></a>';
  });
  return h + '</div>';
}

function filterBar(){
  var h = '<div class="filters"><div class="frow"><span class="lbl">Severity</span>';
  SEVNAMES.forEach(function(s){
    h += '<button class="chip' + (state.sev.has(s) ? ' on' : '') + '" data-f="sev" data-v="' + esc(s) + '">' +
         '<i class="dot" style="color:' + sevColor(s) + '"></i>' + esc(s) + '</button>'; });
  h += '</div><div class="frow"><span class="lbl">Category</span>';
  CATNAMES.forEach(function(c){
    h += '<button class="chip' + (state.cat.has(c) ? ' on' : '') + '" data-f="cat" data-v="' + esc(c) + '">' +
         '<i class="dot" style="color:' + catColor(c) + '"></i>' + esc(c) + '</button>'; });
  h += '</div>';
  if(DATA.tracks.length){
    h += '<div class="frow"><span class="lbl">Track</span>';
    DATA.tracks.forEach(function(t){
      h += '<button class="chip' + (state.track.has(t) ? ' on' : '') + '" data-f="track" data-v="' + esc(t) + '">' +
           esc(t === 'now' ? 'Now' : 'Revamp') + '</button>'; });
    h += '</div>';
  }
  return h + '<div class="countline" id="countline"></div></div>';
}
function updateCount(){
  var el = document.getElementById('countline');
  if(!el) return;
  var n = ALL.filter(matches).length, any = state.sev.size || state.cat.size || state.track.size;
  el.innerHTML = 'Showing <b>' + n + '</b> of <b>' + ALL.length + '</b> findings' +
    (any ? ' &nbsp;·&nbsp; <button class="chip clear" id="clearf">Clear filters</button>' : '');
  var c = document.getElementById('clearf');
  if(c) c.onclick = function(){ state.sev.clear(); state.cat.clear(); state.track.clear();
    syncHash(); render(); };
}

function viewAudit(){
  var page = null, i;
  for(i=0;i<DATA.pages.length;i++) if(DATA.pages[i].slug === state.page) page = DATA.pages[i];
  if(!page){ page = DATA.pages[0]; state.page = page ? page.slug : null; }
  if(!page) return '<p>No pages in this report.</p>';

  var h = filterBar() + '<div class="audit"><div class="rail"><div class="pagelist">';
  DATA.pages.forEach(function(p){
    var n = 0; p.sections.forEach(function(s){ n += s.findings.length; });
    h += '<button data-page="' + esc(p.slug) + '"' + (p.slug === page.slug ? ' class="on"' : '') + '>' +
         esc(p.name) + '<i>' + n + ' finding' + (n === 1 ? '' : 's') + '</i></button>'; });
  h += '</div></div><div class="shots">';
  page.sections.forEach(function(s){
    h += '<div class="shot"><h3>' + esc(s.section || 'Section') + ' <em>· ' + s.findings.length + '</em></h3>' +
         '<div class="frame"><div class="chrome"><i></i><i></i><i></i><div class="addr">' +
         esc(DATA.meta.url || '') + '</div></div><div class="canvas">';
    if(s.img){
      h += '<img src="' + esc(s.img) + '" alt="' + esc(s.section) + '" loading="lazy">';
      s.findings.forEach(function(f){
        if(!f.hasMarker) return;
        h += '<button class="pin" data-id="' + esc(f.id) + '" style="left:' + (f.x*100) + '%;top:' +
             (f.y*100) + '%" aria-label="Finding ' + f.n + '">' + f.n + '</button>'; });
    } else {
      h += '<div class="noimg">Screenshot unavailable for this section.<br>The findings on the right still apply.</div>';
    }
    h += '</div></div></div>';
  });
  h += '</div><div class="rail"><div class="cards">';
  page.sections.forEach(function(s){
    h += '<div class="grouphead">' + esc(s.section || 'Section') + '</div>';
    s.findings.forEach(function(f){
      h += '<div class="fcard" data-id="' + esc(f.id) + '"><div class="fnum">' + f.n + '</div>' +
           '<div class="fbody">' + tagsHtml(f, PLAIN) + bodyHtml(f) + '</div></div>'; });
  });
  return h + '</div></div></div>';
}

function viewSummary(){
  var s = DATA.stats;
  var h = '<div class="eyebrow">General</div><h1>Summary</h1><div class="grid2"><div class="sheet">';
  (DATA.summary.narrative || []).forEach(function(p){ h += '<p>' + esc(p) + '</p>'; });
  if(!(DATA.summary.narrative || []).length) h += '<p class="mut">No summary narrative was recorded.</p>';
  h += '<h2 style="margin-top:22px">Severity</h2><div class="sevbar">';
  var tot = s.findings || 1;
  SEVNAMES.forEach(function(n){
    var v = s.severity[n] || 0;
    if(v) h += '<span style="width:' + (v/tot*100) + '%;background:' + sevColor(n) + '" title="' + n + ': ' + v + '"></span>'; });
  h += '</div><div class="sevkey">';
  SEVNAMES.forEach(function(n){
    h += '<span><i style="background:' + sevColor(n) + '"></i>' + n + ' — ' + (s.severity[n] || 0) + '</span>'; });
  h += '</div></div><div><div class="sheet"><h2>Findings by category</h2><div class="countgrid">';
  Object.keys(s.categories).sort(function(a,b){ return (s.categories[b]||0)-(s.categories[a]||0); })
    .forEach(function(c){
      h += '<div class="cnt"><span class="tag" style="background:' + catColor(c) + '">' + esc(c) +
           '</span><b>' + s.categories[c] + '</b></div>'; });
  h += '</div></div><div class="sheet" style="margin-top:var(--gap)"><h2>At a glance</h2><table class="metrics">' +
       '<tr><th>Metric</th><th class="num" style="text-align:right">Value</th></tr>' +
       row('Pages audited', s.pages) + row('Screens captured', s.screens) +
       row('Total findings', s.findings) + row('Critical', s.severity.Critical || 0) +
       row('Moderate', s.severity.Moderate || 0) + row('Minor', s.severity.Minor || 0);
  if(IA && IA.pages) h += row('Pages proposed', IA.pages.length);
  if(IA && IA.personas) h += row('Personas', IA.personas.length);
  if(DATA.meta.site_type) h += '<tr><td>Site type</td><td class="num">' + esc(DATA.meta.site_type) + '</td></tr>';
  if(DATA.meta.audience) h += '<tr><td>Audience</td><td class="num">' + esc(DATA.meta.audience) + '</td></tr>';
  h += '<tr><td>Dated</td><td class="num">' + esc(DATA.meta.date) + '</td></tr></table></div></div></div>';
  return h;
  function row(l, v){ return '<tr><td>' + l + '</td><td class="num">' + v + '</td></tr>'; }
}

function viewPersonas(){
  if(!IA) return viewHome();
  var ev = IA.evidence || {}, people = IA.personas || [];
  var pageName = {};
  (IA.pages || []).forEach(function(p){ pageName[p.id] = p.name; });

  var h = '<div class="eyebrow">Personas</div><h1>Who the site has to serve</h1>';
  if(ev.note) h += '<div class="note"><b>Basis.</b> ' + esc(ev.note) + '</div>';

  /* The cluster row is the argument. Without it a persona is an assertion. */
  if((ev.clusters || []).length){
    h += '<div class="clusters">';
    ev.clusters.forEach(function(c){
      h += '<div class="clus"><b>' + esc(c.n != null ? c.n : '') + '</b>' +
           '<span class="cn">' + esc(c.name || '') + '</span>' +
           (c.members ? '<span class="cm">' + esc(c.members) + '</span>' : '') + '</div>'; });
    h += '</div>';
  }
  if(!people.length) return h + '<p style="color:var(--footer)">No personas were recorded.</p>';

  h += '<div class="pgrid">';
  people.forEach(function(p){
    var colour = p.colour || DCOLOR.UX;
    h += '<div class="pcard" style="border-top-color:' + esc(colour) + '">' +
         '<div class="ph"><h4>' + esc(p.name) + '</h4>' +
         (p.weight ? '<span class="wt" style="background:' + esc(colour) + '">' + esc(p.weight) + '</span>' : '') +
         '</div><p class="role">' + esc(p.role || '') + '</p>';
    if(p.quote) h += '<blockquote class="q">“' + esc(p.quote) + '”</blockquote>';
    if(p.context) h += '<p class="ctx">' + esc(p.context) + '</p>';
    if((p.wants || []).length){
      h += '<p class="sub">What they need</p><ul class="needs">';
      p.wants.forEach(function(w){ h += '<li>' + esc(w) + '</li>'; });
      h += '</ul>';
    }
    if((p.blocked_by || []).length){
      h += '<div class="blk"><p class="sub">What stops them today</p>';
      p.blocked_by.forEach(function(b){
        h += '<div class="bi"><i style="background:' + sevColor('Critical') + '"></i><div class="bt">' +
             esc(b.text || '') + (b.fid ? '<div style="margin-top:5px">' + evidenceHtml(b.fid) + '</div>' : '') +
             '</div></div>'; });
      h += '</div>';
    }
    if((p.journey || []).length){
      h += '<div class="jrn">';
      p.journey.forEach(function(id, i){
        if(i) h += '<em>→</em>';
        h += '<span>' + esc(pageName[id] || id) + '</span>'; });
      h += '</div>';
    }
    h += '</div>';
  });
  return h + '</div>';
}

function sectionVisible(s){
  var ph = s.phase || 1;
  if(state.phase !== 'all' && String(ph) !== state.phase) return false;
  if(state.disc.size && !(s.chips || []).some(function(c){ return state.disc.has(c); })) return false;
  return true;
}

function viewSitemap(){
  if(!IA) return viewHome();
  var pages = IA.pages || [];

  var h = '<div class="filters"><div class="frow"><span class="lbl">Discipline</span>';
  DISCIPLINES.forEach(function(d){
    h += '<button class="chip' + (state.disc.has(d) ? ' on' : '') + '" data-f="disc" data-v="' + d + '">' +
         '<i class="dot" style="color:' + DCOLOR[d] + '"></i>' + d + '</button>'; });
  h += '<span class="lbl" style="margin-left:16px">Scope</span><span class="seg">';
  [['all','All phases'],['1','Phase 1'],['2','Phase 2']].forEach(function(o){
    h += '<button data-phase="' + o[0] + '"' + (state.phase === o[0] ? ' class="on"' : '') + '>' + o[1] + '</button>'; });
  h += '</span><span class="grow" id="iacount"></span></div></div>';

  h += '<div class="eyebrow">Sitemap &amp; information architecture</div><h1>Proposed structure</h1>';

  h += '<div class="legend"><span class="k"><i class="dash"></i>Phase 2 — needs content or budget that does not exist at launch</span>' +
       '<span class="k"><span class="badge">New</span>page that does not exist today</span>' +
       '<span class="k"><span class="badge tpl">Template</span>one design, many records</span>';
  if(HAS_AUDIT) h += '<span class="k">Evidence buttons open the audit finding that justifies the section</span>';
  h += '</div>';

  if((IA.funnels || []).length){
    h += '<div class="funnels">';
    IA.funnels.forEach(function(f){
      var t = (f.temp || '').toLowerCase();
      h += '<div class="funnel"><b>' + esc(f.name || 'Funnel') +
           (t ? ' <span class="temp" style="background:' + (TEMPC[t] || C.eyebrow) + '">' + esc(t) + '</span>' : '') +
           '</b><div class="path">' + esc(f.path || '') + '</div>' +
           (f.note ? '<span class="fn">' + esc(f.note) + '</span>' : '') + '</div>'; });
    h += '</div>';
  }

  h += '<div class="board">';
  pages.forEach(function(p){
    h += '<div class="col" data-page-id="' + esc(p.id) + '"><div class="cn"><b>' + esc(p.name) + '</b>';
    if(p.isnew) h += '<span class="badge">New</span>';
    if(p.template) h += '<span class="badge tpl">Template</span>';
    if((p.phase || 1) === 2) h += '<span class="badge p2">Phase 2</span>';
    h += '</div><div class="slug">' + esc(p.slug || '') + '</div>';
    if(p.plain) h += '<div class="plain"><em>In plain words</em>' + esc(p.plain) + '</div>';
    (p.sections || []).forEach(function(s, si){
      var p2 = (s.phase || 1) === 2;
      h += '<div class="scard' + (p2 ? ' p2' : '') + '" data-sec="' + esc(p.id) + ':' + si + '">' +
           '<b>' + esc(s.t || '') + '</b><p>' + esc(s.d || '') + '</p><div class="dchips">';
      (s.chips || []).forEach(function(c){
        h += '<span class="dchip" style="background:' + (DCOLOR[c] || C.body_muted) + '">' + esc(c) + '</span>'; });
      if(s.fid) h += evidenceHtml(s.fid);
      h += '</div></div>';
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
      var ref = (el.dataset.sec || '').split(':'), page = null;
      (IA.pages || []).forEach(function(p){ if(p.id === ref[0]) page = p; });
      var s = page ? (page.sections || [])[+ref[1]] : null;
      var ok = s ? sectionVisible(s) : true;
      tot += 1;
      if(ok){ shown += 1; any = true; }
      el.classList.toggle('hide', !ok);
    });
    col.classList.toggle('gone', !any);
  });
  var el = document.getElementById('iacount');
  if(el){
    var filtered = state.disc.size || state.phase !== 'all';
    el.innerHTML = '<b>' + shown + '</b>' + (filtered ? ' of <b>' + tot + '</b>' : '') + ' sections' +
      (filtered ? ' &nbsp;<button class="chip clear" id="cleari">Clear</button>' : '');
    var c = document.getElementById('cleari');
    if(c) c.onclick = function(){ state.disc.clear(); state.phase = 'all'; syncHash(); render(); };
  }
}

function viewDatabase(){
  if(!IA || !IA.db) return viewHome();
  var db = IA.db;
  var h = '<div class="eyebrow">For the developer</div><h1>Content model</h1>';
  if(db.note) h += '<div class="note">' + esc(db.note) + '</div>';
  (db.groups || []).forEach(function(g){
    h += '<div class="dbgroup"><h2>' + esc(g.name || 'Tables') + '</h2><div class="dbgrid">';
    (g.tables || []).forEach(function(t){
      var p2 = (t.phase || g.phase || 1) === 2;
      h += '<div class="tbl' + (p2 ? ' p2' : '') + '"><div class="th">' + esc(t.name || '') +
           (t.note ? '<small>' + esc(t.note) + '</small>' : '') + '</div><ul>';
      (t.fields || []).forEach(function(f){
        h += '<li>' + esc(f.f || '') +
             (f.loc ? ' <span class="loc">loc</span>' : '') +
             (f.fk ? ' <span class="fk">FK→' + esc(f.fk) + '</span>' : '') + '</li>'; });
      h += '</ul></div>';
    });
    h += '</div></div>';
  });
  if((db.relations || []).length){
    h += '<div class="dbgroup"><h2>Relationships</h2><div class="rel">';
    db.relations.forEach(function(r){ h += esc(r) + '<br>'; });
    h += '</div></div>';
  }
  if((db.notes || []).length){
    h += '<div class="dbgroup"><h2>Decisions worth keeping</h2><div class="dbnotes">';
    db.notes.forEach(function(n){
      h += '<div class="dbnote"><b>' + esc(n.t || '') + '</b>' + esc(n.d || '') + '</div>'; });
    h += '</div></div>';
  }
  return h;
}

function viewGlossary(){
  if(!IA || !IA.glossary) return viewHome();
  var groups = {}, order = [];
  IA.glossary.forEach(function(g){
    var k = g.group || 'General';
    if(!groups[k]){ groups[k] = []; order.push(k); }
    groups[k].push(g);
  });
  var h = '<div class="eyebrow">Plain language</div><h1>Glossary</h1>' +
          '<div class="note">Every specialist term used anywhere in this document. ' +
          'If a term appears on the board and not here, one of the two is wrong.</div>';
  order.forEach(function(k){
    h += '<div class="glgroup"><h2>' + esc(k) + '</h2><div class="glgrid">';
    groups[k].forEach(function(g){
      h += '<div class="gl"><b>' + esc(g.term) + '</b> <span>— ' + esc(g.def) + '</span></div>'; });
    h += '</div></div>';
  });
  return h;
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
           (group.length === 1 ? '' : 's') + '</span></div>' + list(group); });
    var untracked = items.filter(function(f){ return !f.track; });
    if(untracked.length) h += '<div class="trackhead"><h2>Unassigned</h2><span>' +
      untracked.length + '</span></div>' + list(untracked);
  } else { h += list(items); }
  return h;

  function list(arr){
    if(!arr.length) return '<p style="color:var(--footer)">Nothing in this track.</p>';
    var out = '';
    arr.forEach(function(f, i){
      out += '<div class="act" data-id="' + esc(f.id) + '"><div class="rank">' + (i+1) + '</div>' +
             '<div class="fbody">' + tagsHtml(f) + '<p>' + esc(f.fix || f.observation) + '</p>' +
             '<div class="where">' + esc(f.page) + ' · ' + esc(f.section) +
             ' &nbsp;<a href="#/audit/' + esc(f.pageSlug) + '/' + esc(f.id) +
             '" style="color:var(--eyebrow)">see it on the page</a></div></div></div>'; });
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
               f.observation, f.fix, f.scope, f.benchmark, f.principle]); });
  var csv = rows.map(function(r){
    return r.map(function(v){ return '"' + String(v == null ? '' : v).replace(/"/g,'""') + '"'; }).join(',');
  }).join('\r\n');
  var blob = new Blob(['﻿' + csv], {type:'text/csv;charset=utf-8'});
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = (DATA.meta.client || 'report').replace(/[^a-z0-9]+/gi,'-').toLowerCase() + '-action-items.csv';
  document.body.appendChild(a); a.click();
  setTimeout(function(){ URL.revokeObjectURL(a.href); a.remove(); }, 400);
}

/* ---------------------------------------------------------- filters + focus */
function applyFilters(){
  ['.pin','.fcard','.act'].forEach(function(sel){
    document.querySelectorAll(sel).forEach(function(el){
      var f = findFinding(el.dataset.id);
      el.classList.toggle('dim', !(f && matches(f)));
    });
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
      pin.classList.remove('flash'); void pin.offsetWidth; pin.classList.add('flash');
    }
  }
  if(card){ card.classList.add('on'); if(opts.scrollCard) card.scrollIntoView({block:'nearest', behavior:'smooth'}); }
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
  if(top + tip.offsetHeight > window.scrollY + window.innerHeight - 10)
    top = r.top + window.scrollY - tip.offsetHeight - 10;
  tip.style.top = top + 'px';
  tip.style.left = left + 'px';
}
function hideTip(){ tip.classList.remove('show'); }

/* ---------------------------------------------------------- keyboard */
function stepPin(dir){
  var pins = Array.prototype.slice.call(document.querySelectorAll('.pin:not(.dim)'));
  if(!pins.length) return;
  var idx = -1, i;
  for(i=0;i<pins.length;i++) if(pins[i].dataset.id === state.finding) idx = i;
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
  home: viewHome, audit: viewAudit, summary: viewSummary, personas: viewPersonas,
  sitemap: viewSitemap, database: viewDatabase, glossary: viewGlossary, actions: viewActions
};

function render(){
  var app = document.getElementById('app');
  var key = VIEWS.indexOf(state.view) >= 0 ? state.view : 'home';
  state.view = key;
  app.innerHTML = (RENDERERS[key] || viewHome)();

  /* Compare an explicit view key. classList.toggle(cls, force) with `force`
     evaluating to undefined does NOT clear the class - it falls back to a plain
     flip, which is how a report ends up with two active tabs after a re-render. */
  document.querySelectorAll('nav.views a').forEach(function(a){
    a.classList.toggle('active', a.getAttribute('data-view') === key); });

  if(key === 'sitemap') applyIaFilters(); else applyFilters();
  applyFocus({scrollPin:!!state.finding, scrollCard:!!state.finding});
  window.scrollTo({top:0});
}

document.addEventListener('click', function(e){
  var t = e.target;
  var ev = t.closest && t.closest('[data-ev]');
  if(ev){
    var fid = ev.dataset.ev;
    if(openEvidence.has(fid)) openEvidence.delete(fid); else openEvidence.add(fid);
    render(); return;
  }
  var ph = t.closest && t.closest('[data-phase]');
  if(ph){ state.phase = ph.dataset.phase; syncHash(); render(); return; }
  var chip = t.closest && t.closest('.chip[data-f]');
  if(chip){
    var set = state[chip.dataset.f];
    if(set.has(chip.dataset.v)) set.delete(chip.dataset.v); else set.add(chip.dataset.v);
    chip.classList.toggle('on');
    syncHash();
    if(chip.dataset.f === 'disc') applyIaFilters(); else applyFilters();
    return;
  }
  var pb = t.closest && t.closest('[data-page]');
  if(pb){ state.page = pb.dataset.page; state.finding = null; syncHash(); render(); return; }
  var pin = t.closest && t.closest('.pin');
  if(pin){ state.finding = (state.finding === pin.dataset.id) ? null : pin.dataset.id;
    syncHash(); applyFocus({scrollCard:true}); return; }
  var fc = t.closest && t.closest('.fcard');
  if(fc){ state.finding = (state.finding === fc.dataset.id) ? null : fc.dataset.id;
    syncHash(); applyFocus({scrollPin:true}); return; }
  if(t.id === 'csv'){ exportCsv(); return; }
});
document.addEventListener('mouseover', function(e){
  var pin = e.target.closest && e.target.closest('.pin');
  if(pin){ var f = findFinding(pin.dataset.id); if(f) showTip(pin, f); }
});
document.addEventListener('mouseout', function(e){
  var pin = e.target.closest && e.target.closest('.pin');
  if(pin && state.finding !== pin.dataset.id) hideTip();
});
window.addEventListener('hashchange', function(){
  if(ignoreHash) return;
  readHash(); render();
});

/* render() runs LAST, after every view function above it is defined. A cold
   load straight to #/sitemap with this call placed earlier dies in the temporal
   dead zone before it paints anything. */
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
  <div class="brandmark">__CLIENT__<small>__AGENCY__ · __KIND__</small></div>
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


def render_css(colors, assets_dir):
    css = CSS.replace("__FONTFACES__", font_faces(assets_dir))
    for token, key in COLOR_TOKENS:
        css = css.replace(token, colors[key])
    return css


def render(brand, meta, model, ia, assets_dir, cost_bands=None):
    """brand: brand.json dict. meta: client/url/date/kind/lede/agency/footers.
    model: report-data.json dict or None. ia: ia.json dict or None."""
    views = views_for(model, ia)

    payload = {
        "schema": SCHEMA,
        "views": views,
        "meta": meta,
        "brand": {"categories": brand["categories"], "severity": brand["severity"],
                  "colors": brand["colors"]},
        "pages": (model or {}).get("pages", []),
        "summary": (model or {}).get("summary", {"narrative": [], "counts": {}}),
        "stats": (model or {}).get("stats", {}),
        "tracks": (model or {}).get("tracks", []),
        "ia": ia,
        "costBands": cost_bands or {},
    }
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")

    return (HTML
            .replace("__CSS__", render_css(brand["colors"], assets_dir))
            .replace("__NAV__", nav_html(views))
            .replace("__JS__", JS)
            .replace("__DATA__", data)
            .replace("__TITLE__", "%s — %s" % (meta["client"], meta["kind"]))
            .replace("__CLIENT__", meta["client"])
            .replace("__AGENCY__", meta.get("agency", ""))
            .replace("__KIND__", meta["kind"])
            .replace("__URL__", meta.get("url", ""))
            .replace("__DATE__", meta.get("date", date.today().isoformat()))
            .replace("__FOOTL__", meta.get("footer_left", ""))
            .replace("__FOOTR__", meta.get("footer_right", "")))
