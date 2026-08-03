#!/usr/bin/env python3
"""
capture.py - Stage 1 of a website assessment.

Opens a site in Chromium, splits each page into visual sections, screenshots
each section at desktop and mobile widths, and records:
  - the bounding box of every interactive / text element inside each section
    (so markers can later be pinned to the exact element a finding refers to)
  - hard technical evidence: contrast failures, missing alt text, heading
    outline, meta tags, form labels, tap-target sizes, load timing

Output goes to <out>/ :
  screens/<page>__<section>.png        section screenshots (desktop)
  screens/<page>__<section>@mobile.png section screenshots (mobile)
  screens/<page>__full.png             whole page
  page-data.json                       sections, elements, technical evidence

Usage:
  python3 capture.py --url https://example.com --out ./audit
  python3 capture.py --url https://example.com/a --url https://example.com/b --out ./audit
  python3 capture.py --url https://example.com --crawl 6 --out ./audit
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

DESKTOP = {"width": 1440, "height": 900}
MOBILE = {"width": 390, "height": 844}

# ---------------------------------------------------------------- page script
# Runs inside the browser. Returns sections + elements + technical evidence.
PAGE_JS = r"""
() => {
  const R = (n) => Math.round(n * 100) / 100;

  // ---- colour helpers -------------------------------------------------
  const parseRGB = (s) => {
    if (!s) return null;
    const m = s.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(',').map(v => parseFloat(v.trim()));
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  const lum = (c) => {
    const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b);
  };
  const contrast = (a, b) => {
    const l1 = lum(a), l2 = lum(b);
    return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
  };
  const blend = (fg, bg) => ({
    r: fg.r * fg.a + bg.r * (1 - fg.a),
    g: fg.g * fg.a + bg.g * (1 - fg.a),
    b: fg.b * fg.a + bg.b * (1 - fg.a),
    a: 1
  });
  const effectiveBg = (el) => {
    let node = el;
    let acc = null;
    while (node && node !== document.documentElement) {
      const cs = getComputedStyle(node);
      const c = parseRGB(cs.backgroundColor);
      if (c && c.a > 0) {
        acc = acc ? blend(acc, c) : c;
        if (acc.a >= 0.99) return acc;
      }
      node = node.parentElement;
    }
    return acc && acc.a >= 0.99 ? acc : { r: 255, g: 255, b: 255, a: 1 };
  };
  const hex = (c) => '#' + [c.r, c.g, c.b].map(v =>
    Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, '0')).join('').toUpperCase();

  // ---- selector -------------------------------------------------------
  const cssPath = (el) => {
    if (el.id && /^[A-Za-z][\w-]*$/.test(el.id)) return '#' + el.id;
    const parts = [];
    let node = el;
    while (node && node.nodeType === 1 && parts.length < 5) {
      let part = node.tagName.toLowerCase();
      if (node.id && /^[A-Za-z][\w-]*$/.test(node.id)) { parts.unshift('#' + node.id); break; }
      const cls = (node.className && typeof node.className === 'string')
        ? node.className.trim().split(/\s+/).filter(c => /^[A-Za-z][\w-]*$/.test(c)).slice(0, 2)
        : [];
      if (cls.length) part += '.' + cls.join('.');
      const parent = node.parentElement;
      if (parent) {
        const sibs = Array.from(parent.children).filter(c => c.tagName === node.tagName);
        if (sibs.length > 1) part += `:nth-of-type(${sibs.indexOf(node) + 1})`;
      }
      parts.unshift(part);
      node = node.parentElement;
    }
    return parts.join(' > ');
  };

  const visible = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.05) return false;
    const r = el.getBoundingClientRect();
    return r.width > 1 && r.height > 1;
  };

  const docTop = (el) => {
    const r = el.getBoundingClientRect();
    return { x: R(r.left + window.scrollX), y: R(r.top + window.scrollY), w: R(r.width), h: R(r.height) };
  };

  // ---- section detection ----------------------------------------------
  // Candidates: landmarks, plus wide/tall block children of the main wrapper.
  const vw = window.innerWidth;
  const seen = new Set();
  const candidates = [];

  const consider = (el, forced) => {
    if (!el || seen.has(el) || !visible(el)) return;
    const b = docTop(el);
    if (!forced && (b.w < vw * 0.55 || b.h < 90)) return;
    if (b.h > document.documentElement.scrollHeight * 0.92 && !forced) return;
    seen.add(el);
    candidates.push({ el, box: b, forced: !!forced });
  };

  ['header', 'nav[role="navigation"]', 'footer'].forEach(sel =>
    document.querySelectorAll(sel).forEach(el => consider(el, true)));

  // Find the densest content wrapper and walk its direct children.
  let wrapper = document.querySelector('main') || document.querySelector('#__next, #root, #app') || document.body;
  let guard = 0;
  while (wrapper && wrapper.children.length === 1 && guard++ < 6) {
    const only = wrapper.children[0];
    if (only.getBoundingClientRect().height > window.innerHeight * 0.5) wrapper = only; else break;
  }
  Array.from(wrapper.children).forEach(el => consider(el, false));
  document.querySelectorAll('main > section, main > div[class*="section"], body > section').forEach(el => consider(el, false));

  candidates.sort((a, b) => a.box.y - b.box.y);

  // Drop sections fully contained in an earlier one.
  const sections = [];
  candidates.forEach(c => {
    const inside = sections.some(s =>
      c.box.y >= s.box.y - 2 && (c.box.y + c.box.h) <= (s.box.y + s.box.h) + 2 && !c.forced);
    if (!inside) sections.push(c);
  });

  const labelFor = (el, i) => {
    const tag = el.tagName.toLowerCase();
    if (tag === 'header') return 'Nav Bar';
    if (tag === 'footer') return 'Footer';
    if (tag === 'nav') return 'Navigation';
    const aria = el.getAttribute('aria-label');
    if (aria && aria.length < 40) return aria.trim();
    const h = el.querySelector('h1, h2, h3');
    if (h && h.innerText.trim()) {
      const t = h.innerText.trim().replace(/\s+/g, ' ');
      return t.length > 42 ? t.slice(0, 42).trim() + '…' : t;
    }
    if (i === 0) return 'Hero';
    return 'Section ' + (i + 1);
  };

  // ---- per-section element inventory -----------------------------------
  const INTERESTING = 'a,button,input,select,textarea,h1,h2,h3,h4,img,svg,label,[role="button"],[role="link"],form,li>a,p';

  const out = sections.map((s, i) => {
    const el = s.el;
    const els = [];
    const pool = Array.from(el.querySelectorAll(INTERESTING)).filter(visible).slice(0, 220);
    pool.forEach(node => {
      const b = docTop(node);
      const cs = getComputedStyle(node);
      const txt = (node.innerText || node.value || node.getAttribute('alt') || '').trim().replace(/\s+/g, ' ');
      const fg = parseRGB(cs.color) || { r: 0, g: 0, b: 0, a: 1 };
      const bg = effectiveBg(node);
      const hasText = txt.length > 0 && node.children.length === 0;
      const fontPx = parseFloat(cs.fontSize) || 16;
      const bold = (parseInt(cs.fontWeight, 10) || 400) >= 700;
      const large = fontPx >= 24 || (fontPx >= 18.66 && bold);
      let cr = null;
      if (hasText) cr = R(contrast(fg.a < 1 ? blend(fg, bg) : fg, bg));
      els.push({
        tag: node.tagName.toLowerCase(),
        sel: cssPath(node),
        text: txt.slice(0, 90),
        box: b,
        rel: { x: R((b.x - s.box.x) / Math.max(1, s.box.w)), y: R((b.y - s.box.y) / Math.max(1, s.box.h)),
               w: R(b.w / Math.max(1, s.box.w)), h: R(b.h / Math.max(1, s.box.h)) },
        color: hex(fg), bg: hex(bg), font_px: R(fontPx), bold: bold,
        contrast: cr,
        contrast_min: large ? 3.0 : 4.5,
        contrast_fail: cr !== null ? cr < (large ? 3.0 : 4.5) : null,
        alt: node.tagName === 'IMG' ? (node.getAttribute('alt') === null ? null : node.getAttribute('alt')) : undefined,
        href: node.tagName === 'A' ? node.getAttribute('href') : undefined,
        aria_label: node.getAttribute('aria-label') || undefined,
        tap_small: (/^(a|button|input|select)$/.test(node.tagName.toLowerCase()) && (b.w < 44 || b.h < 44)) || undefined
      });
    });
    return { index: i, label: labelFor(el, i), tag: el.tagName.toLowerCase(), sel: cssPath(el), box: s.box, elements: els };
  });

  // ---- page-level technical evidence ------------------------------------
  const headings = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6'))
    .filter(visible).slice(0, 60)
    .map(h => ({ level: +h.tagName[1], text: h.innerText.trim().replace(/\s+/g, ' ').slice(0, 110) }));

  const imgs = Array.from(document.images);
  const links = Array.from(document.querySelectorAll('a[href]'));
  const vague = /^(click here|read more|learn more|here|more|link|this)$/i;

  const meta = (n) => { const m = document.querySelector(`meta[name="${n}"]`); return m ? m.content : null; };
  const og = (p) => { const m = document.querySelector(`meta[property="og:${p}"]`); return m ? m.content : null; };

  const nav = performance.getEntriesByType('navigation')[0];

  const technical = {
    title: document.title || null,
    title_len: (document.title || '').length,
    meta_description: meta('description'),
    meta_description_len: (meta('description') || '').length,
    meta_robots: meta('robots'),
    canonical: (document.querySelector('link[rel="canonical"]') || {}).href || null,
    lang: document.documentElement.lang || null,
    dir: document.documentElement.dir || null,
    viewport_meta: !!document.querySelector('meta[name="viewport"]'),
    og_title: og('title'), og_image: og('image'), og_description: og('description'),
    structured_data: Array.from(document.querySelectorAll('script[type="application/ld+json"]')).map(s => {
      try { const j = JSON.parse(s.textContent); return j['@type'] || (Array.isArray(j) ? j.map(x => x['@type']).join(',') : 'unknown'); }
      catch (e) { return 'invalid-json'; }
    }),
    favicon: !!document.querySelector('link[rel*="icon"]'),
    headings: headings,
    h1_count: headings.filter(h => h.level === 1).length,
    heading_skips: (() => {
      const skips = []; let prev = 0;
      headings.forEach(h => { if (prev && h.level > prev + 1) skips.push(`h${prev} → h${h.level}: "${h.text.slice(0, 50)}"`); prev = h.level; });
      return skips;
    })(),
    images_total: imgs.length,
    images_missing_alt: imgs.filter(i => i.getAttribute('alt') === null).map(i => (i.currentSrc || i.src || '').split('/').pop()).slice(0, 25),
    images_oversized: imgs.filter(i => i.naturalWidth > 0 && i.naturalWidth > i.clientWidth * 2.2 && i.clientWidth > 40)
      .map(i => ({ src: (i.currentSrc || i.src || '').split('/').pop(), natural: i.naturalWidth, displayed: i.clientWidth })).slice(0, 20),
    links_total: links.length,
    links_vague: links.filter(a => vague.test((a.innerText || '').trim())).map(a => (a.innerText || '').trim()).slice(0, 20),
    links_empty: links.filter(a => !(a.innerText || '').trim() && !a.getAttribute('aria-label') && !a.querySelector('img[alt]:not([alt=""])')).length,
    links_new_tab_no_warning: links.filter(a => a.target === '__blank' || a.target === '_blank').filter(a => !/new (tab|window)/i.test(a.getAttribute('aria-label') || '')).length,
    external_links: links.filter(a => { try { return new URL(a.href, location.href).hostname !== location.hostname; } catch (e) { return false; } }).length,
    forms: Array.from(document.forms).map(f => ({
      sel: cssPath(f),
      fields: Array.from(f.elements).filter(e => /input|select|textarea/i.test(e.tagName)).length,
      unlabelled: Array.from(f.elements).filter(e => /input|select|textarea/i.test(e.tagName))
        .filter(e => e.type !== 'hidden' && e.type !== 'submit' &&
          !e.getAttribute('aria-label') && !e.labels?.length && !e.getAttribute('placeholder')).length,
      required: Array.from(f.elements).filter(e => e.required).length,
      submit_text: (f.querySelector('[type=submit], button') || {}).innerText || null
    })),
    skip_link: !!document.querySelector('a[href^="#"][class*="skip"], a[href^="#main"], a[href^="#content"]'),
    landmarks: {
      header: document.querySelectorAll('header').length,
      nav: document.querySelectorAll('nav').length,
      main: document.querySelectorAll('main').length,
      footer: document.querySelectorAll('footer').length
    },
    focus_outline_suppressed: (() => {
      let n = 0;
      Array.from(document.querySelectorAll('a,button,input')).slice(0, 120).forEach(el => {
        const cs = getComputedStyle(el, ':focus-visible');
        if (cs.outlineStyle === 'none' && cs.boxShadow === 'none') n++;
      });
      return n;
    })(),
    word_count: (document.body.innerText || '').trim().split(/\s+/).length,
    scroll_height: document.documentElement.scrollHeight,
    timing: nav ? {
      dom_content_loaded_ms: R(nav.domContentLoadedEventEnd),
      load_ms: R(nav.loadEventEnd),
      ttfb_ms: R(nav.responseStart - nav.requestStart),
      transfer_kb: R((nav.transferSize || 0) / 1024)
    } : null,
    resources: (() => {
      const rs = performance.getEntriesByType('resource');
      const by = {};
      rs.forEach(r => {
        const t = r.initiatorType || 'other';
        by[t] = by[t] || { count: 0, kb: 0 };
        by[t].count++; by[t].kb += (r.transferSize || 0) / 1024;
      });
      Object.values(by).forEach(v => v.kb = R(v.kb));
      return by;
    })(),
    heaviest_resources: performance.getEntriesByType('resource')
      .filter(r => r.transferSize > 120000)
      .sort((a, b) => b.transferSize - a.transferSize).slice(0, 10)
      .map(r => ({ url: r.name.split('/').pop().slice(0, 70), kb: R(r.transferSize / 1024), type: r.initiatorType }))
  };

  // Roll contrast failures up to page level, de-duplicated by colour pair.
  const pairs = {};
  out.forEach(s => s.elements.forEach(e => {
    if (e.contrast_fail) {
      const k = e.color + '|' + e.bg;
      pairs[k] = pairs[k] || { fg: e.color, bg: e.bg, ratio: e.contrast, required: e.contrast_min, count: 0, sample: e.text, sections: [] };
      pairs[k].count++;
      if (!pairs[k].sections.includes(s.label)) pairs[k].sections.push(s.label);
    }
  }));
  technical.contrast_failures = Object.values(pairs).sort((a, b) => a.ratio - b.ratio).slice(0, 15);
  technical.tap_targets_small = out.reduce((n, s) => n + s.elements.filter(e => e.tap_small).length, 0);

  return { sections: out, technical: technical, url: location.href, viewport: { w: vw, h: window.innerHeight } };
}
"""


def slug(s: str, maxlen: int = 46) -> str:
    s = re.sub(r"[^\w\s-]", "", s or "").strip().lower()
    s = re.sub(r"[\s_-]+", "-", s)
    return (s or "section")[:maxlen].strip("-")


def page_slug(url: str) -> str:
    p = urlparse(url)
    path = p.path.strip("/")
    return slug(path.replace("/", "-")) if path else "home"


def autoscroll(page):
    """Trigger lazy-loaded content, then return to top."""
    page.evaluate("""async () => {
        await new Promise(res => {
            let y = 0;
            const step = () => {
                window.scrollTo(0, y);
                y += window.innerHeight * 0.8;
                if (y < document.documentElement.scrollHeight) setTimeout(step, 90);
                else { window.scrollTo(0, 0); setTimeout(res, 350); }
            };
            step();
        });
    }""")


def freeze(page):
    """Stop animations/carousels so screenshots are deterministic."""
    page.add_style_tag(content="""
        *, *::before, *::after {
            animation-play-state: paused !important;
            animation-duration: 0s !important;
            transition-duration: 0s !important;
            scroll-behavior: auto !important;
        }
    """)


def capture_page(pw_page, url, out_dir, do_mobile=True):
    screens = out_dir / "screens"
    screens.mkdir(parents=True, exist_ok=True)
    ps = page_slug(url)

    pw_page.set_viewport_size(DESKTOP)
    pw_page.goto(url, wait_until="networkidle", timeout=60000)
    autoscroll(pw_page)
    freeze(pw_page)
    pw_page.wait_for_timeout(600)

    data = pw_page.evaluate(PAGE_JS)
    data["page_slug"] = ps
    data["requested_url"] = url

    full_path = screens / f"{ps}__full.png"
    pw_page.screenshot(path=str(full_path), full_page=True)
    data["full_screenshot"] = str(full_path.relative_to(out_dir))

    for s in data["sections"]:
        name = f"{ps}__{s['index']:02d}-{slug(s['label'])}"
        p = screens / f"{name}.png"
        box = s["box"]
        clip = {
            "x": max(0, box["x"]), "y": max(0, box["y"]),
            "width": max(8, box["w"]), "height": max(8, min(box["h"], 4000)),
        }
        try:
            pw_page.screenshot(path=str(p), clip=clip, full_page=True)
            s["screenshot"] = str(p.relative_to(out_dir))
            s["screenshot_size"] = {"w": clip["width"], "h": clip["height"]}
        except Exception as e:
            s["screenshot"] = None
            s["screenshot_error"] = str(e)

    if do_mobile:
        try:
            pw_page.set_viewport_size(MOBILE)
            pw_page.goto(url, wait_until="networkidle", timeout=60000)
            autoscroll(pw_page)
            freeze(pw_page)
            pw_page.wait_for_timeout(500)
            mp = screens / f"{ps}__mobile.png"
            pw_page.screenshot(path=str(mp), full_page=True)
            data["mobile_screenshot"] = str(mp.relative_to(out_dir))
            data["mobile"] = pw_page.evaluate("""() => ({
                horizontal_scroll: document.documentElement.scrollWidth > window.innerWidth + 2,
                scroll_width: document.documentElement.scrollWidth,
                viewport_width: window.innerWidth,
                smallest_font_px: Math.min(...Array.from(document.querySelectorAll('p,li,span,a'))
                    .slice(0,240).map(e => parseFloat(getComputedStyle(e).fontSize) || 16)),
                nav_visible: !!document.querySelector('nav, header')
            })""")
        except Exception as e:
            data["mobile_error"] = str(e)

    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", action="append", required=True, help="page URL (repeatable)")
    ap.add_argument("--out", default="./audit")
    ap.add_argument("--crawl", type=int, default=0,
                    help="also follow up to N internal links from the first URL")
    ap.add_argument("--no-mobile", action="store_true")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    urls = list(dict.fromkeys(args.url))
    result = {"pages": [], "errors": []}

    exe = os.environ.get("CHROMIUM_PATH", "/opt/pw-browsers/chromium")
    with sync_playwright() as pw:
        launch = {"args": ["--disable-dev-shm-usage", "--font-render-hinting=none"]}
        if os.path.exists(exe):
            launch["executable_path"] = exe
        browser = pw.chromium.launch(**launch)
        ctx = browser.new_context(
            viewport=DESKTOP, device_scale_factor=2,
            user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
            ignore_https_errors=True,
        )
        page = ctx.new_page()

        if args.crawl:
            try:
                page.goto(urls[0], wait_until="domcontentloaded", timeout=60000)
                host = urlparse(urls[0]).hostname
                hrefs = page.eval_on_selector_all(
                    "a[href]", "els => els.map(e => e.href)")
                for h in hrefs:
                    if len(urls) >= args.crawl:
                        break
                    try:
                        u = urljoin(urls[0], h).split("#")[0]
                        if urlparse(u).hostname == host and u not in urls and not re.search(
                                r"\.(pdf|jpg|jpeg|png|zip|docx?|xlsx?|mp4)$", u, re.I):
                            urls.append(u)
                    except Exception:
                        pass
            except Exception as e:
                result["errors"].append({"stage": "crawl", "error": str(e)})

        for u in urls:
            try:
                print(f"  capturing {u}", file=sys.stderr)
                result["pages"].append(capture_page(page, u, out_dir, do_mobile=not args.no_mobile))
            except Exception as e:
                result["errors"].append({"url": u, "error": str(e)})
                print(f"  ! failed {u}: {e}", file=sys.stderr)

        browser.close()

    dest = out_dir / "page-data.json"
    dest.write_text(json.dumps(result, indent=2))

    n_sec = sum(len(p.get("sections", [])) for p in result["pages"])
    print(json.dumps({
        "out": str(out_dir),
        "page_data": str(dest),
        "pages": len(result["pages"]),
        "sections": n_sec,
        "errors": result["errors"],
    }, indent=2))


if __name__ == "__main__":
    main()
