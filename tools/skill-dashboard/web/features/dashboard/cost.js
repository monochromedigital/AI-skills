// The cost section: what the token usage would cost at API list prices, per
// day, per project, per session, and by kind of token. Numbers come from
// cost.py on the Mac; this file only lays them out.

import { COPY, fill } from "../../content.js";
import { DailyBars, RankedBars } from "../../charts.js";
import { compact, day, full, localDay, money, number } from "../../format.js";
import { EmptyState, h, ListRow, Panel, Text } from "../../ui.js";

const usd = (report) => (value) => money(value, report.cost.currency);

export function CostDailyPanel(report) {
  const c = report.cost;
  const fmt = usd(report);
  const label = (d) => day(localDay(d.date));
  const total = c.daily.reduce((sum, d) => sum + d.cost, 0);
  return Panel({
    title: COPY.cost.daily.title, className: "panel--wide",
    caption: fill(COPY.cost.daily.caption, { days: report.windows.chartDays }),
    body: total ? [
      DailyBars({ data: c.daily, valueOf: (d) => d.cost, xLabelFor: label, ariaLabel: COPY.cost.daily.title, tickFormat: fmt,
        tooltipFor: (d) => fill(COPY.cost.daily.tooltip, { date: label(d), cost: fmt(d.cost) }) }),
      Text({ text: fill(COPY.cost.note, { asOf: day(c.asOf) }), tone: "muted", size: "xs", as: "p" }),
      c.leftOut ? Text({ text: fill(COPY.cost.leftOut, { label: c.leftOut.label, paths: c.leftOut.paths.join(", ") }), tone: "muted", size: "xs", as: "p" }) : null,
    ] : EmptyState(COPY.cost.daily.empty),
  });
}

export function CostProjectsPanel(report, onPick) {
  const fmt = usd(report);
  const items = report.cost.projects.slice(0, report.ui.costProjects).map((p) => ({
    id: p.path, label: p.name, value: p.cost, valueText: fmt(p.cost),
    tooltip: [p.name, fill(COPY.cost.projects.tooltip, { cost: fmt(p.cost), tokens: compact(p.tokens), sessions: number(p.sessions) })],
  }));
  return Panel({
    title: COPY.cost.projects.title, caption: COPY.cost.projects.caption,
    body: items.length ? RankedBars({ items, onSelect: (item) => onPick(item.id) }) : EmptyState(COPY.cost.projects.empty),
  });
}

export function CostSessionsPanel(report) {
  const fmt = usd(report);
  const sessions = report.cost.sessions;
  const rows = sessions.map((s) => ListRow({
    title: s.title ?? COPY.cost.sessions.untitled,
    meta: fill(COPY.cost.sessions.meta, { project: s.project ?? COPY.table.never, replies: number(s.replies), tokens: compact(s.tokens) }),
    trail: h("span", { class: "money", title: full(s.lastUsed) }, fmt(s.cost)),
  }));
  return Panel({
    title: COPY.cost.sessions.title, caption: fill(COPY.cost.sessions.caption, { count: sessions.length }),
    body: rows.length ? h("ul", { class: ["list", "list--scroll"] }, rows) : EmptyState(COPY.cost.sessions.empty),
  });
}

export function CostKindsPanel(report) {
  const c = report.cost;
  const fmt = usd(report);
  const total = Object.values(c.byKind).reduce((a, b) => a + b, 0) || 1;
  const share = new Intl.NumberFormat(undefined, { style: "percent", maximumFractionDigits: 0 });
  const items = Object.entries(c.byKind).sort((a, b) => b[1] - a[1]).map(([kind, value]) => ({
    id: kind, label: COPY.cost.kinds.labels[kind] ?? kind, value, valueText: fmt(value),
    tooltip: [COPY.cost.kinds.labels[kind] ?? kind, fill(COPY.cost.kinds.tooltip, { cost: fmt(value), share: share.format(value / total) })],
  }));
  const unpriced = Object.entries(c.unpriced);
  return Panel({
    title: COPY.cost.kinds.title, caption: COPY.cost.kinds.caption,
    body: [RankedBars({ items }),
      Text({ text: COPY.cost.kinds.explain, tone: "muted", size: "xs", as: "p" }),
      unpriced.length ? Text({ tone: "muted", size: "xs", as: "p", text: fill(COPY.cost.unpriced, {
        count: number(unpriced.reduce((a, [, n]) => a + n, 0)), models: unpriced.map(([m]) => m).join(", ") }) }) : null],
  });
}

/** The KPI tile for the top row. */
export function costTile(report) {
  const c = report.cost;
  return {
    label: fill(COPY.cost.kpi.label, { days: report.windows.recentDays }),
    value: money(c.totals.recent, c.currency),
    sub: fill(COPY.cost.kpi.sub, { total: money(c.totals.all, c.currency), since: report.coverage.since ? day(report.coverage.since) : "" }),
  };
}

/** Both rows of cost panels, ready to drop into the page. */
export function CostBands(report, onPick) {
  return [
    h("div", { class: "band" }, CostDailyPanel(report), CostProjectsPanel(report, onPick)),
    h("div", { class: "band" }, CostSessionsPanel(report), CostKindsPanel(report)),
  ];
}
