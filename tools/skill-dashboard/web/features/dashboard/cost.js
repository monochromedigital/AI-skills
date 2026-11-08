// The cost section: what the token usage would cost at API list prices, for
// one month or all time. Numbers come from cost.py on the Mac; this file only
// lays them out. The page owns which period is shown.

import { COPY, fill } from "../../content.js";
import { DailyBars, RankedBars } from "../../charts.js";
import { Dropdown } from "../../controls.js";
import { compact, day, decimal, full, localDay, money, month, number, percent, relative } from "../../format.js";
import { EmptyState, h, ListRow, Panel, SectionHead, Text } from "../../ui.js";

const usd = (report) => (value) => money(value, report.cost.currency);
const periodName = (p) => (p.kind === "all" ? COPY.cost.head.all : month(p.id));

/** The period to show: the one asked for, else the newest month. */
export const costPeriod = (report, id) => report.cost.periods.find((p) => p.id === id) ?? report.cost.periods[0];

function planLine(report, p) {
  const plan = report.cost.plan;
  if (!plan?.monthlyFee || !p.cost) return null;
  const fmt = usd(report);
  const months = p.kind === "all" ? p.series.length : 1;
  const paid = plan.monthlyFee * months;
  return fill(p.kind === "all" ? COPY.cost.head.planAll : COPY.cost.head.planMonth,
    { fee: fmt(plan.monthlyFee), paid: fmt(paid), months: number(months), ratio: decimal(p.cost / paid), period: periodName(p) });
}

function CostHead(report, p, onPeriod) {
  const c = report.cost;
  const fmt = usd(report);
  return SectionHead({
    title: COPY.cost.head.title,
    lines: [fill(COPY.cost.head.summary, { cost: fmt(p.cost), replies: number(p.replies), sessions: number(p.sessionCount) }),
      planLine(report, p)],
    notes: [fill(COPY.cost.note, { asOf: day(c.asOf) }),
      c.leftOut ? fill(COPY.cost.leftOut, { label: c.leftOut.label, paths: c.leftOut.paths.join(", ") }) : null],
    actions: Dropdown({ label: COPY.cost.head.period, prefix: COPY.cost.head.period, value: p.id, onChange: onPeriod,
      options: c.periods.map((x) => ({ value: x.id, label: periodName(x), count: fmt(x.cost) })) }),
  });
}

function SeriesPanel(report, p) {
  const fmt = usd(report);
  const label = p.kind === "all" ? (d) => month(d.date, "short") : (d) => day(localDay(d.date));
  const title = p.kind === "all" ? COPY.cost.series.month : COPY.cost.series.day;
  return Panel({
    title, className: "panel--wide", caption: fill(COPY.cost.series.caption, { period: periodName(p) }),
    body: p.cost
      ? DailyBars({ data: p.series, valueOf: (d) => d.cost, xLabelFor: label, ariaLabel: title, tickFormat: fmt,
        tooltipFor: (d) => fill(COPY.cost.series.tooltip, { date: label(d), cost: fmt(d.cost) }) })
      : EmptyState(COPY.cost.series.empty),
  });
}

function ProjectsPanel(report, p, onPick) {
  const fmt = usd(report);
  const items = p.projects.slice(0, report.ui.costProjects).map((x) => ({
    id: x.path, label: x.name, value: x.cost, valueText: fmt(x.cost),
    tooltip: [x.name, fill(COPY.cost.projects.tooltip, { cost: fmt(x.cost), tokens: compact(x.tokens), sessions: number(x.sessions) })],
  }));
  return Panel({
    title: COPY.cost.projects.title, caption: fill(COPY.cost.projects.caption, { period: periodName(p) }),
    body: items.length ? RankedBars({ items, onSelect: (item) => onPick(item.id) }) : EmptyState(COPY.cost.projects.empty),
  });
}

function SessionsPanel(report, p) {
  const fmt = usd(report);
  const rows = p.sessions.map((s) => ListRow({
    title: s.title ?? (s.cloud ? COPY.cost.sessions.cloud : COPY.cost.sessions.untitled),
    meta: fill(COPY.cost.sessions.meta, { project: s.project ?? COPY.table.never, replies: number(s.replies), tokens: compact(s.tokens) }),
    trail: h("span", { class: "money", title: full(s.lastUsed) }, fmt(s.cost)),
  }));
  return Panel({
    title: COPY.cost.sessions.title, caption: fill(COPY.cost.sessions.caption, { period: periodName(p), count: rows.length }),
    body: rows.length ? h("ul", { class: ["list", "list--scroll"] }, rows) : EmptyState(COPY.cost.sessions.empty),
  });
}

function KindsPanel(report, p) {
  const fmt = usd(report);
  const total = Object.values(p.byKind).reduce((a, b) => a + b, 0) || 1;
  const name = (kind) => COPY.cost.kinds.labels[kind] ?? kind;
  const items = Object.entries(p.byKind).sort((a, b) => b[1] - a[1]).map(([kind, value]) => ({
    id: kind, label: name(kind), value, valueText: fmt(value),
    tooltip: [name(kind), fill(COPY.cost.kinds.tooltip, { cost: fmt(value), share: percent(value / total) })],
  }));
  const unpriced = Object.entries(report.cost.unpriced);
  return Panel({
    title: COPY.cost.kinds.title, caption: fill(COPY.cost.kinds.caption, { period: periodName(p) }),
    body: [RankedBars({ items }),
      Text({ text: COPY.cost.kinds.explain, tone: "muted", size: "xs", as: "p" }),
      unpriced.length ? Text({ tone: "muted", size: "xs", as: "p", text: fill(COPY.cost.unpriced, {
        count: number(unpriced.reduce((a, [, n]) => a + n, 0)), models: unpriced.map(([m]) => m).join(", ") }) }) : null],
  });
}

/** Every cloud environment that has ever reported: its cost in the period and when it last reported. */
function EnvironmentsPanel(report, p) {
  const fmt = usd(report);
  const t = COPY.cost.environments;
  const inPeriod = new Map(p.environments.map((e) => [e.name, e]));
  const everyone = report.cost.periods.find((x) => x.kind === "all")?.environments ?? [];
  const rows = everyone.map((e) => ({ e, here: inPeriod.get(e.name) })).sort((a, b) => (b.here?.cost ?? 0) - (a.here?.cost ?? 0))
    .map(({ e, here }) => ListRow({
      title: e.named ? e.name : t.unnamed,
      meta: fill(here?.sessions === 1 ? t.metaOne : t.meta, { sessions: number(here?.sessions ?? 0), when: relative(e.lastUsed, COPY.time) }),
      trail: h("span", { class: "money", title: full(e.lastUsed) }, fmt(here?.cost ?? 0)),
    }));
  return Panel({
    title: t.title, caption: fill(t.caption, { period: periodName(p) }),
    body: rows.length ? h("ul", { class: ["list", "list--scroll"] }, rows) : EmptyState(t.empty),
  });
}

/** The heading with its period picker, then both rows of panels for that period. */
export function CostSection(report, periodId, { onPick, onPeriod }) {
  const p = report.cost?.periods?.length ? costPeriod(report, periodId) : null;
  if (!p) return [];
  return [
    CostHead(report, p, onPeriod),
    h("div", { class: "band" }, SeriesPanel(report, p), ProjectsPanel(report, p, onPick)),
    h("div", { class: "band" }, SessionsPanel(report, p), KindsPanel(report, p), EnvironmentsPanel(report, p)),
  ];
}
