// The page header: title, when the data was last synced, and the refresh buttons.

import { COPY, fill } from "../../content.js";
import { Dropdown } from "../../controls.js";
import { relative } from "../../format.js";
import { Button, h, Text } from "../../ui.js";

/** Which Mac's snapshot to show; only drawn once a second Mac has synced. */
function MachinePicker({ machines, value, onChange }) {
  if (machines.length < 2) return null;
  return Dropdown({ label: COPY.page.machine, prefix: COPY.page.machine, value, onChange,
    options: machines.map((m) => ({ value: m.id, label: m.name, count: relative(m.lastSync, COPY.time) })) });
}

export function Masthead({ report, loading, machines = [], onMachine, onRefresh, onCheckUpdates }) {
  const when = report?.coverage.lastSync ? relative(report.coverage.lastSync, COPY.time) : null;
  const synced = when ? fill(report.readOnly ? COPY.page.snapshot : COPY.page.synced, { when }) : null;
  return h("header", { class: "masthead" },
    h("div", {}, h("h1", { class: "masthead__title" }, COPY.page.title), h("p", { class: "masthead__lede" }, COPY.page.lede)),
    h("div", { class: "masthead__tools" },
      synced ? Text({ text: synced, tone: "muted" }) : null,
      MachinePicker({ machines, value: report?.machine?.id, onChange: onMachine }),
      Button({ label: COPY.page.refresh, icon: "refresh", disabled: loading, onClick: onRefresh }),
      report?.readOnly ? null : Button({ label: COPY.page.checkUpdates, variant: "primary", disabled: loading, onClick: onCheckUpdates })));
}
