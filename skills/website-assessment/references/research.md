# Live research

**This step is not optional.** Every audit browses the live internet twice:
once to see the client's site as a real browser renders it, and once to gather
the external evidence that turns opinions into findings.

An audit written from training data is out of date on the day it ships. WCAG
minor versions, Core Web Vitals metrics, structured-data requirements,
platform conventions, and every conversion benchmark move. A client who
checks one stale number stops trusting the whole deck.

## Part 1 — the site must be seen live

The audit is a visual assessment of a running website. Assessing from memory,
from a description, or from a cached copy is not permitted.

Route A (Claude in Chrome) and Route B (Playwright) both satisfy this. Route C
(WebFetch, markup only) **does not** — it produces no visual evidence.

If only Route C is available:

1. Say so before writing anything, and get the user's explicit agreement to
   continue on that basis
2. Write only Copy/Content, SEO, and markup-level Development findings
3. Put a stated limitation on the summary slide: the audit was performed on
   markup only, UI and visual accessibility were not assessed
4. Never write a visual finding. "The hero image is low contrast" from HTML
   alone is a fabrication, and it is the fastest way to lose a client

Never present an audit as complete when the site was never rendered.

## Part 2 — external research, before findings are written

Run this after capture and after the site type is confirmed, so the searches
are specific. Budget four to eight searches; more is usually padding.

### What to look up every time

1. **The client's vertical conversion benchmark.** Not the global average —
   the average for their industry and their site type. The gap between their
   likely performance and their sector's median is the business case for the
   whole engagement.
2. **The standards the findings cite.** Confirm the current WCAG version and
   level, the current Core Web Vitals metrics and thresholds, and any
   structured-data requirement before quoting it. These change.
3. **Regulation that applies to this client.** Accessibility duties for public
   bodies, price-disclosure rules for travel and ecommerce, subscription
   cancellation law, cookie consent, sector-specific advertising rules. A
   compliance finding outranks a usability finding in every client meeting.
4. **Two or three named competitors.** Capture the equivalent page from each —
   the pricing page, the PDP, the service page, the donation flow. A
   side-by-side is more persuasive than any statistic, because the client
   cannot argue that their competitor does it differently.
5. **Platform-specific guidance**, if the site runs on a known platform.
   Shopify, HubSpot, Webflow, WordPress, and Squarespace all have known
   performance and structure ceilings; knowing which are fixable and which are
   platform limits stops you recommending the impossible.

The site-type file lists what to look up for that type specifically. Read it
first, then search.

### Where to take numbers from

Prefer, in this order:

1. The standards body or platform owner — W3C, web.dev, Google Search Central,
   the relevant regulator
2. A named research organisation with a stated methodology — Baymard, NN/g,
   CrUX, official industry association reports
3. A vendor benchmark report with a stated sample size and date

Reject: undated statistics, listicles aggregating other listicles, any figure
you cannot trace to a study, and anything whose source is another AI summary.
The tell is a number that appears everywhere with no original.

### How a researched number enters a finding

The number is evidence for a finding you already made from looking at the
page. It is never the finding itself.

Wrong — a statistic wearing a finding's clothes:

> 70% of carts are abandoned, so the checkout needs work.

Right — an observation, its consequence, and the evidence that sizes it:

> Shipping cost first appears at step three of checkout, after the visitor has
> entered their address. Extra costs revealed late are the most-cited reason
> for cart abandonment, named by 40% of abandoning shoppers.

Rules:

- One researched number per finding at most; two makes it a lecture
- Attribute in the `benchmark` field, not in the observation sentence — it
  renders as its own line and keeps the finding readable
- Name the source and the year: `Baymard Institute, 2026 — 50-study average`
- Never state the client's own conversion rate unless they gave it to you
- Never imply a fix will produce a specific uplift. "Sites that do X see 30%
  more Y" is correlation, and the client will hold you to it

### Recording sources

Keep a `research.json` next to `findings.json` while you work:

```json
[
  { "claim": "70.22% average documented cart abandonment",
    "source": "Baymard Institute — Cart Abandonment Rate list",
    "url": "https://baymard.com/lists/cart-abandonment-rate",
    "checked": "2026-08-03" }
]
```

It is not rendered into the deck, but when a client challenges a number in the
meeting, having the URL is the difference between authority and a retraction.

## Part 3 — competitor capture

Treat competitor pages as a capture job, not a search job. Open the page, look
at it, screenshot the equivalent section. A competitor comparison built from
descriptions rather than screenshots is worth very little, and it shows.

Two competitors is enough. Three if the client named three. Capture the *same*
page type you are criticising on the client's site so the comparison is fair —
comparing the client's homepage to a competitor's product page is a cheap shot
a client will spot.

Frame competitor findings as evidence, never as instruction. "Their pricing
page states the annual saving in the toggle" is useful. "You should copy their
pricing page" is not advice anyone pays for.
