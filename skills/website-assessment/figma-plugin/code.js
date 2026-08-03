/* Crackwits Website Assessment - Figma plugin (main thread)
 *
 * Receives an audit bundle from the plugin UI and builds the assessment
 * slides as real Figma frames: eyebrow + title, a findings panel with
 * numbered cards and category tags, a device-framed screenshot with markers
 * pinned to the exact element, and a summary slide with category counts.
 *
 * Layout constants mirror assets/brand.json so PPTX and Figma output match.
 */

figma.showUI(__html__, { width: 460, height: 620, themeColors: true });

// ---------------------------------------------------------------- constants
const SLIDE_PT_W = 960; // PPTX slide width in points - used to convert type sizes

const DEFAULT_BRAND = {
  colors: {
    background: '#312F31', panel: '#FFFFFF', card: '#F8F7F8',
    eyebrow: '#1E8FD9', title: '#FFFFFF', body: '#312F31',
    body_muted: '#636163', marker: '#866FBC', marker_text: '#FFFFFF',
    tag_text: '#FFFFFF', footer: '#8A888A'
  },
  categories: {
    'Copy / Content': { color: '#1E8FD9', summary_order: 1 },
    'UX Design':      { color: '#DF6630', summary_order: 2 },
    'UI Design':      { color: '#5C8B63', summary_order: 3 },
    'Development':    { color: '#866FBC', summary_order: 4 },
    'SEO':            { color: '#D7586C', summary_order: 5 },
    'Accessibility':  { color: '#7D797E', summary_order: 6 },
    'CRO':            { color: '#2E8F86', summary_order: 7 }
  },
  severity: {
    Critical: { color: '#D7586C', weight: 3 },
    Moderate: { color: '#DF6630', weight: 2 },
    Minor:    { color: '#7D797E', weight: 1 }
  },
  type: {
    eyebrow: { size_pt: 11, weight: 'Regular' },
    title: { size_pt: 24, weight: 'Light' },
    finding_body: { size_pt: 8.5, weight: 'Regular' },
    tag: { size_pt: 6, weight: 'Medium' },
    marker: { size_pt: 5.5, weight: 'Medium' },
    stat_number: { size_pt: 20, weight: 'Light' },
    footer: { size_pt: 6.5, weight: 'Regular' }
  },
  layout: {
    eyebrow: { x: 0.058, y: 0.100 },
    title: { x: 0.058, y: 0.135 },
    panel: { x: 0.056, y: 0.244, w: 0.344, h: 0.670 },
    panel_radius: 0.018, panel_pad: 0.014,
    card_radius: 0.008, card_gap: 0.006,
    card_pad_x: 0.016, card_pad_y: 0.010,
    device: { x: 0.360, y: 0.100, w: 0.585, h: 0.800 },
    marker_d: 0.0125, tag_h_in: 0.145,
    footer_y: 0.955, footer_l_x: 0.012, footer_r_x: 0.988
  }
};

const FONT_FAMILY_PRIMARY = 'Urbanist';
const FONT_FAMILY_FALLBACK = 'Inter';
let FONT = FONT_FAMILY_PRIMARY;

// ---------------------------------------------------------------- helpers
function hexToRgb(hex) {
  const h = String(hex).replace('#', '');
  return {
    r: parseInt(h.slice(0, 2), 16) / 255,
    g: parseInt(h.slice(2, 4), 16) / 255,
    b: parseInt(h.slice(4, 6), 16) / 255
  };
}
const solid = (hex, opacity) => [{ type: 'SOLID', color: hexToRgb(hex), opacity: opacity === undefined ? 1 : opacity }];

async function loadFonts() {
  const styles = ['Light', 'Regular', 'Medium', 'SemiBold', 'Bold'];
  try {
    for (const style of styles) {
      await figma.loadFontAsync({ family: FONT_FAMILY_PRIMARY, style });
    }
    FONT = FONT_FAMILY_PRIMARY;
    return { font: FONT, warning: null };
  } catch (e) {
    FONT = FONT_FAMILY_FALLBACK;
    for (const style of styles) {
      try { await figma.loadFontAsync({ family: FONT_FAMILY_FALLBACK, style }); } catch (e2) { /* ignore */ }
    }
    return {
      font: FONT,
      warning: 'Urbanist is not available in this file, so the slides were built in Inter. ' +
               'Install Urbanist (Google Fonts) and re-run to match the template exactly.'
    };
  }
}

