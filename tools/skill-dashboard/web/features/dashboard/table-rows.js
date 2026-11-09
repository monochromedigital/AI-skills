// The pieces of the skills table: sortable header cells, the row for one
// skill, and the header row of a group.

import { COPY, fill } from "../../content.js";
import { Menu } from "../../controls.js";
import { full, isRecent, number } from "../../format.js";
import { Badge, Checkbox, h, Icon, Text } from "../../ui.js";
import { INLINE_REASON, reasonText, SkillStatus, sourceLabel, when } from "./status.js";

const byText = (key) => (a, b) => (a[key] ?? "").localeCompare(b[key] ?? "");

export const SORTERS = {
  name: (a, b) => a.id.localeCompare(b.id),
  group: byText("group"),
  uses: (a, b, here) => here(a) - here(b),
  recent: (a, b) => a.usesRecent - b.usesRecent,
  lastUsed: byText("lastUsed"),
  added: byText("addedAt"),
  status: (a, b) => a.update.status.localeCompare(b.update.status),
};

export function HeaderCell({ key, label, sort, onSort, className }) {
  const active = sort.key === key;
  return h("th", { scope: "col", class: className, "aria-sort": active ? (sort.dir === "asc" ? "ascending" : "descending") : null },
    SORTERS[key]
      ? h("button", { type: "button", class: ["sort", active && "is-active"],
        onClick: () => onSort({ key, dir: active && sort.dir === "desc" ? "asc" : "desc" }) },
      label, active ? Icon(sort.dir === "asc" ? "chevron-up" : "chevron-down", "sm") : null)
      : label);
}

export function GroupRow({ section, span, selectable, selection, collapsed, onToggle, onSelect }) {
  const ids = section.rows.map((s) => s.id);
  const picked = ids.filter((id) => selection.has(id)).length;
  const uses = section.rows.reduce((sum, s) => sum + s.uses, 0);
  return h("tr", { class: "group-row" },
    selectable && h("td", { class: "cell-check" }, Checkbox({ label: fill(COPY.table.selectGroup, { group: section.label }),
      checked: picked === ids.length, indeterminate: picked > 0 && picked < ids.length, onChange: (on) => onSelect(ids, on) })),
    h("td", { colspan: span },
      h("button", { type: "button", class: "group-toggle", "aria-expanded": String(!collapsed),
        "aria-label": fill(COPY.table.toggleGroup, { group: section.label }), onClick: () => onToggle(section.key) },
      Icon(collapsed ? "chevron-right" : "chevron-down", "sm"),
      h("span", { class: "group-toggle__name" }, section.label),
      h("span", { class: "group-toggle__meta" }, fill(COPY.table.groupMeta, { count: number(ids.length), uses: number(uses) })))));
}

function NameCell(s, ctx) {
  const isNew = isRecent(s.addedAt, ctx.newBadgeDays);
  return h("td", { class: "cell-name" },
    h("div", { class: "cell-name__title" },
      h("button", { type: "button", class: "name-link", onClick: () => ctx.onDetails(s) }, s.name),
      isNew ? Badge({ text: COPY.table.isNew, tone: "new" }) : null,
      s.kind === "command" ? Badge({ text: COPY.table.command }) : null),
    h("div", { class: "cell-name__meta" },
      Badge({ text: sourceLabel(s) }),
      s.version ? Text({ text: s.version, tone: "muted", size: "xs" }) : null,
      s.enabled ? null : Badge({ text: COPY.table.off, tone: "muted" })),
    s.description ? h("div", { class: "cell-name__desc", title: s.description }, s.description) : null);
}

export function SkillRow(s, ctx) {
  const dateCell = (value) => h("td", { class: "nowrap", title: full(value) }, value ? when(value) : COPY.table.never);
  const here = ctx.here(s);
  return h("tr", { class: [!s.enabled && "is-off", ctx.selection.has(s.id) && "is-selected"], "data-skill-id": s.id },
    ctx.selectable && h("td", { class: "cell-check" }, Checkbox({ label: fill(COPY.table.selectRow, { name: s.name }),
      checked: ctx.selection.has(s.id), onChange: (on, { shift }) => ctx.onSelect([s.id], on, { shift }) })),
    NameCell(s, ctx),
    ctx.showGroup ? h("td", {}, Badge({ text: ctx.groupName(s.group) })) : null,
    h("td", { class: "num" }, here ? number(here) : COPY.table.never),
    h("td", { class: "num" }, s.usesRecent ? number(s.usesRecent) : COPY.table.never),
    dateCell(s.lastUsed),
    dateCell(s.addedAt),
    h("td", {}, SkillStatus(s.update), INLINE_REASON.has(s.update.status) ? h("div", { class: "cell-reason" }, reasonText(s.update)) : null),
    h("td", { class: "cell-menu" }, Menu({ label: fill(COPY.table.rowMenu, { name: s.name }), items: () => ctx.menuFor(s) })));
}
