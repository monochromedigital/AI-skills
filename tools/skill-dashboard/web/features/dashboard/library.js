// Two ways into the library besides the table: the projects skills are used
// in, and the skills added most recently.

import { COPY, fill } from "../../content.js";
import { full, isRecent, number } from "../../format.js";
import { Badge, EmptyState, h, ListRow, Panel, Text } from "../../ui.js";
import { sourceLabel, when } from "./status.js";

const NameLink = (text, onClick) => h("button", { type: "button", class: "name-link", onClick }, text);

export function ProjectsPanel(report, onPick) {
  const rows = report.projects.map((p) => ListRow({
    title: NameLink(p.name, () => onPick(p.path)),
    meta: [fill(COPY.projects.meta, { uses: number(p.uses), skills: number(p.skills), sessions: number(p.sessions) }),
      fill(COPY.projects.top, { skills: p.top.join(", ") })].join(" · "),
    trail: Text({ text: when(p.lastUsed), tone: "muted", size: "xs", title: full(p.lastUsed) }),
  }));
  return Panel({
    title: COPY.projects.title, caption: COPY.projects.caption,
    body: rows.length ? h("ul", { class: ["list", "list--scroll"] }, rows) : EmptyState(COPY.projects.empty),
  });
}

export function RecentlyAddedPanel(report, onDetails) {
  const groupName = new Map(report.groups.map((g) => [g.id, g.name]));
  const newest = report.skills.filter((s) => s.addedAt && s.source !== "builtin")
    .sort((a, b) => b.addedAt.localeCompare(a.addedAt)).slice(0, report.ui.recentlyAdded);
  const rows = newest.map((s) => ListRow({
    title: [NameLink(s.name, () => onDetails(s)),
      isRecent(s.addedAt, report.ui.newBadgeDays) ? Badge({ text: COPY.table.isNew, tone: "new" }) : null],
    meta: [sourceLabel(s), groupName.get(s.group)].filter(Boolean).join(" · "),
    trail: Text({ text: when(s.addedAt), tone: "muted", size: "xs", title: full(s.addedAt) }),
  }));
  return Panel({
    title: COPY.added.title, caption: COPY.added.caption,
    body: rows.length ? h("ul", { class: "list" }, rows) : EmptyState(COPY.added.empty),
  });
}