// ---------------------------------------------------------------- builder
class DeckBuilder {
  constructor(brand, W, H) {
    this.b = brand;
    this.W = W;
    this.H = H;
    this.px = (f) => Math.round(this.W * f);
    this.py = (f) => Math.round(this.H * f);
    // point sizes in the PPTX are relative to a 960pt-wide slide
    this.pt = (p) => Math.max(4, Math.round((p / SLIDE_PT_W) * this.W));
    this.inch = (i) => Math.round((i / 13.3333) * this.W);
  }

  slide(name) {
    const f = figma.createFrame();
    f.name = name;
    f.resize(this.W, this.H);
    f.fills = solid(this.b.colors.background);
    f.clipsContent = true;
    return f;
  }

  text(parent, opts) {
    const t = figma.createText();
    t.fontName = { family: FONT, style: opts.style || 'Regular' };
    t.characters = String(opts.text == null ? '' : opts.text);
    t.fontSize = opts.size;
    t.fills = solid(opts.color);
    t.x = opts.x;
    t.y = opts.y;
    if (opts.width) {
      t.textAutoResize = 'HEIGHT';
      t.resize(opts.width, t.height);
    } else {
      t.textAutoResize = 'WIDTH_AND_HEIGHT';
    }
    if (opts.lineHeight) t.lineHeight = { value: opts.lineHeight, unit: 'PERCENT' };
    if (opts.align) t.textAlignHorizontal = opts.align;
    if (opts.name) t.name = opts.name;
    parent.appendChild(t);
    return t;
  }

  /** Text made of runs: [{text, style, color}] rendered into one node. */
  richText(parent, runs, opts) {
    const t = figma.createText();
    t.fontName = { family: FONT, style: 'Regular' };
    t.characters = runs.map(r => r.text).join('');
    t.fontSize = opts.size;
    t.x = opts.x;
    t.y = opts.y;
    t.textAutoResize = 'HEIGHT';
    t.resize(opts.width, t.height);
    t.lineHeight = { value: opts.lineHeight || 142, unit: 'PERCENT' };
    t.fills = solid(opts.color);
    let i = 0;
    for (const r of runs) {
      const j = i + r.text.length;
      if (r.text.length) {
        t.setRangeFontName(i, j, { family: FONT, style: r.style || 'Regular' });
        t.setRangeFills(i, j, solid(r.color || opts.color));
      }
      i = j;
    }
    if (opts.name) t.name = opts.name;
    parent.appendChild(t);
    return t;
  }

  rect(parent, x, y, w, h, fill, radius, name) {
    const r = figma.createRectangle();
    r.x = x; r.y = y;
    r.resize(Math.max(1, w), Math.max(1, h));
    r.fills = solid(fill);
    if (radius) r.cornerRadius = radius;
    if (name) r.name = name;
    parent.appendChild(r);
    return r;
  }

  /** Auto-layout pill with centred label; returns the node so callers can read width. */
  pill(parent, x, y, label, color) {
    const h = this.inch(this.b.layout.tag_h_in);
    const f = figma.createFrame();
    f.name = 'tag/' + label;
    f.layoutMode = 'HORIZONTAL';
    f.primaryAxisSizingMode = 'AUTO';
    f.counterAxisSizingMode = 'FIXED';
    f.primaryAxisAlignItems = 'CENTER';
    f.counterAxisAlignItems = 'CENTER';
    f.paddingLeft = f.paddingRight = Math.round(h * 0.42);
    f.resize(10, h);
    f.cornerRadius = Math.round(h * 0.30);
    f.fills = solid(color);
    f.clipsContent = false;
    parent.appendChild(f);
    const t = figma.createText();
    t.fontName = { family: FONT, style: 'Medium' };
    t.characters = label;
    t.fontSize = this.pt(this.b.type.tag.size_pt);
    t.fills = solid(this.b.colors.tag_text);
    t.textAutoResize = 'WIDTH_AND_HEIGHT';
    f.appendChild(t);
    f.x = x; f.y = y;
    return f;
  }

