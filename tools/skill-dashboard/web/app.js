// Page layer: owns state, loads the report and switches between the two pages
// (pages/overview.js, pages/skills.js) by the address's #fragment. Clicks are
// handled in handlers.js; nothing below this file talks to the server.

import { fetchMachines, fetchReport } from "./api.js";
import { ALL_MACHINES } from "./combine.js";
import { COPY, fill } from "./content.js";
import { BulkBar, planBulk } from "./features/dashboard/bulk.js";
import { SkillDetail } from "./features/dashboard/detail.js";
import { Masthead } from "./features/dashboard/masthead.js";
import { skillMenuItems } from "./features/dashboard/menu.js";
import { rowsBetween, SkillsTable } from "./features/dashboard/table.js";
import { createHandlers } from "./handlers.js";
import { keepPlace } from "./keep-place.js";
import { Drawer } from "./overlays.js";
import { OverviewPage } from "./pages/overview.js";
import { SkillsPage } from "./pages/skills.js";
import { h } from "./ui.js";

const ROUTES = { overview: "#/", skills: "#/skills" };
const viewOf = () => (location.hash === ROUTES.skills ? "skills" : "overview");

const app = document.getElementById("app");
const state = {
  report: null, error: null, loading: false, mcpChecking: false, autoChecked: false, drawer: null, machines: [], machine: null,
  table: { search: "", source: "all", status: "all", usage: "all", group: "all", project: "all", groupBy: "group", sort: { key: "uses", dir: "desc" } },
  selection: new Set(), collapsed: new Set(), lastPicked: null, costPeriod: null, view: viewOf(),
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

/** Redraw without losing the table's scroll position or the control that had focus. */
const redraw = (fn) => keepPlace(app, () => slots.table?.querySelector(".table-wrap"), fn);

/** Re-draw only the table and bulk bar. */
const refreshTable = () => redraw(() => {
  const table = Table();
  slots.table.replaceWith(table);
  slots.table = table;
  const bulk = Bulk();
  slots.bulk.replaceWith(bulk);
  slots.bulk = bulk;
});

/** Switch page now (history entry included); the hashchange listener covers tabs, back and forward. */
function goTo(view) {
  if (state.view === view) return;
  history.pushState(null, "", ROUTES[view]);
  state.view = view;
  render();
  window.scrollTo(0, 0);
}
window.addEventListener("hashchange", () => { state.view = viewOf(); render(); window.scrollTo(0, 0); });

/** Show the skills used in one project: the Skills page, its table filtered to that folder. */
function showProject(path) {
  Object.assign(state.table, { project: path, search: "", group: "all" });
  state.view === "skills" ? refreshTable() : goTo("skills");
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

const costHandlers = { onPick: (path) => showProject(path), onPeriod: (id) => { state.costPeriod = id; render(); } };

// ── layout ──
// "All Macs" leads the list whenever the console has any Mac to show.
const machineChoices = () => (state.machines.length ? [{ id: ALL_MACHINES, name: COPY.page.allMachines }, ...state.machines] : []);
const Header = () => Masthead({ view: state.view, report: state.report, loading: state.loading, machines: machineChoices(),
  nav: Object.entries(ROUTES).map(([view, href]) => ({ href, label: COPY.nav[view], current: view === state.view })),
  onMachine: (id) => { state.machine = id; load(); },
  onRefresh: () => load(), onCheckUpdates: () => load({ refresh: true }) });

const render = () => redraw(() => {
  const r = state.report;
  if (!r) {
    app.replaceChildren(Header(), h("p", { class: "empty" }, state.error ? fill(COPY.page.loadFailed, { error: state.error }) : COPY.page.loading));
    return;
  }
  slots.table = Table();
  slots.bulk = Bulk();
  const page = state.view === "skills"
    ? SkillsPage(r, { table: slots.table, bulk: slots.bulk, onAction: act.runAction, mcpChecking: state.mcpChecking, showProject, openDetail })
    : OverviewPage(r, { costPeriod: state.costPeriod, costHandlers, onManage: () => goTo("skills"),
      onSkill: (item) => openDetail(r.skills.find((s) => s.id === item.id)) });
  app.replaceChildren(Header(), ...page);
});

load();
