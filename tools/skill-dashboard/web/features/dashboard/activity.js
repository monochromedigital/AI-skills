// What happened: recent skill use, recently removed skills, and what the counts cover.

import { COPY, fill } from "../../content.js";
import { day, full, number } from "../../format.js";
import { Button, EmptyState, h, ListRow, Panel, Text } from "../../ui.js";
import { when } from "./status.js";

export function RecentPanel(report) {
  const rows = report.recent.map((e) => ListRow({
    title: e.name,
    meta: [fill(COPY.via[e.via] ?? e.via, { name: e.name }), e.project, e.subagent ? COPY.recent.subagent : null].filter(Boolean).join(" · "),
    trail: Text({ text: when(e.ts), tone: "muted", size: "xs", title: full(e.ts) }),
  }));
  return Panel({
    title: COPY.recent.title, caption: fill(COPY.recent.caption, { count: report.recent.length }),
    body: rows.length ? h("ul", { class: ["list", "list--scroll"] }, rows) : EmptyState(COPY.recent.empty),
  });
}

export function TrashPanel(report, onAction) {
  if (!report.trash.length || report.readOnly) return null;
  const rows = report.trash.map((t) => ListRow({
    title: t.name,
    meta: t.removedAt ? fill(COPY.trash.removed, { when: when(t.removedAt) }) : null,
    trail: Button({ label: COPY.trash.restore, size: "sm", onClick: () => onAction("skill-restore", { target: t.entry, name: t.name }) }),
  }));
  return Panel({ title: COPY.trash.title, caption: fill(COPY.trash.caption, { path: report.paths.trash }),
    body: h("ul", { class: ["list", "list--scroll"] }, rows) });
}

export function Coverage(report) {
  const c = report.coverage;
  const notes = [];
  const macs = report.combined ? new Intl.ListFormat(undefined, { type: "conjunction" }).format(report.combined.names) : null;
  if (c.since) notes.push(fill(macs ? COPY.page.coverageCombined : COPY.page.coverage, { since: day(c.since), transcripts: number(c.transcripts), macs }));
  if (!c.remoteEnabled) notes.push(COPY.page.remoteOff);
  const failed = Object.keys(c.remoteErrors || {}).length;
  if (failed) notes.push(fill(COPY.page.remoteFailed, { count: failed }));
  return h("footer", { class: "coverage" }, notes.map((n) => h("p", {}, n)));
}
