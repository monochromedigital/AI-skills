// What needs doing: skill and plugin updates, and MCP servers that need a sign-in.

import { COPY, fill } from "../../content.js";
import { shortPath } from "../../format.js";
import { Badge, Button, EmptyState, h, ListRow, Panel, StatusPill, Text } from "../../ui.js";
import { ActionButtons, MCP_STATUS, reasonText, SkillStatus, sourceLabel, when } from "./status.js";

export function UpdatesPanel(report, onAction) {
  const rows = report.updates.map((u) => {
    const isPlugin = u.kind === "plugin";
    const meta = [reasonText(u)];
    if (isPlugin) meta.push(u.skills === 1 ? COPY.updates.pluginSkillsOne : fill(COPY.updates.pluginSkills, { count: u.skills }));
    const item = isPlugin ? { target: u.pluginKey, plugin: u.plugin, name: u.plugin, source: "plugin" }
      : { target: u.id, name: u.name, source: u.source };
    return ListRow({
      lead: SkillStatus(u), title: isPlugin ? u.plugin : u.name, meta: meta.filter(Boolean).join(" · "),
      // Removing a plugin is offered in the table; this panel is for updating.
      trail: ActionButtons({ actions: report.readOnly ? [] : u.actions.filter((a) => a !== "plugin-uninstall"), item, onAction, links: report.links }),
    });
  });
  return Panel({
    title: COPY.updates.title, caption: COPY.updates.caption,
    body: rows.length ? h("ul", { class: "list" }, rows) : EmptyState(COPY.updates.empty),
  });
}

function McpRow(server, onAction, readOnly) {
  const style = MCP_STATUS[server.status] ?? MCP_STATUS.unknown;
  const attention = server.status !== "connected";
  return ListRow({
    lead: StatusPill({ ...style, text: COPY.mcpStatus[server.status] ?? server.statusText, title: server.statusText }),
    title: [server.label, " ", Badge({ text: sourceLabel(server) })],
    meta: h("span", { class: "mono", title: server.target }, server.target),
    // stdio servers run locally and have nothing to sign in to.
    trail: server.transport === "stdio" || readOnly ? null : Button({
      label: attention ? COPY.mcp.signIn : COPY.mcp.reauth, variant: attention ? "primary" : "ghost", size: "sm",
      onClick: () => onAction("mcp-login", { target: server.name, name: server.label }),
    }),
  });
}

export function McpPanel(report, onAction, checking) {
  const status = report.mcp;
  const caption = status ? fill(COPY.mcp.caption, { when: when(status.checkedAt), dir: shortPath(status.checkedFrom, 1) }) : COPY.mcp.neverChecked;
  const check = report.readOnly ? null : Button({ label: COPY.mcp.checkAll, icon: "refresh", size: "sm", disabled: checking, onClick: () => onAction("mcp-check", { target: null }) });
  const servers = [...(status?.servers ?? [])].sort((a, b) =>
    (a.status === "connected") - (b.status === "connected") || a.name.localeCompare(b.name));
  let body;
  if (checking) body = EmptyState(COPY.mcp.checking);
  else if (!status) body = EmptyState(COPY.mcp.neverChecked);
  else if (!servers.length) body = EmptyState(COPY.mcp.empty);
  else body = [h("ul", { class: ["list", "list--scroll"] }, servers.map((s) => McpRow(s, onAction, report.readOnly))),
    Text({ text: COPY.mcp.projectNote, tone: "muted", size: "xs", as: "p" })];
  return Panel({ title: COPY.mcp.title, caption, actions: check, body });
}
