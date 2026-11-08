// Page: the Overview. Cost first, then a snapshot of the skills with a way
// into the Skills page. The app passes in everything this page reacts to.

import { Coverage } from "../features/dashboard/activity.js";
import { CostSection } from "../features/dashboard/cost.js";
import { CostKpis, SkillsSnapshotHead } from "../features/dashboard/overview.js";
import { CloudGuide } from "../features/dashboard/cloud-guide.js";
import { TopPanel, UsagePanel } from "../features/dashboard/summary.js";
import { COPY } from "../content.js";
import { Drawer } from "../overlays.js";
import { h } from "../ui.js";

export function OverviewPage(report, { costPeriod, costHandlers, onSkill, onManage }) {
  const hasCost = Boolean(report.cost?.periods?.length);
  const onHelp = () => Drawer({ title: COPY.cloudGuide.title, closeLabel: COPY.cloudGuide.close, body: CloudGuide(report) });
  return [
    ...(hasCost ? [CostKpis(report), ...CostSection(report, costPeriod, { ...costHandlers, onHelp })] : []),
    SkillsSnapshotHead(report, onManage),
    h("div", { class: "band" }, UsagePanel(report), TopPanel(report, onSkill)),
    Coverage(report),
  ];
}
