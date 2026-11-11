// The page header: the page tabs, title, when the data was last synced, and the refresh buttons.

import { COPY, fill } from "../../content.js";
import { Dropdown, Tabs } from "../../controls.js";
import { relative } from "../../format.js";
import { Button, h, Text } from "../../ui.js";

/** Which Mac's snapshot to show, or all of them; only drawn on the online console, where there is a choice. */
function MachinePicker({ machines, value, onChange }) {
  if (machines.length < 2) return null;
  return Dropdown({ label: COPY.page.machine, prefix: COPY.page.machine, value, onChange,
    options: machines.map((m) => ({ value: m.id, label: m.name, count: m.lastSync ? relative(m.lastSync, COPY.time) : null })) });
}

export function Masthead({ view, nav, report, loading, machines = [], onMachine, onRefresh, onCheckUpdates }) {
  const when = report?.coverage.lastSync ? relative(report.coverage.lastSync, COPY.time) : null;
  const synced = when ? fill(report.readOnly ? COPY.page.snapshot : COPY.page.synced, { when }) : null;
  return h("header", { class: "masthead" },
    h("div", {}, Tabs({ label: COPY.nav.label, items: nav }),
      h("h1", { class: "masthead__title" }, COPY.views[view].title),
      h("p", { class: "masthead__lede" }, (report?.combined && COPY.views[view].ledeCombined) || COPY.views[view].lede)),
    h("div", { class: "masthead__tools" },
      synced ? Text({ text: synced, tone: "muted" }) : null,
      MachinePicker({ machines, value: report?.machine?.id, onChange: onMachine }),
      Button({ label: COPY.page.refresh, icon: "refresh", disabled: loading, onClick: onRefresh }),
      report?.readOnly ? null : Button({ label: COPY.page.checkUpdates, variant: "primary", disabled: loading, onClick: onCheckUpdates })));
}
