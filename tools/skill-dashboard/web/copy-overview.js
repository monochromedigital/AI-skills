// Words for the two pages (Overview and Skills), the page tabs, and the
// Overview's cost tiles and skills snapshot. Merged into COPY by content.js.

export const OVERVIEW_COPY = {
  nav: { label: "Pages", overview: "Overview", skills: "Skills" },
  views: {
    overview: { title: "Overview", lede: "What your Claude Code work would cost at API prices, and a snapshot of your skills." },
    skills: { title: "Skills", lede: "Every skill on this Mac, how often Claude reaches for it, and the tools to manage them." },
  },
  costKpi: {
    week: { label: "Last {days} days", up: "+{delta} on the {days} days before", down: "−{delta} on the {days} days before", flat: "Same as the {days} days before" },
    month: { label: "{month} so far", sub: "{ratio}× your {fee} plan", subNoPlan: "at API prices" },
    all: { label: "All time", sub: "since {since}" },
    cloud: { label: "Cloud sessions", sub: "{share} of {month}", none: "None recorded yet; see the README to set them up" },
  },
  snapshot: {
    title: "Skills",
    summary: "{installed} installed · {used} used · {uses} uses in the last {days} days",
    updates: "Updates ready to install: {count}",
    mcp: "MCP servers that need attention: {count}",
    manage: "Manage skills",
  },
};