  marker(parent, cx, cy, n) {
    const d = this.px(this.b.layout.marker_d);
    const g = figma.createFrame();
    g.name = 'marker/' + String(n).padStart(2, '0');
    g.resize(d, d);
    g.x = Math.round(cx - d / 2);
    g.y = Math.round(cy - d / 2);
    g.cornerRadius = d / 2;
    g.fills = solid(this.b.colors.marker);
    g.strokes = solid('#FFFFFF');
    g.strokeWeight = Math.max(1, Math.round(d * 0.075));
    g.clipsContent = false;
    g.layoutMode = 'HORIZONTAL';
    g.primaryAxisAlignItems = 'CENTER';
    g.counterAxisAlignItems = 'CENTER';
    g.primaryAxisSizingMode = 'FIXED';
    g.counterAxisSizingMode = 'FIXED';
    parent.appendChild(g);
    const t = figma.createText();
    t.fontName = { family: FONT, style: 'Medium' };
    t.characters = String(n).padStart(2, '0');
    t.fontSize = this.pt(this.b.type.marker.size_pt);
    t.fills = solid(this.b.colors.marker_text);
    t.textAutoResize = 'WIDTH_AND_HEIGHT';
    g.appendChild(t);
    return g;
  }

  heading(slide, eyebrow, title) {
    const L = this.b.layout, T = this.b.type, C = this.b.colors;
    this.text(slide, { text: eyebrow, x: this.px(L.eyebrow.x), y: this.py(L.eyebrow.y),
      size: this.pt(T.eyebrow.size_pt), color: C.eyebrow, style: 'Regular', name: 'eyebrow' });
    this.text(slide, { text: title, x: this.px(L.title.x), y: this.py(L.title.y),
      size: this.pt(T.title.size_pt), color: C.title, style: 'Light', name: 'title' });
  }

  footer(slide, meta) {
    const L = this.b.layout, T = this.b.type, C = this.b.colors;
    const year = meta.year || new Date().getFullYear();
    this.text(slide, { text: 'Crackwits © ' + year + '. All Rights Reserved',
      x: this.px(L.footer_l_x), y: this.py(L.footer_y),
      size: this.pt(T.footer.size_pt), color: C.footer });
    const right = this.text(slide, { text: meta.footer_right || 'Website UX/UI Assessment',
      x: 0, y: this.py(L.footer_y), size: this.pt(T.footer.size_pt), color: C.footer });
    right.x = this.px(L.footer_r_x) - right.width;
  }

