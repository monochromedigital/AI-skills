// Words for the cost section. Merged into COPY by content.js.

export const COST_COPY = {
  cost: {
    kpi: { label: "API cost, last {days} days", sub: "{total} since {since}" },
    note: "At Anthropic API list prices (as of {asOf}). Your Claude plan bills a flat fee; this is what the same work would cost on the API.",
    daily: { title: "Cost per day", caption: "API list prices · last {days} days", tooltip: "{date} · {cost}", empty: "No usage in this window." },
    projects: { title: "Cost by project", caption: "All time · click a project to see its skills", tooltip: "{cost} · {tokens} tokens · {sessions} sessions", empty: "No project costs yet." },
    sessions: {
      title: "Most expensive sessions", caption: "All time, top {count}",
      meta: "{project} · {replies} replies · {tokens} tokens", untitled: "Untitled session", empty: "No sessions yet.",
    },
    kinds: {
      title: "Where the cost goes", caption: "All time",
      labels: { cacheRead: "Re-reading context", cacheWrite: "Caching context", output: "Claude's replies", input: "New input" },
      tooltip: "{cost} · {share} of the total",
      explain: "Each reply re-sends the whole conversation; caching makes that cheap but not free, which is why long sessions cost the most.",
    },
    leftOut: "Leaves out {label} ({paths}), set in config.json under costLeaveOut.",
    unpriced: "{count} replies used models with no listed price and aren't included: {models}.",
  },
};
