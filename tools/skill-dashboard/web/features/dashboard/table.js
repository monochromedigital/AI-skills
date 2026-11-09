// Every skill in one table: filters across the top, rows grouped (by group,
// source, or not at all), a header that stays put while the rows scroll,
// checkboxes for bulk editing and a three-dots menu per row.

import { COPY, fill } from "../../content.js";
import { Dropdown } from "../../controls.js";
import { number } from "../../format.js";
import { Checkbox, EmptyState, h, Panel, SearchInput, Text } from "../../ui.js";
import { GroupRow, HeaderCell, SkillRow, SORTERS } from "./table-rows.js";

/** Ids of the rows from one skill to another, inclusive, in on-screen order (for shift-click). */
export function rowsBetween(root, fromId, toId) {
  const order = [...root.querySelectorAll("tr[data-skill-id]")].map((tr) => tr.dataset.skillId);
  const [a, b] = [order.indexOf(fromId), order.indexOf(toId)].sort((x, y) => x - y);
  return a >= 0 ? order.slice(a, b + 1) : [toId];
}

export const usesIn = (project) => (s) => (project === "all" ? s.uses : s.byProject[project] ?? 0);

export function filterSkills(skills, t) {
  const query = t.search.trim().toLowerCase();
  const here = usesIn(t.project);
  const rows = skills.filter((s) =>
    (!query || `${s.id} ${s.description}`.toLowerCase().includes(query))
    && (t.source === "all" || s.source === t.source)
    && (t.status === "all" || s.update.status === t.status)
    && (t.group === "all" || s.group === t.group)
    && (t.project === "all" || here(s) > 0)
    && (t.usage === "all" || (t.usage === "used" ? s.uses > 0 : s.uses === 0)));
  const sorter = SORTERS[t.sort.key] ?? SORTERS.uses;
  return rows.sort((a, b) => sorter(a, b, here) * (t.sort.dir === "asc" ? 1 : -1) || a.id.localeCompare(b.id));
}

function sections(rows, report, groupBy) {
  if (groupBy === "none") return [{ key: "all", label: null, rows }];
  const order = groupBy === "group" ? report.groups.map((g) => [g.id, g.name]) : Object.entries(COPY.sourceFilter);
  const byKey = new Map(order.map(([key, label]) => [key, { key, label, rows: [] }]));
  for (const s of rows) {
    const key = groupBy === "group" ? s.group : s.source;
    if (!byKey.has(key)) byKey.set(key, { key, label: key, rows: [] });
    byKey.get(key).rows.push(s);
  }
  return [...byKey.values()].filter((section) => section.rows.length);
}

function Toolbar(report, t, setTable) {
  const option = (value, label, count) => ({ value, label, count: count == null ? null : number(count) });
  const distinct = (key) => [...new Set(report.skills.map(key))];
  const searchMin = report.ui.dropdownSearchMin;
  return h("div", { class: "filters" },
    SearchInput({ label: COPY.table.search, value: t.search, onInput: (search) => setTable({ search }) }),
    Dropdown({ label: COPY.table.groupAll, value: t.group, onChange: (group) => setTable({ group }), searchMin, searchLabel: COPY.table.groupSearch,
      options: [option("all", COPY.table.groupAll), ...report.groups.filter((g) => g.skills).map((g) => option(g.id, g.name, g.skills))] }),
    Dropdown({ label: COPY.table.projectAll, value: t.project, onChange: (project) => setTable({ project }), searchMin, searchLabel: COPY.table.projectSearch,
      options: [option("all", COPY.table.projectAll), ...report.projects.map((p) => option(p.path, p.name, p.uses))] }),
    Dropdown({ label: COPY.table.sourceAll, value: t.source, onChange: (source) => setTable({ source }),
      options: [option("all", COPY.table.sourceAll), ...distinct((s) => s.source).map((v) => option(v, COPY.sourceFilter[v] ?? v))] }),
    Dropdown({ label: COPY.table.statusAll, value: t.status, onChange: (status) => setTable({ status }),
      options: [option("all", COPY.table.statusAll), ...distinct((s) => s.update.status).map((v) => option(v, COPY.status[v] ?? v))] }),
    Dropdown({ label: COPY.table.usageAll, value: t.usage, onChange: (usage) => setTable({ usage }),
      options: [option("all", COPY.table.usageAll), option("used", COPY.table.usageUsed), option("unused", COPY.table.usageUnused)] }),
    Dropdown({ label: COPY.table.groupBy, prefix: COPY.table.groupBy, value: t.groupBy, onChange: (groupBy) => setTable({ groupBy }),
      options: [option("group", COPY.table.groupByGroup), option("source", COPY.table.groupBySource), option("none", COPY.table.groupByNone)] }));
}

export function SkillsTable(report, view, handlers) {
  const { table: t, selection, collapsed } = view;
  const rows = filterSkills(report.skills, t);
  const showGroup = t.groupBy !== "group";
  const selectable = !report.readOnly;
  const names = new Map(report.groups.map((g) => [g.id, g.name]));
  const ctx = {
    ...handlers, selection, showGroup, selectable, here: usesIn(t.project), groupName: (id) => names.get(id) ?? id,
    newBadgeDays: report.ui.newBadgeDays,
  };
  const picked = rows.filter((s) => selection.has(s.id)).length;
  const col = COPY.table.columns;
  const sortProps = { sort: t.sort, onSort: (sort) => handlers.setTable({ sort }) };
  const head = h("thead", {}, h("tr", {},
    selectable && h("th", { class: "cell-check" }, Checkbox({ label: COPY.table.selectAll, checked: rows.length > 0 && picked === rows.length,
      indeterminate: picked > 0 && picked < rows.length, onChange: (on) => handlers.onSelect(rows.map((s) => s.id), on) })),
    HeaderCell({ key: "name", label: col.name, ...sortProps }),
    showGroup ? HeaderCell({ key: "group", label: col.group, ...sortProps }) : null,
    HeaderCell({ key: "uses", label: t.project === "all" ? col.uses : col.usesIn, className: "num", ...sortProps }),
    HeaderCell({ key: "recent", label: fill(col.recent, { days: report.windows.recentDays }), className: "num", ...sortProps }),
    HeaderCell({ key: "lastUsed", label: col.lastUsed, ...sortProps }),
    HeaderCell({ key: "added", label: col.added, ...sortProps }),
    HeaderCell({ key: "status", label: col.status, ...sortProps }),
    h("th", { class: "cell-menu" })));
  const span = head.querySelectorAll("th").length - (selectable ? 1 : 0);
  const bodies = sections(rows, report, t.groupBy).map((section) => h("tbody", {},
    section.label ? GroupRow({ section, span, selectable, selection, collapsed: collapsed.has(section.key),
      onToggle: handlers.onToggleGroup, onSelect: handlers.onSelect }) : null,
    collapsed.has(section.key) ? null : section.rows.map((s) => SkillRow(s, ctx))));
  return Panel({
    title: COPY.table.title, className: "panel--full", caption: selectable ? COPY.table.selectHint : null,
    actions: Text({ text: fill(COPY.table.caption, { shown: number(rows.length), total: number(report.skills.length) }), tone: "muted" }),
    body: [Toolbar(report, t, handlers.setTable),
      rows.length ? h("div", { class: "table-wrap" }, h("table", { class: "table" }, head, bodies)) : EmptyState(COPY.table.empty)],
  });
}