  /**
   * Findings panel. Cards use auto layout so text drives height.
   * Appends cards until the panel would overflow the slide, then stops and
   * reports how many it placed so the caller can spill the rest onto a
   * continuation slide.
   */
  panel(slide, findings, startN, showSeverity, showFix, showPrinciple) {
    const L = this.b.layout, T = this.b.type, C = this.b.colors;
    const px = this.px(L.panel.x), py = this.py(L.panel.y);
    const pw = this.px(L.panel.w), ph = this.py(L.panel.h);

    const panel = figma.createFrame();
    panel.name = 'findings-panel';
    panel.x = px; panel.y = py;
    panel.resize(pw, ph);
    panel.cornerRadius = this.px(L.panel_radius);
    panel.fills = solid(C.panel);
    panel.clipsContent = true;
    panel.layoutMode = 'VERTICAL';
    // grow while we measure, pinned back to FIXED once we know what fits
    panel.primaryAxisSizingMode = 'AUTO';
    panel.counterAxisSizingMode = 'FIXED';
    panel.paddingLeft = panel.paddingRight = panel.paddingTop = panel.paddingBottom = this.px(L.panel_pad);
    panel.itemSpacing = this.py(L.card_gap);
    slide.appendChild(panel);

    const markerD = this.px(L.marker_d);
    const cardPadX = this.px(L.card_pad_x), cardPadY = this.py(L.card_pad_y);
    const innerW = pw - this.px(L.panel_pad) * 2;
    const textW = innerW - cardPadX * 2 - markerD - this.px(0.008);
    const bodySize = this.pt(T.finding_body.size_pt);

    let placed = 0;
    for (let i = 0; i < findings.length; i++) {
      const f = findings[i];
      const n = startN + i;

      const card = figma.createFrame();
      card.name = 'finding/' + String(n).padStart(2, '0');
      card.layoutMode = 'HORIZONTAL';
      card.primaryAxisSizingMode = 'FIXED';
      card.counterAxisSizingMode = 'AUTO';
      card.counterAxisAlignItems = 'MIN';
      card.paddingLeft = card.paddingRight = cardPadX;
      card.paddingTop = card.paddingBottom = cardPadY;
      card.itemSpacing = this.px(0.008);
      card.cornerRadius = this.px(L.card_radius);
      card.fills = solid(C.card);
      card.resize(innerW, 10);
      card.layoutAlign = 'STRETCH';
      panel.appendChild(card);

      // left gutter: the number chip
      const chip = figma.createFrame();
      chip.name = 'chip';
      chip.resize(markerD, markerD);
      chip.cornerRadius = markerD / 2;
      chip.fills = solid(C.marker);
      chip.layoutMode = 'HORIZONTAL';
      chip.primaryAxisAlignItems = 'CENTER';
      chip.counterAxisAlignItems = 'CENTER';
      chip.primaryAxisSizingMode = 'FIXED';
      chip.counterAxisSizingMode = 'FIXED';
      card.appendChild(chip);
      const chipT = figma.createText();
      chipT.fontName = { family: FONT, style: 'Medium' };
      chipT.characters = String(n).padStart(2, '0');
      chipT.fontSize = this.pt(T.marker.size_pt);
      chipT.fills = solid(C.marker_text);
      chipT.textAutoResize = 'WIDTH_AND_HEIGHT';
      chip.appendChild(chipT);

      // right column: tags + copy
      const col = figma.createFrame();
      col.name = 'content';
      col.layoutMode = 'VERTICAL';
      col.primaryAxisSizingMode = 'AUTO';
      col.counterAxisSizingMode = 'FIXED';
      col.itemSpacing = Math.round(bodySize * 0.55);
      col.fills = [];
      col.resize(textW, 10);
      card.appendChild(col);

      // tag row wraps automatically
      const tagRow = figma.createFrame();
      tagRow.name = 'tags';
      tagRow.layoutMode = 'HORIZONTAL';
      tagRow.layoutWrap = 'WRAP';
      tagRow.primaryAxisSizingMode = 'FIXED';
      tagRow.counterAxisSizingMode = 'AUTO';
      tagRow.itemSpacing = this.px(0.004);
      tagRow.counterAxisSpacing = this.px(0.003);
      tagRow.fills = [];
      tagRow.resize(textW, 10);
      tagRow.layoutAlign = 'STRETCH';
      col.appendChild(tagRow);

      (f.categories || []).forEach(cat => {
        const spec = this.b.categories[cat] || { color: C.body_muted };
        this.pill(tagRow, 0, 0, cat, spec.color);
      });
      if (showSeverity && f.severity && this.b.severity[f.severity]) {
        this.pill(tagRow, 0, 0, String(f.severity).toUpperCase(), this.b.severity[f.severity].color);
      }

      const addPara = (runs) => {
        const t = this.richText(col, runs, { size: bodySize, color: C.body, width: textW });
        t.layoutAlign = 'STRETCH';
        return t;
      };

      if (f.observation) addPara([{ text: f.observation }]);
      if (f.detail) addPara([{ text: f.detail }]);
      if (f.fix && showFix) addPara([{ text: 'Fix: ', style: 'SemiBold' }, { text: f.fix }]);
      if (f.principle && showPrinciple) {
        addPara([{ text: 'Principle: ', style: 'SemiBold' },
                 { text: f.principle, color: C.body_muted }]);
      }
      if (f.scope) addPara([{ text: f.scope, style: 'SemiBold' }]);

      // Figma lays out synchronously, so the height is already correct here.
      if (placed > 0 && panel.height > ph) {
        card.remove();
        break;
      }
      placed++;
    }

    panel.primaryAxisSizingMode = 'FIXED';
    panel.resize(pw, ph);
    return { panel: panel, placed: Math.max(1, placed) };
  }

