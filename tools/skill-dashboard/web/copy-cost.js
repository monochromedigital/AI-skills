// Words for the cost section. Merged into COPY by content.js.

export const COST_COPY = {
  cost: {
    kpi: { label: "API cost, last {days} days", sub: "{total} since {since}" },
    head: {
      title: "Token cost",
      period: "Period",
      all: "All time",
      summary: "{cost} at API prices · {replies} replies · {sessions} sessions",
      planMonth: "Your plan is {fee} a month. At API prices, {period} came to {ratio}× that.",
      planAll: "Your plan cost {paid} over these {months} months ({fee} a month). At API prices, the same work came to {ratio}× that.",
    },
    note: "At Anthropic API list prices (as of {asOf}). Your plan bills a flat fee; this is what the same work would cost if paid per token on the API.",
    leftOut: "Leaves out {label} ({paths}), set in config.json under costLeaveOut.",
    series: { day: "Cost per day", month: "Cost per month", caption: "API list prices · {period}", tooltip: "{date} · {cost}", empty: "No usage in this period." },
    projects: { title: "Cost by project", caption: "{period} · click a project to see its skills", tooltip: "{cost} · {tokens} tokens · {sessions} sessions", empty: "No project costs in this period." },
    sessions: {
      title: "Most expensive sessions", caption: "{period}, top {count}",
      meta: "{project} · {replies} replies · {tokens} tokens", untitled: "Untitled session", empty: "No sessions in this period.",
    },
    kinds: {
      title: "Where the cost goes", caption: "{period}",
      labels: { cacheRead: "Re-reading context", cacheWrite: "Caching context", output: "Claude's replies", input: "New input" },
      tooltip: "{cost} · {share} of the total",
      explain: "Each reply re-sends the whole conversation; caching makes that cheap but not free, which is why long sessions cost the most.",
    },
    unpriced: "{count} replies used models with no listed price and aren't included: {models}.",
  },
};
