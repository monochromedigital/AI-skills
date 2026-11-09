// Words for the cost section. Merged into COPY by content.js.

export const COST_COPY = {
  cloudGuide: {
    title: "Add a cloud environment",
    intro: "Each cloud environment reports its usage only after these settings are added. claude.ai can't copy them to new environments, so do this every time you make one.",
    steps: [
      "On claude.ai/code, stay on the new-session screen and open the environment menu: the first control under the message box.",
      "Find the environment under Cloud (or More), hover it and click its gear icon. For a brand-new one, choose New environment.",
      "Environment variables: keep what's there and add the lines from {file} on your Mac (they hold the upload key). Change the last line to the environment's name, with no spaces. Save changes.",
      "Network access: if it's Limited, add {host} on its own line and keep Allow package managers ticked. Full needs nothing. Save changes.",
      "Run any short session in it. After the next sync (every morning, or Check for updates on the Mac) it appears in Cloud environments with its last report.",
    ],
    check: "If an environment you've used never appears in Cloud environments, it's missing these settings.",
    skill: "On your Mac you can also ask Claude: \"set up cloud tracking for <environment>\". The cloud-env-tracking skill does these steps in the browser and checks them.",
    close: "Close",
  },
  cost: {
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
      meta: "{project} · {replies} replies · {tokens} tokens", untitled: "Untitled session", cloud: "Cloud session", empty: "No sessions in this period.",
    },
    kinds: {
      title: "Where the cost goes", caption: "{period}",
      labels: { cacheRead: "Re-reading context", cacheWrite: "Caching context", output: "Claude's replies", input: "New input" },
      tooltip: "{cost} · {share} of the total",
      explain: "Each reply re-sends the whole conversation; caching makes that cheap but not free, which is why long sessions cost the most.",
    },
    environments: {
      title: "Cloud environments", caption: "{period} · every environment that has reported", howTo: "How to add one",
      meta: "{sessions} sessions · last report {when}", metaOne: "1 session · last report {when}", unnamed: "Unnamed environment",
      empty: "No cloud environment has reported yet. Each one needs the settings in How to add one.",
    },
    unpriced: "{count} replies used models with no listed price and aren't included: {models}.",
  },
};