  summary(meta, counts, narrative, imageBytes, imageDims) {
    const L = this.b.layout, T = this.b.type, C = this.b.colors;
    const slide = this.slide('Summary');
    this.heading(slide, 'General', 'Summary');
    this.footer(slide, meta);

    if (imageBytes) this.placeFitted(slide, imageBytes, imageDims, 'summary-screenshot');

    const px = this.px(L.panel.x), py = this.py(L.panel.y);
    const pw = this.px(L.panel.w), ph = this.py(L.panel.h);
    const panel = this.rect(slide, px, py, pw, ph, C.panel, this.px(L.panel_radius), 'summary-panel');

    const pad = this.px(L.panel_pad) + this.px(0.006);
    const innerX = px + pad, innerW = pw - pad * 2;
    const bodySize = this.pt(T.finding_body.size_pt);

    let y = py + pad;
    (narrative || []).forEach(para => {
      const t = this.richText(slide, [{ text: para }],
        { size: bodySize, color: C.body, x: innerX, y, width: innerW, lineHeight: 148 });
      y += t.height + Math.round(bodySize * 0.9);
    });

    const ordered = Object.keys(counts)
      .filter(k => counts[k])
      .sort((a, b) => ((this.b.categories[a] || {}).summary_order || 99) -
                      ((this.b.categories[b] || {}).summary_order || 99));

    const cols = 2, gap = this.px(0.010);
    const rowsN = Math.max(1, Math.ceil(ordered.length / cols));
    const cw = Math.floor((innerW - gap) / cols);
    const gridTop = y + this.py(0.016);
    const gridBottom = py + ph - pad;
    const chh = Math.min(this.py(0.078),
      Math.max(this.py(0.048), Math.floor((gridBottom - gridTop - gap * (rowsN - 1)) / rowsN)));
    const gridH = rowsN * chh + gap * (rowsN - 1);
    const gy = Math.max(gridTop, gridBottom - gridH);

    ordered.forEach((cat, i) => {
      const r = Math.floor(i / cols), c = i % cols;
      const x = innerX + c * (cw + gap);
      const cy = gy + r * (chh + gap);
      this.rect(slide, x, cy, cw, chh, C.card, this.px(L.card_radius), 'stat/' + cat);
      const pillH = this.inch(L.tag_h_in);
      const spec = this.b.categories[cat] || { color: C.body_muted };
      this.pill(slide, x + this.px(0.010), cy + Math.round((chh - pillH) / 2), cat, spec.color);
      const num = this.text(slide, { text: String(counts[cat]),
        x: 0, y: 0, size: this.pt(T.stat_number.size_pt), color: C.body, style: 'Light' });
      num.x = x + cw - this.px(0.014) - num.width;
      num.y = cy + Math.round((chh - num.height) / 2);
    });

    return slide;
  }

  placeFitted(slide, bytes, dims, name) {
    const L = this.b.layout;
    const boxX = this.px(L.device.x), boxY = this.py(L.device.y);
    const boxW = this.px(L.device.w), boxH = this.py(L.device.h);
    const img = figma.createImage(bytes);
    const node = figma.createRectangle();
    node.name = name || 'screenshot';
    node.fills = [{ type: 'IMAGE', imageHash: img.hash, scaleMode: 'FILL' }];
    let w = boxW, h = boxH;
    if (dims && dims.w && dims.h) {
      const s = Math.min(boxW / dims.w, boxH / dims.h);
      w = Math.round(dims.w * s); h = Math.round(dims.h * s);
      node.fills = [{ type: 'IMAGE', imageHash: img.hash, scaleMode: 'FIT' }];
    }
    node.x = boxX + Math.round((boxW - w) / 2);
    node.y = boxY + Math.round((boxH - h) / 2);
    node.resize(w, h);
    slide.appendChild(node);
    return { node, rect: { x: node.x, y: node.y, w, h } };
  }

  cover(meta) {
    const C = this.b.colors, T = this.b.type;
    const slide = this.slide('Cover');
    this.text(slide, { text: meta.deck_kicker || 'Website UX/UI Assessment',
      x: this.px(0.058), y: this.py(0.36), size: this.pt(T.eyebrow.size_pt), color: C.eyebrow });
    this.text(slide, { text: meta.client || 'Client', x: this.px(0.058), y: this.py(0.42),
      size: this.pt(54), color: C.title, style: 'Light', width: this.px(0.80) });
    this.text(slide, { text: (meta.url || '') + '    ·    ' + (meta.audited_on || ''),
      x: this.px(0.058), y: this.py(0.60), size: this.pt(12), color: C.footer });
    this.footer(slide, meta);
    return slide;
  }
}

