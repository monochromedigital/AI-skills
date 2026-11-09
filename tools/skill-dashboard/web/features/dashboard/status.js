// Shared pieces every dashboard panel uses: how a status looks, how a reason
// reads, how a source is named, and which buttons a row offers.

import { COPY, fill } from "../../content.js";
import { Button, h, LinkButton, StatusPill } from "../../ui.js";
import { relative } from "../../format.js";

export const when = (value) => relative(value, COPY.time);

const SKILL_STATUS = {
  update: { tone: "warning", icon: "arrow-up" },
  current: { tone: "good", icon: "check" },
  drift: { tone: "serious", icon: "alert" },
  managed: { tone: "neutral", icon: "cloud" },
  untracked: { tone: "muted", icon: "minus" },
  "not-installed": { tone: "neutral", icon: "plus" },
  builtin: { tone: "neutral", icon: "box" },
  unknown: { tone: "muted", icon: "question" },
};

export const MCP_STATUS = {
  connected: { tone: "good", icon: "check" },
  "needs-auth": { tone: "warning", icon: "key" },
  failed: { tone: "critical", icon: "x" },
  pending: { tone: "neutral", icon: "pause" },
  disabled: { tone: "muted", icon: "minus" },
  unknown: { tone: "muted", icon: "question" },
};

// Statuses whose explanation earns a line in the table; the rest keep it in the tooltip.
export const INLINE_REASON = new Set(["update", "drift", "unknown"]);

// Actions that add or refresh get the filled button; removals stay quiet.
const PRIMARY_ACTIONS = new Set(["plugin-update", "skill-update-from-repo", "skill-install-from-repo"]);

export const sourceLabel = (item) => fill(COPY.sources[item.source] ?? item.source, { plugin: item.plugin });

export function reasonText(update) {
  let key = update.reason;
  if (key === "plugin-version" && update.refreshMarketplace) key = "plugin-version-stale";
  if ((key === "repo-newer" || key === "installed-newer") && update.target === "account") key += "-account";
  const template = COPY.reasons[update.status === "current" ? `${key}-current` : key] ?? COPY.reasons[key];
  return template ? fill(template, update) : "";
}

export function SkillStatus(update) {
  const style = SKILL_STATUS[update.status] ?? SKILL_STATUS.unknown;
  return StatusPill({ ...style, text: COPY.status[update.status] ?? update.status, title: reasonText(update) });
}

export function ActionButtons({ actions, item, onAction, links }) {
  const buttons = actions.map((action) => Button({
    label: COPY.actions[action].label,
    variant: PRIMARY_ACTIONS.has(action) ? "primary" : "ghost",
    size: "sm",
    onClick: () => onAction(action, item),
  }));
  if (item.source === "account") buttons.push(LinkButton({ label: COPY.actions.manageAccount, href: links.accountSkills }));
  return buttons.length ? h("div", { class: "actions" }, buttons) : null;
}
