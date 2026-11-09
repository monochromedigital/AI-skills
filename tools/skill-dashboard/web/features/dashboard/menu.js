// Everything you can do to one skill, as the items of its three-dots menu.
// Options that don't apply right now stay visible but disabled, with the
// reason beside them, so the menu always shows the full set.

import { COPY, fill } from "../../content.js";

export const targetFor = (s) => ({
  target: s.source === "plugin" ? s.update.pluginKey : s.id, name: s.name, plugin: s.plugin, source: s.source,
});

// Uninstall is always listed. Only personal skills and plugins can be removed
// from this Mac; for the rest it stays visible, disabled, with the reason.
function uninstallItem(s, item, onAction) {
  if (s.source === "personal") return { label: COPY.menu.uninstall, icon: "trash", danger: true, onSelect: () => onAction("skill-uninstall", item) };
  if (s.source === "plugin") {
    return { label: fill(COPY.menu.removePlugin, { plugin: s.plugin }), icon: "trash", danger: true, onSelect: () => onAction("plugin-uninstall", item) };
  }
  return { label: COPY.menu.uninstall, icon: "trash", danger: true, disabled: true, hint: COPY.menu.cannotUninstall[s.source] };
}

// What a read-only snapshot still offers: looking, copying, and the claude.ai link.
const SAFE = new Set(["details", "copy", "manage"]);

export function skillMenuItems(s, { onAction, onDetails, onMoveGroup, onCopy, onOpenLink, links, readOnly }) {
  const item = targetFor(s);
  const u = s.update;
  return [
    { key: "details", label: COPY.menu.details, icon: "info", onSelect: () => onDetails(s) },
    s.source === "plugin" && {
      label: fill(COPY.menu.updatePlugin, { plugin: s.plugin }), icon: "arrow-up",
      disabled: u.status !== "update", hint: COPY.menu.upToDate, onSelect: () => onAction("plugin-update", item),
    },
    s.source === "personal" && {
      label: COPY.menu.updateRepo, icon: "arrow-up", disabled: u.reason !== "repo-newer",
      hint: s.inRepo ? COPY.menu.upToDate : COPY.menu.noSource, onSelect: () => onAction("skill-update-from-repo", item),
    },
    s.source === "repo" && { label: COPY.menu.install, icon: "download", onSelect: () => onAction("skill-install-from-repo", item) },
    { label: COPY.menu.move, icon: "folder", onSelect: (anchor) => onMoveGroup([s.id], anchor, s.group) },
    { key: "copy", label: fill(COPY.menu.copy, { name: s.id }), icon: "copy", onSelect: () => onCopy(s) },
    s.source === "account" && { key: "manage", label: COPY.menu.manage, icon: "external", onSelect: () => onOpenLink(links.accountSkills) },
    { separator: true },
    uninstallItem(s, item, onAction),
  ].filter((item) => item && (!readOnly || SAFE.has(item.key)));
}
