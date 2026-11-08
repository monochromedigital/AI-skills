// Chart organisms, generic: they draw numbers and call back for labels.
// Geometry comes from tokens (--chart-*), colour from classes in app.css.
// Marks follow the dataviz skill: thin bars, a 2px gap, 4px rounded data
// ends anchored to the baseline, recessive grid, hover tooltip by default.

import { tooltip } from "./overlays.js";
import { h, svg, tokenNumber } from "./ui.js";

// Axis steps are 1, 2 or 5 times a power of ten, so tick labels read as round numbers.
const DECIMAL = 10;
const NICE_MULTIPLES = [1, 2, 5, DECIMAL];

function niceStep(max, ticks) {
  const raw = max / Math.max(1, ticks);
  const magnitude = DECIMAL ** Math.floor(Math.log10(raw || 1));
  const multiple = NICE_MULTIPLES.find((m) => raw / magnitude <= m) ?? DECIMAL;
  return Math.max(1, Math.ceil(multiple * magnitude)); // counts are whole numbers
}

function roundedTop(x, y, w, height, radius) {
  const r = Math.min(radius, w / 2, height);
  return `M${x},${y + height}V${y + r}Q${x},${y} ${x + r},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + height}Z`;
}

/** Vertical bars, one per item: [{ value, ... }]. */
export function DailyBars({ data, valueOf, tooltipFor, xLabelFor, ariaLabel }) {
  const root = h("div", { class: "chart", role: "img", "aria-label": ariaLabel });

  function draw() {
    const width = root.clientWidth;
    if (!width) return;
    const t = (name) => tokenNumber(root, name);
    const height = t("--chart-height");
    const [pt, pr, pb, pl] = ["top", "right", "bottom", "left"].map((side) => t(`--chart-pad-${side}`));
    const tickGap = t("--chart-tick-gap");
    const values = data.map(valueOf);
    const step = niceStep(Math.max(1, ...values), t("--chart-ticks"));
    const top = Math.ceil(Math.max(1, ...values) / step) * step;
    const plotW = width - pl - pr;
    const plotH = height - pt - pb;
    const slot = plotW / data.length;
    const barW = Math.max(1, Math.min(t("--chart-bar-max"), slot - t("--chart-bar-gap")));
    const y = (v) => pt + plotH - (v / top) * plotH;
    const chart = svg("svg", { class: "chart__svg", width, height, viewBox: `0 0 ${width} ${height}` });

    for (let v = 0; v <= top; v += step) {
      chart.append(
        svg("line", { class: v === 0 ? "chart__baseline" : "chart__grid", x1: pl, x2: width - pr, y1: y(v), y2: y(v) }),
        svg("text", { class: "chart__tick", x: pl - tickGap, y: y(v), "text-anchor": "end", "dominant-baseline": "middle" }, v),
      );
    }

    const every = Math.ceil(data.length / t("--chart-x-labels"));
    const bars = data.map((item, i) => {
      const x = pl + slot * i;
      const value = values[i];
      const bar = value ? svg("path", { class: "chart__bar", d: roundedTop(x + (slot - barW) / 2, y(value), barW, y(0) - y(value), t("--chart-bar-radius")) }) : null;
      const hit = svg("rect", { class: "chart__hit", x, y: pt, width: slot, height: plotH,
        onMousemove: (e) => { root.classList.add("is-hovering"); bar?.classList.add("is-active"); tooltip.show(tooltipFor(item), e.clientX, e.clientY); },
        onMouseleave: () => { root.classList.remove("is-hovering"); bar?.classList.remove("is-active"); tooltip.hide(); } });
      const label = (data.length - 1 - i) % every === 0
        ? svg("text", { class: "chart__tick", x: x + slot / 2, y: height - pb / 2, "text-anchor": "middle", "dominant-baseline": "middle" }, xLabelFor(item))
        : null;
      return [bar, label, hit];
    });
    // Hit targets go last so they sit above every bar and label.
    chart.append(...bars.flatMap(([bar, label]) => [bar, label].filter(Boolean)), ...bars.map(([, , hit]) => hit));
    root.replaceChildren(chart);
  }

  new ResizeObserver(draw).observe(root);
  return root;
}

/** Horizontal ranked bars: [{ label, value, valueText, tooltip }]. */
export function RankedBars({ items, onSelect }) {
  const max = Math.max(1, ...items.map((item) => item.value));
  return h("ol", { class: "ranked" }, items.map((item) =>
    h("li", {},
      h("button", { type: "button", class: "ranked__row", onClick: () => onSelect?.(item),
        onMousemove: (e) => tooltip.show(item.tooltip, e.clientX, e.clientY), onMouseleave: () => tooltip.hide(),
        onFocus: (e) => { const r = e.currentTarget.getBoundingClientRect(); tooltip.show(item.tooltip, r.right, r.top); },
        onBlur: () => tooltip.hide() },
        h("span", { class: "ranked__label", title: item.label }, item.label),
        h("span", { class: "ranked__track" }, h("span", { class: "ranked__fill", vars: { "--fill": item.value / max } })),
        h("span", { class: "ranked__value" }, item.valueText)))));
}
