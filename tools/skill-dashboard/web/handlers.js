// What happens when you click: single actions, bulk actions, groups, copy.
// Each handler confirms when something is removed, shows progress in a toast,
// and reloads the report when the job finishes.

import { runJob } from "./api.js";
import { COPY, fill } from "./content.js";
import { openListbox } from "./controls.js";
import { planBulk, uninstallSummary } from "./features/dashboard/bulk.js";
import { number } from "./format.js";
import { confirmDialog, promptDialog, toast } from "./overlays.js";

export function createHandlers({ state, reload, render }) {
  const pollMs = () => state.report.ui.pollMilliseconds;
  const note = (text, icon = "refresh") => toast({ text, icon, closeLabel: COPY.actions.close });
  const failedNote = (handle, text, job) => handle.update({ text: [text, job.error].filter(Boolean).join(" "),
    tone: "critical", icon: "x", log: (job.log || []).join("\n") || null });

  async function runAction(action, item, { quiet = false } = {}) {
    const copy = COPY.actions[action];
    const label = item.name ?? item.target ?? "";
    if (copy.confirmTitle) {
      const values = { ...item, count: item.plugin ? state.report.skills.filter((s) => s.plugin === item.plugin).length : 0 };
      const ok = await confirmDialog({ title: fill(copy.confirmTitle, values), body: fill(copy.confirmBody, values),
        confirmLabel: copy.confirm, cancelLabel: COPY.actions.cancel });
      if (!ok) return;
    }
    const handle = quiet ? null : note(fill(copy.running, { target: label }));
    if (action === "mcp-check") { state.mcpChecking = true; render(); }
    const job = await runJob(action, item.target, pollMs());
    if (action === "mcp-check") state.mcpChecking = false;
    if (job.status === "done") {
      const restart = job.result?.restartNeeded ? ` ${COPY.actions.restartNeeded}` : "";
      handle?.update({ text: fill(copy.done, { target: label }) + restart, tone: "good", icon: "check" });
    } else {
      failedNote(handle ?? note(""), fill(copy.failed, { target: label }), job);
    }
    await reload();
  }

  async function runBulk(kind) {
    const plan = planBulk(state.report.skills.filter((s) => state.selection.has(s.id)));
    const items = plan[kind];
    if (!items.length) return;
    if (kind === "uninstall") {
      const ok = await confirmDialog({ title: fill(COPY.bulk.confirmTitle, { count: number(plan.ids.length) }),
        body: uninstallSummary(plan.summary), confirmLabel: COPY.bulk.confirm, cancelLabel: COPY.actions.cancel });
      if (!ok) return;
    }
    const handle = note(fill(COPY.bulk.running, { count: number(items.length) }));
    const job = await runJob("bulk", { items }, pollMs());
    const result = job.result ?? {};
    if (job.status === "done" && !result.failed?.length) {
      const restart = result.restartNeeded ? ` ${COPY.actions.restartNeeded}` : "";
      handle.update({ text: fill(COPY.bulk.done, { done: number(result.done) }) + restart, tone: "good", icon: "check" });
    } else {
      failedNote(handle, fill(COPY.bulk.partial, { done: number(result.done ?? 0), failed: number(result.failed?.length ?? items.length),
        names: (result.failed ?? []).join(", ") }), job);
    }
    state.selection.clear();
    await reload();
  }

  async function groupJob(action, target, count) {
    const job = await runJob(action, target, pollMs());
    if (job.status === "done") {
      const id = job.result?.group ?? target.group;
      const name = state.report.groups.find((g) => g.id === id)?.name ?? target.name ?? id;
      note(fill(COPY.groups.moved, { count: number(count), group: name }), "check").update({ tone: "good" });
    } else {
      failedNote(note(""), COPY.groups.failed, job);
    }
    await reload();
  }

  function moveToGroup(ids, anchor, current) {
    openListbox(anchor, {
      label: COPY.groups.pick, value: current, searchMin: state.report.ui.dropdownSearchMin, searchLabel: COPY.groups.search,
      options: state.report.groups.map((g) => ({ value: g.id, label: g.name, count: number(g.skills) })),
      onPick: (group) => groupJob("group-assign", { ids, group }, ids.length),
      extra: [{ label: COPY.groups.newGroup, icon: "plus", onSelect: async () => {
        const name = await promptDialog({ title: COPY.groups.newTitle, label: COPY.groups.newLabel,
          confirmLabel: COPY.groups.create, cancelLabel: COPY.actions.cancel });
        if (name) groupJob("group-create", { name, ids }, ids.length);
      } }],
    });
  }

  async function copySkill(skill) {
    const text = `/${skill.id}`;
    await navigator.clipboard?.writeText(text);
    note(fill(COPY.menu.copied, { name: skill.id }), "check").update({ tone: "good" });
  }

  const openLink = (href) => window.open(href, "_blank", "noopener,noreferrer");

  return { runAction, runBulk, moveToGroup, copySkill, openLink };
}
