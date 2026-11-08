// The top of the page: the KPI tiles, uses per day, and the most-used ranking.

import { COPY, fill } from "../../content.js";
import { DailyBars, RankedBars } from "../../charts.js";
import { day, localDay, number } from "../../format.js";
import { EmptyState, h, Panel, StatTile } from "../../ui.js";
import { when } from "./status.js";

export function KpiRow(report) {
  const k = report.kpis;
  const days = report.windows.recentDays;
  const delta = k.invocationsRecent - k.invocationsPrevious;
  const trend = delta > 0 ? COPY.kpi.recent.up : delta < 0 ? COPY.kpi.recent.down : COPY.kpi.recent.flat;
  const mcpSub = report.mcp == null ? COPY.kpi.mcp.subUnknown
    : k.mcpAttention ? fill(COPY.kpi.mcp.subSome, { count: k.mcpAttention }) : COPY.kpi.mcp.subNone;
  return h("div", { class: "kpis" },
    StatTile({ label: COPY.kpi.installed.label, value: number(k.installed),
      sub: fill(COPY.kpi.installed.sub, { used: number(k.used), unused: number(k.unused) }) }),
    StatTile({ label: fill(COPY.kpi.recent.label, { days }), value: number(k.invocationsRecent),
      sub: fill(trend, { delta: number(Math.abs(delta)), days }) }),
    StatTile({ label: COPY.kpi.total.label, value: number(k.invocations),
      sub: report.coverage.since ? fill(COPY.kpi.total.sub, { since: day(report.coverage.since) }) : null }),
    StatTile({ label: COPY.kpi.updates.label, value: number(k.updates), tone: k.updates ? "warning" : null,
      sub: k.updates ? COPY.kpi.updates.subSome : COPY.kpi.updates.subNone }),
    StatTile({ label: COPY.kpi.mcp.label, value: report.mcp ? number(k.mcpTotal) : COPY.table.never, sub: mcpSub }));
}

export function UsagePanel(report) {
  const total = report.daily.reduce((sum, d) => sum + d.count, 0);
  const label = (d) => day(localDay(d.date));
  const tooltipFor = (d) => fill(d.count === 1 ? COPY.usage.tooltipOne : COPY.usage.tooltip, { date: label(d), count: number(d.count) });
  const chart = DailyBars({ data: report.daily, valueOf: (d) => d.count, tooltipFor, xLabelFor: label, ariaLabel: COPY.usage.title });
  const srTable = h("table", { class: "sr-only" }, h("caption", {}, COPY.usage.srTable),
    report.daily.map((d) => h("tr", {}, h("th", {}, label(d)), h("td", {}, d.count))));
  return Panel({
    title: COPY.usage.title, className: "panel--wide",
    caption: fill(COPY.usage.caption, { days: report.windows.chartDays }),
    body: total ? [chart, srTable] : EmptyState(COPY.usage.empty),
  });
}

export function TopPanel(report, onSelect) {
  const items = report.skills.filter((s) => s.uses).slice(0, report.windows.topSkills).map((s) => ({
    id: s.id, label: s.name, value: s.uses, valueText: number(s.uses),
    tooltip: [s.id, fill(COPY.top.tooltip, { count: number(s.uses), when: when(s.lastUsed), projects: number(s.projects) })],
  }));
  return Panel({
    title: COPY.top.title, caption: COPY.top.caption,
    body: items.length ? RankedBars({ items, onSelect }) : EmptyState(COPY.top.empty),
  });
}
