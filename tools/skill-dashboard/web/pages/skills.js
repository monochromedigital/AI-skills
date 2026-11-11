// Page: Skills. Everything for managing them: the counts, what needs
// attention, where they're used, and the full table with bulk editing. The app
// builds the table and bulk bar (it redraws them on its own) and passes them in.

import { Coverage, RecentPanel, TrashPanel } from "../features/dashboard/activity.js";
import { McpPanel, UpdatesPanel } from "../features/dashboard/attention.js";
import { ProjectsPanel, RecentlyAddedPanel } from "../features/dashboard/library.js";
import { KpiRow } from "../features/dashboard/summary.js";
import { COPY } from "../content.js";
import { h, Text } from "../ui.js";

export function SkillsPage(report, { table, bulk, onAction, mcpChecking, showProject, openDetail }) {
  return [
    KpiRow(report),
    report.combined ? Text({ text: COPY.page.perMac, tone: "muted", as: "p" })
      : h("div", { class: "band" }, UpdatesPanel(report, onAction), McpPanel(report, onAction, mcpChecking)),
    h("div", { class: "band" }, ProjectsPanel(report, showProject), RecentlyAddedPanel(report, openDetail),
      RecentPanel(report), TrashPanel(report, onAction)),
    table,
    Coverage(report),
    bulk,
  ];
}