// ---------------------------------------------------------------- message loop
figma.ui.onmessage = async (msg) => {
  if (msg.type === 'cancel') { figma.closePlugin(); return; }
  if (msg.type !== 'build') return;

  try {
    const fontInfo = await loadFonts();
    if (fontInfo.warning) figma.ui.postMessage({ type: 'warn', text: fontInfo.warning });

    const data = msg.data;
    const brand = Object.assign({}, DEFAULT_BRAND, msg.brand || {});
    if (msg.brand) {
      // shallow-merge the nested groups so a partial brand file still works
      ['colors', 'categories', 'severity', 'type', 'layout'].forEach(k => {
        brand[k] = Object.assign({}, DEFAULT_BRAND[k], (msg.brand[k] || {}));
      });
    }

    const W = msg.frameW || 3840;
    const H = msg.frameH || 2160;
    const B = new DeckBuilder(brand, W, H);
    const meta = data.meta || {};
    const showSeverity = meta.show_severity !== false;
    const showFix = meta.show_fix !== false;
    const showPrinciple = meta.show_principle !== false;

    const images = msg.images || {};   // filename -> {bytes: Uint8Array, w, h}
    const made = [];
    const counts = {};

    if (meta.cover !== false) made.push(B.cover(meta));

    for (const sl of (data.slides || [])) {
      const findings = sl.findings || [];
      findings.forEach(f => (f.categories || []).forEach(c => { counts[c] = (counts[c] || 0) + 1; }));

      const key = (sl.framed || sl.screenshot || '').split('/').pop();
      const img = images[key];
      const sr = sl.screen_rect || { x: 0, y: 0, w: 1, h: 1 };

      let cursor = 0, part = 0;
      do {
        const slide = B.slide((sl.page || '') + ' / ' + (sl.section || '') +
                              (part ? ' (cont.)' : ''));
        B.heading(slide, sl.page || '',
                  (sl.section || '') + (part ? ' (cont.)' : ''));
        B.footer(slide, meta);

        let rect = null;
        if (img) {
          rect = B.placeFitted(slide, img.bytes, { w: img.w, h: img.h },
            'screenshot/' + (sl.section || '')).rect;
        }

        const chunk = findings.slice(cursor);
        const res = B.panel(slide, chunk, cursor + 1, showSeverity, showFix, showPrinciple);

        if (rect) {
          chunk.slice(0, res.placed).forEach((f, i) => {
            if (!f.marker) return;
            const fxr = sr.x + sr.w * Number(f.marker.x != null ? f.marker.x : 0.5);
            const fyr = sr.y + sr.h * Number(f.marker.y != null ? f.marker.y : 0.5);
            B.marker(slide, rect.x + rect.w * fxr, rect.y + rect.h * fyr, cursor + i + 1);
          });
        }

        made.push(slide);
        cursor += res.placed;
        part++;
      } while (cursor < findings.length && part < 12);
    }

    const summ = data.summary || {};
    if (summ.narrative || summ.counts) {
      const hero = (summ.image || '').split('/').pop();
      const himg = images[hero];
      made.push(B.summary(meta, summ.counts || counts, summ.narrative || [],
        himg && himg.bytes, himg && { w: himg.w, h: himg.h }));
    }

    // lay the slides out in a row on the page
    const startX = figma.viewport.center.x - (W / 2);
    const startY = figma.viewport.center.y - (H / 2);
    made.forEach((f, i) => { f.x = startX + i * (W + Math.round(W * 0.05)); f.y = startY; });

    const group = figma.group(made, figma.currentPage);
    group.name = (meta.client || 'Website') + ' — Assessment';

    figma.currentPage.selection = made;
    figma.viewport.scrollAndZoomIntoView(made);

    figma.ui.postMessage({ type: 'done', slides: made.length, font: FONT });
    figma.notify('Built ' + made.length + ' slides in ' + FONT);
  } catch (err) {
    figma.ui.postMessage({ type: 'error', text: String((err && err.message) || err) });
    figma.notify('Build failed: ' + String((err && err.message) || err), { error: true });
  }
};
