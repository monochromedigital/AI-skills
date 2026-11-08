// Every word the dashboard shows. Components receive text from here and
// never carry their own. Values in {braces} are filled by fill().
// The table, menus, bulk editing, groups and detail panel live in copy-table.js.

import { COST_COPY } from "./copy-cost.js";
import { TABLE_COPY } from "./copy-table.js";

export const COPY = {
  ...TABLE_COPY,
  ...COST_COPY,
  page: {
    title: "Skills",
    lede: "Every skill on this Mac, how often Claude reaches for it, and what needs attention.",
    synced: "Synced {when}",
    snapshot: "Snapshot from {when} · read-only, refreshed daily",
    machine: "Mac",
    refresh: "Refresh",
    checkUpdates: "Check for updates",
    loading: "Reading your sessions…",
    loadFailed: "Couldn't load the dashboard: {error}",
    coverage: "Counting Claude Code sessions on this Mac since {since} ({transcripts} sessions read). Cloud sessions and claude.ai chats run elsewhere and aren't counted.",
    remoteOff: "GitHub update checks are off (updates.checkRemote in config.json).",
    remoteFailed: "Couldn't reach GitHub for {count} marketplace(s); plugin checks used the local copy.",
  },

  kpi: {
    installed: { label: "Installed", sub: "{used} used · {unused} never used" },
    recent: { label: "Uses, last {days} days", up: "+{delta} on the {days} days before", down: "−{delta} on the {days} days before", flat: "Same as the {days} days before" },
    total: { label: "All uses", sub: "since {since}" },
    updates: { label: "Updates", subSome: "ready to install", subNone: "everything current" },
    mcp: { label: "MCP servers", subSome: "{count} need attention", subNone: "all connected", subUnknown: "not checked yet" },
  },

  usage: {
    title: "Uses per day",
    caption: "Last {days} days, every project",
    tooltip: "{date} · {count} uses",
    tooltipOne: "{date} · 1 use",
    empty: "No skill use in this window yet.",
    srTable: "Uses per day",
  },

  top: {
    title: "Most used",
    caption: "All time",
    tooltip: "{count} uses · last {when} · {projects} projects",
    empty: "Nothing used yet.",
  },

  updates: {
    title: "Updates",
    caption: "Newer copies found for these",
    empty: "Everything installed is up to date.",
    pluginSkills: "{count} skills",
    pluginSkillsOne: "1 skill",
    restartNote: "Restart open Claude Code sessions to load the new version.",
  },

  mcp: {
    title: "MCP servers",
    caption: "Checked {when} from {dir}",
    neverChecked: "Not checked yet",
    checkAll: "Check all",
    checking: "Checking every server… this takes a few seconds.",
    signIn: "Sign in",
    reauth: "Sign in again",
    empty: "No MCP servers are configured.",
    projectNote: "Servers set up for one project only appear when checked from inside that project.",
  },

  recent: {
    title: "Recent activity",
    caption: "Latest {count} uses",
    empty: "No activity yet.",
    subagent: "in a subagent",
  },

  trash: {
    title: "Recently removed",
    caption: "Kept in {path}",
    restore: "Restore",
    empty: "Nothing removed.",
    removed: "Removed {when}",
  },

  sources: {
    plugin: "Plugin · {plugin}",
    personal: "Personal",
    account: "claude.ai",
    repo: "This repo",
    builtin: "Built in",
    config: "Your config",
  },

  sourceFilter: {
    plugin: "Plugins",
    personal: "Personal",
    account: "claude.ai",
    repo: "This repo",
    builtin: "Built in",
  },

  via: {
    model: "Claude chose it",
    slash: "You typed /{name}",
  },

  status: {
    update: "Update available",
    current: "Up to date",
    drift: "Changed locally",
    managed: "Synced from claude.ai",
    untracked: "No update source",
    "not-installed": "Not installed",
    builtin: "Built in",
    unknown: "Can't tell",
  },

  mcpStatus: {
    connected: "Connected",
    "needs-auth": "Needs sign-in",
    failed: "Failed",
    pending: "Pending approval",
    disabled: "Off",
    unknown: "Unknown",
  },

  reasons: {
    "plugin-version": "{current} → {latest}",
    "plugin-version-stale": "{current} → {latest}. Your local marketplace copy is behind GitHub; updating refreshes it first.",
    "plugin-version-current": "{current} is the latest.",
    "plugin-commit": "Newer files in the marketplace",
    "plugin-commit-current": "Matches the marketplace.",
    "plugin-content": "Newer files in the marketplace",
    "plugin-content-current": "Matches the marketplace.",
    "plugin-no-version": "The marketplace publishes no version for this plugin.",
    "repo-newer": "The repo copy is newer than the installed one.",
    "repo-newer-account": "The repo copy is newer than the one on claude.ai. Rebuild it with ./package.sh {skill} and upload {distFile} on claude.ai.",
    "installed-newer": "The installed copy has edits the repo doesn't.",
    "installed-newer-account": "The claude.ai copy differs from the repo. Copy it back into the repo if it's the version you want.",
    "matches-repo": "Same as the repo copy.",
    "no-source": "Installed by hand, so there's nothing to compare against. List its GitHub path under updates.upstream in config.json to track it.",
    "account-managed": "Claude Code re-syncs it from claude.ai.",
    "repo-only": "In this repo but not installed.",
    "not-on-disk": "Built into Claude Code, or since removed.",
    upstream: "Compared with {repo}.",
    "upstream-unreachable": "Couldn't reach {repo}.",
  },

  actions: {
    "plugin-update": { label: "Update", running: "Updating {target}…", done: "Updated {target}.", failed: "Couldn't update {target}." },
    "plugin-uninstall": {
      label: "Remove plugin",
      running: "Removing {target}…", done: "Removed {target}.", failed: "Couldn't remove {target}.",
      confirmTitle: "Remove the {plugin} plugin?",
      confirmBody: "Skills come with their plugin, so this removes all {count} of its skills, not just {name}. You can install it again with claude plugin install {target}.",
      confirm: "Remove plugin",
    },
    "skill-uninstall": {
      label: "Uninstall",
      running: "Uninstalling {target}…", done: "Uninstalled {target}. It's in Recently removed if you want it back.", failed: "Couldn't uninstall {target}.",
      confirmTitle: "Uninstall {name}?",
      confirmBody: "The folder moves to the trash in ~/.claude/skill-usage, so you can restore it from this page.",
      confirm: "Uninstall",
    },
    "skill-update-from-repo": { label: "Update from repo", running: "Copying {target} from the repo…", done: "Updated {target}. The old copy is in Recently removed.", failed: "Couldn't update {target}." },
    "skill-install-from-repo": { label: "Install", running: "Installing {target}…", done: "Installed {target}.", failed: "Couldn't install {target}." },
    "skill-restore": { label: "Restore", running: "Restoring…", done: "Restored.", failed: "Couldn't restore." },
    "mcp-check": { label: "Check all", running: "Checking MCP servers…", done: "MCP servers checked.", failed: "Couldn't check MCP servers." },
    "mcp-login": { label: "Sign in", running: "Opened your browser to sign in to {target}. Finish there.", done: "Signed in to {target}.", failed: "Sign-in to {target} didn't finish." },
    "group-assign": { label: "Move", running: "Moving {target}…", done: "Moved {target}.", failed: "Couldn't move {target}." },
    "group-create": { label: "Create", running: "Creating {target}…", done: "Created {target}.", failed: "Couldn't create {target}." },
    bulk: { label: "Apply", running: "Working on {target}…", done: "Finished {target}.", failed: "Couldn't finish {target}." },
    manageAccount: "Manage on claude.ai",
    cancel: "Cancel",
    close: "Close",
    details: "Details",
    restartNeeded: "Restart open Claude Code sessions to pick this up.",
  },

  time: {
    justNow: "just now",
    never: "never",
  },
};

export function fill(template, values = {}) {
  return template.replace(/\{(\w+)\}/g, (_, key) => (values[key] ?? `{${key}}`));
}
