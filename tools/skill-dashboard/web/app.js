// Page layer: owns state, loads the report and lays out the panels. Clicks are
// handled in handlers.js; nothing below this file talks to the server.

import { fetchMachines, fetchReport } from "./api.js";
import { COPY, fill } from "./content.js";
import { Coverage, RecentPanel, TrashPanel } from "./features/dashboard/activity.js";
import { McpPanel, UpdatesPanel } from "./features/dashboard/attention.js";
import { BulkBar, planBulk } from "./features/dashboard/bulk.js";
import { CostBands } from "./features/dashboard/cost.js";
import { SkillDetail } from "./features/dashboard/detail.js";
import { ProjectsPanel, RecentlyAddedPanel } from "./features/dashboard/library.js";
import { Masthead } from "./features/dashboard/masthead.js";
import { skillMenuItems } from "./features/dashboard/menu.js";
import { KpiRow, TopPanel, UsagePanel } from "./features/dashboard/summary.js";
import { rowsBetween, SkillsTable } from "./features/dashboard/table.js";
import { createHandlers } from "./handlers.js";
import { Drawer } from "./overlays.js";
import { h } from "./ui.js";

const app = document.getElementById("app");
const state = {
  report: null, error: null, loading: false, mcpChecking: false, autoChecked: false, drawer: null, machines: [], machine: null,
  table: { search: "", source: "all", status: "all", usage: "all", group: "all", project: "all", groupBy: "group", sort: { key: "uses", dir: "desc" } },
  selection: new Set(), collapsed: new Set(), lastPicked: null,
};
const slots = { table: null, bulk: null };
const act = createHandlers({ state, reload: () => load(), render: () => render() });

async function load({ refresh = false } = {}) {
  state.loading = true;
  render();
  try {
    [state.report, state.machines] = await Promise.all([fetchReport(refresh, state.machine), fetchMachines()]);
    state.error = null;
    const ids = new Set(state.report.skills.map((s) => s.id));
    state.selection = new Set([...state.selection].filter((id) => ids.has(id)));
  } catch (error) {
    state.error = error.message;
  }
  state.loading = false;
  render();
  if (state.report && !state.report.readOnly && !state.report.mcp && !state.autoChecked) {
    state.autoChecked = true;
    act.runAction("mcp-check", { target: null }, { quiet: true });
  }
}

// ── table, selection, detail ──
const tableHandlers = {
  setTable(patch) {
    Object.assign(state.table, patch);
    refreshTable();
  },
  onSelect(ids, on, { shift = false } = {}) {
    const single = ids.length === 1 ? ids[0] : null;
    if (shift && single && state.lastPicked) ids = rowsBetween(slots.table, state.lastPicked, single);
    if (single) state.lastPicked = single;
    for (const id of ids) on ? state.selection.add(id) : state.selection.delete(id);
    refreshTable();
  },
  onToggleGroup(key) {
    state.collapsed.has(key) ? state.collapsed.delete(key) : state.collapsed.add(key);
    refreshTable();
  },
  onDetails: (s) => openDetail(s),
  menuFor: (s) => skillMenuItems(s, { onAction: act.runAction, onDetails: openDetail, onMoveGroup: act.moveToGroup,
    onCopy: act.copySkill, onOpenLink: act.openLink, links: state.report.links, readOnly: state.report.readOnly }),
};

function Table() {
  return SkillsTable(state.report, { table: state.table, selection: state.selection, collapsed: state.collapsed }, tableHandlers);
}

function Bulk() {
  return BulkBar({
    plan: planBulk(state.report.readOnly ? [] : state.report.skills.filter((s) => state.selection.has(s.id))),
    onUpdate: () => act.runBulk("update"), onInstall: () => act.runBulk("install"), onUninstall: () => act.runBulk("uninstall"),
    onMove: (anchor) => act.moveToGroup([...state.selection], anchor, null),
    onClear: () => { state.selection.clear(); refreshTable(); },
  });
}

/** Redraw without losing the table's scroll position or the control that had focus (matched by data-focus-key). */
function keepPlace(redraw) {
  const scroll = slots.table?.querySelector(".table-wrap")?.scrollTop ?? 0;
  const focusKey = app.contains(document.activeElement) ? document.activeElement.dataset.focusKey : null;
  redraw();
  const wrap = slots.table?.querySelector(".table-wrap");
  if (wrap) wrap.scrollTop = scroll;
  const again = focusKey && [...app.querySelectorAll("[data-focus-key]")].find((el) => el.dataset.focusKey === focusKey);
  if (!again) return;
  again.focus();
  if (again.setSelectionRange) again.setSelectionRange(again.value.length, again.value.length);
}

/** Re-draw only the table and bulk bar. */
const refreshTable = () => keepPlace(() => {
  const table = Table();
  slots.table.replaceWith(table);
  slots.table = table;
  const bulk = Bulk();
  slots.bulk.replaceWith(bulk);
  slots.bulk = bulk;
});

function showProject(path) {
  tableHandlers.setTable({ project: path, search: "", group: "all" });
  slots.table.scrollIntoView({ behavior: "smooth", block: "start" });
}

function openDetail(skill) {
  state.drawer?.close();
  const closeThen = (fn) => (...args) => { state.drawer?.close(); fn(...args); };
  state.drawer = Drawer({
    title: skill.name, subtitle: skill.id, closeLabel: COPY.actions.close, onClose: () => { state.drawer = null; },
    body: SkillDetail(skill, state.report, { onAction: closeThen(act.runAction), onMoveGroup: act.moveToGroup, onProject: closeThen(showProject) }),
  });
}

// ── layout ──
const Header = () => Masthead({ report: state.report, loading: state.loading, machines: state.machines,
  onMachine: (id) => { state.machine = id; load(); },
  onRefresh: () => load(), onCheckUpdates: () => load({ refresh: true }) });

const render = () => keepPlace(() => {
  const r = state.report;
  if (!r) {
    app.replaceChildren(Header(), h("p", { class: "empty" }, state.error ? fill(COPY.page.loadFailed, { error: state.error }) : COPY.page.loading));
    return;
  }
  slots.table = Table();
  slots.bulk = Bulk();
  app.replaceChildren(
    Header(),
    KpiRow(r),
    h("div", { class: "band" }, UsagePanel(r), TopPanel(r, (item) => openDetail(r.skills.find((s) => s.id === item.id)))),
    ...(r.cost ? CostBands(r, showProject) : []),
    h("div", { class: "band" }, UpdatesPanel(r, act.runAction), McpPanel(r, act.runAction, state.mcpChecking)),
    h("div", { class: "band" }, ProjectsPanel(r, showProject), RecentlyAddedPanel(r, openDetail), RecentPanel(r), TrashPanel(r, act.runAction)),
    slots.table,
    Coverage(r),
    slots.bulk);
});

load();
