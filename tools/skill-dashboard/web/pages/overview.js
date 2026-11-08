// Page: the Overview. Cost first, then a snapshot of the skills with a way
// into the Skills page. The app passes in everything this page reacts to.

import { Coverage } from "../features/dashboard/activity.js";
import { CostSection } from "../features/dashboard/cost.js";
import { CostKpis, SkillsSnapshotHead } from "../features/dashboard/overview.js";
import { TopPanel, UsagePanel } from "../features/dashboard/summary.js";
import { h } from "../ui.js";

export function OverviewPage(report, { costPeriod, costHandlers, onSkill, onManage }) {
  const hasCost = Boolean(report.cost?.periods?.length);
  return [
    ...(hasCost ? [CostKpis(report), ...CostSection(report, costPeriod, costHandlers)] : []),
    SkillsSnapshotHead(report, onManage),
    h("div", { class: "band" }, UsagePanel(report), TopPanel(report, onSkill)),
    Coverage(report),
  ];
}
