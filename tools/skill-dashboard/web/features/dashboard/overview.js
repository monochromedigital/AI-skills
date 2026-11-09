// The Overview's own pieces: the cost tiles at the top, and the heading of the
// skills snapshot with its link to the Skills page.

import { COPY, fill } from "../../content.js";
import { day, decimal, money, month, number, percent } from "../../format.js";
import { Button, SectionHead, StatTile, h } from "../../ui.js";

/** Four tiles that don't follow the period picker: the rolling week, this month, all time, and cloud sessions. */
export function CostKpis(report) {
  const c = report.cost;
  const fmt = (value) => money(value, c.currency);
  const t = COPY.costKpi;
  const days = report.windows.recentDays;
  const delta = c.totals.recent - c.totals.previous;
  const trend = delta > 0 ? t.week.up : delta < 0 ? t.week.down : t.week.flat;
  const monthName = month(c.thisMonth);
  const fee = c.plan?.monthlyFee;
  const cloudAll = c.periods.find((p) => p.kind === "all")?.bySource.cloud ?? 0;
  const cloudMonth = c.periods.find((p) => p.id === c.thisMonth)?.bySource.cloud ?? 0;
  return h("div", { class: "kpis" },
    StatTile({ label: fill(t.week.label, { days }), value: fmt(c.totals.recent), sub: fill(trend, { delta: fmt(Math.abs(delta)), days }) }),
    StatTile({ label: fill(t.month.label, { month: monthName }), value: fmt(c.totals.month),
      sub: fee ? fill(t.month.sub, { ratio: decimal(c.totals.month / fee), fee: fmt(fee) }) : t.month.subNoPlan }),
    StatTile({ label: t.all.label, value: fmt(c.totals.all),
      sub: report.coverage.since ? fill(t.all.sub, { since: day(report.coverage.since) }) : null }),
    StatTile({ label: t.cloud.label, value: fmt(cloudMonth),
      sub: cloudAll ? fill(t.cloud.sub, { share: percent(c.totals.month ? cloudMonth / c.totals.month : 0), month: monthName }) : t.cloud.none }));
}

/** The skills snapshot's heading: a one-line summary, anything waiting, and the way into the Skills page. */
export function SkillsSnapshotHead(report, onManage) {
  const k = report.kpis;
  const s = COPY.snapshot;
  return SectionHead({
    title: s.title,
    lines: [fill(s.summary, { installed: number(k.installed), used: number(k.used), uses: number(k.invocationsRecent), days: report.windows.recentDays })],
    notes: [k.updates ? fill(s.updates, { count: number(k.updates) }) : null,
      k.mcpAttention ? fill(s.mcp, { count: number(k.mcpAttention) }) : null],
    actions: Button({ label: s.manage, icon: "chevron-right", onClick: onManage }),
  });
}
