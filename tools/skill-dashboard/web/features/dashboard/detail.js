// One skill in full: what it is, its status and actions, how much it is used,
// and which projects and sessions it was used in. Shown in the side drawer.

import { COPY, fill } from "../../content.js";
import { RankedBars } from "../../charts.js";
import { day, full, number } from "../../format.js";
import { Badge, Button, EmptyState, h, ListRow, Text } from "../../ui.js";
import { ActionButtons, reasonText, SkillStatus, sourceLabel, when } from "./status.js";
import { targetFor } from "./menu.js";

const Stat = (label, value, title) => h("div", { class: "kv" }, h("dt", {}, label), h("dd", { title }, value));
const Section = (title, body) => h("section", { class: "detail__section" }, h("h3", { class: "detail__heading" }, title), body);

export function SkillDetail(s, report, { onAction, onMoveGroup, onProject }) {
  const st = COPY.detail.stats;
  const none = COPY.table.never;
  const projectName = new Map(report.projects.map((p) => [p.path, p.name]));
  const groupName = report.groups.find((g) => g.id === s.group)?.name ?? s.group;

  const projects = Object.entries(s.byProject).sort((a, b) => b[1] - a[1]).map(([path, count]) => ({
    id: path, label: projectName.get(path) ?? path, value: count, valueText: number(count),
    tooltip: [projectName.get(path) ?? path, fill(COPY.detail.projectTooltip, { count: number(count) })],
  }));
  const sessions = s.sessions.map((x) => ListRow({
    title: x.title ?? COPY.detail.untitled,
    meta: fill(x.uses === 1 ? COPY.detail.sessionMetaOne : COPY.detail.sessionMeta, { project: x.project ?? none, count: number(x.uses) }),
    trail: Text({ text: when(x.lastUsed), tone: "muted", size: "xs", title: full(x.lastUsed) }),
  }));

  return h("div", { class: "detail" },
    h("div", { class: "detail__badges" },
      Badge({ text: sourceLabel(s) }), Badge({ text: groupName }), s.version ? Badge({ text: s.version }) : null),
    s.description ? h("p", { class: "detail__desc" }, s.description) : null,
    h("div", { class: "detail__status" }, SkillStatus(s.update), Text({ text: reasonText(s.update), tone: "muted", size: "xs" })),
    report.readOnly ? null : h("div", { class: "detail__actions" },
      ActionButtons({ actions: s.actions, item: targetFor(s), onAction, links: report.links }),
      Button({ label: COPY.menu.move, icon: "folder", size: "sm", onClick: (e) => onMoveGroup([s.id], e.currentTarget, s.group) })),
    h("dl", { class: "kvs" },
      Stat(st.uses, number(s.uses)),
      Stat(fill(st.recent, { days: report.windows.recentDays }), number(s.usesRecent)),
      Stat(st.projects, number(s.projects)),
      Stat(st.firstUsed, s.firstUsed ? day(s.firstUsed) : none, full(s.firstUsed)),
      Stat(st.lastUsed, s.lastUsed ? when(s.lastUsed) : none, full(s.lastUsed)),
      Stat(st.added, s.addedAt ? day(s.addedAt) : none, full(s.addedAt))),
    s.uses ? Text({ as: "p", tone: "muted", size: "xs",
      text: fill(COPY.detail.via, { model: number(s.viaModel), slash: number(s.viaSlash), subagent: number(s.viaSubagent) }) }) : null,
    Section(COPY.detail.projects, projects.length ? RankedBars({ items: projects, onSelect: (item) => onProject(item.id) }) : EmptyState(COPY.detail.notUsed)),
    Section(COPY.detail.sessions, sessions.length ? h("ul", { class: "list" }, sessions) : EmptyState(COPY.detail.notUsed)));
}
