// Bulk editing: what a selection of skills turns into, and the bar that acts on it.
// A plugin can't lose one skill, so selected plugin skills become one
// "remove plugin" or "update plugin" item per plugin, never one per skill.

import { COPY, fill } from "../../content.js";
import { number } from "../../format.js";
import { Button, h } from "../../ui.js";

export function planBulk(selected) {
  const update = new Map();
  const uninstall = new Map();
  const install = [];
  const plugins = new Set();
  let personal = 0;
  let skipped = 0;
  for (const s of selected) {
    if (s.source === "plugin") {
      if (s.update.status === "update") update.set(s.update.pluginKey, { action: "plugin-update", target: s.update.pluginKey });
      uninstall.set(s.update.pluginKey, { action: "plugin-uninstall", target: s.update.pluginKey });
      plugins.add(s.plugin);
    } else if (s.source === "personal") {
      if (s.update.reason === "repo-newer") update.set(s.id, { action: "skill-update-from-repo", target: s.id });
      uninstall.set(s.id, { action: "skill-uninstall", target: s.id });
      personal += 1;
    } else if (s.source === "repo") {
      install.push({ action: "skill-install-from-repo", target: s.id });
    } else {
      skipped += 1;
    }
  }
  return {
    ids: selected.map((s) => s.id),
    update: [...update.values()],
    install,
    uninstall: [...uninstall.values()],
    summary: { personal, plugins: [...plugins].sort(), skipped },
  };
}

/** The confirmation text for a bulk uninstall, one sentence per kind of thing it touches. */
export function uninstallSummary({ personal, plugins, skipped }) {
  return [
    personal ? fill(COPY.bulk.personal, { count: number(personal) }) : null,
    plugins.length ? fill(COPY.bulk.plugins, { count: number(plugins.length), names: plugins.join(", ") }) : null,
    skipped ? fill(COPY.bulk.skipped, { count: number(skipped) }) : null,
  ].filter(Boolean).join(" ");
}

export function BulkBar({ plan, onUpdate, onInstall, onUninstall, onMove, onClear }) {
  if (!plan.ids.length) return h("div", { class: "bulkbar", hidden: true });
  const count = (items) => number(items.length);
  return h("div", { class: "bulkbar", role: "toolbar", "aria-label": fill(COPY.bulk.selected, { count: plan.ids.length }) },
    h("span", { class: "bulkbar__count" }, fill(COPY.bulk.selected, { count: number(plan.ids.length) })),
    Button({ label: fill(COPY.bulk.update, { count: count(plan.update) }), icon: "arrow-up", size: "sm", variant: "primary",
      disabled: !plan.update.length, onClick: onUpdate }),
    plan.install.length ? Button({ label: fill(COPY.bulk.install, { count: count(plan.install) }), icon: "download", size: "sm", onClick: onInstall }) : null,
    Button({ label: COPY.bulk.move, icon: "folder", size: "sm", onClick: (e) => onMove(e.currentTarget) }),
    Button({ label: fill(COPY.bulk.uninstall, { count: count(plan.uninstall) }), icon: "trash", size: "sm", variant: "danger-ghost",
      disabled: !plan.uninstall.length, onClick: onUninstall }),
    Button({ icon: "x", size: "sm", variant: "ghost", title: COPY.bulk.clear, onClick: onClear }));
}
