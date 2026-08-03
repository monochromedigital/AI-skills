# Content publishers

News sites, magazines, trade media, blogs, and documentation sites.

**Conversion here** is attention converted into return: a second article read,
a newsletter signup, a subscription, or an answered question in the case of
docs. The economics are ad impressions, subscriptions, or support deflection —
establish which before writing, because the findings differ sharply.

The distinctive tension on this type is that the business model actively
degrades the experience. Auditing it honestly means naming that tradeoff
rather than pretending ads and paywalls should not exist.

## What must be captured

1. Homepage / front page
2. **An article page** — a long one, with the full ad and interstitial load
3. A second article reached from the first, to test the onward path
4. A category or section index
5. Search results for a real query
6. The paywall or registration wall, at the moment it appears
7. Newsletter signup, wherever it lives
8. Author page and an archive page
9. Article page at 390×844 mobile — this is where most of the audience is
10. For docs: the getting-started page, a deep reference page, and search

## The article page

This is the product. Almost all the value in a publisher audit is here.

- Time to first readable paragraph, measured. Layout shift from late-loading
  ads is the defining failure of this type — cite CLS against the 0.1 threshold
- Ad density and placement: count units above the fold, and whether any
  ad sits inside the reading column in a way that interrupts a sentence
- Sticky elements — header, video player, newsletter bar, consent banner —
  measured as a percentage of mobile viewport lost. Above roughly a third,
  raise it
- Typography actually readable: measure line length, line height, and body
  size. A 15px body at 110% line height across a 90-character line is a real,
  quantifiable finding
- Publish date *and* update date visible; for news, the absence of a date is
  Critical
- Author identified with credentials where the subject warrants it
- The onward path: related articles relevant rather than algorithmic filler,
  and placed where a reader who finished actually is
- Interruptions ordered sanely — consent, then paywall, then newsletter, never
  three modals stacked

## Paywall and registration

- The wall's rules are stated: how many free articles, what a subscription costs
- Price shown before the signup form
- The cut point is not mid-sentence — an abrupt truncation reads as a bug
- Google's requirements for paywalled content markup are met, or the article
  will be treated as cloaking
- Cancellation route as easy to find as the subscribe route. Where it is not,
  say so plainly; in several jurisdictions this is now a legal requirement

## Documentation sites

Treat separately if the site is docs rather than editorial:

- Search is the primary navigation; test it with an error message string
- Every page states which version it applies to
- Code samples copyable, complete, and runnable as written
- The getting-started path reaches a working result without leaving the page
- Deep links to headings are stable — docs are linked from support tickets
- A "was this helpful" route that actually goes somewhere
- Reference and tutorial content are distinguishable, not interleaved

## Type-specific notes per category

**Copy / Content** — headlines describe rather than bait; a gap between
headline promise and article content is a trust finding. Check for orphaned
content: articles reachable from nowhere but search.

**UX Design** — reading is the task. Anything that competes with the reading
column is measured against it. Test the back button behaviour on infinite
scroll, which routinely strands readers.

**UI Design** — consistency across article templates. Publishers accumulate
five article layouts over a decade; the inconsistency is the finding.

**Development** — third-party scripts are the performance story. Count them,
identify the heaviest, and separate first-party weight from ad-tech weight so
the client can see what is actually theirs to fix. Check lazy loading below
the fold and whether the ad slots reserve space.

**SEO** — `Article` / `NewsArticle` structured data with author and dates;
canonical handling for syndicated content; archive pagination crawlable;
author `sameAs` for E-E-A-T signals. Check whether AI crawlers are permitted
or blocked in `robots.txt` — an explicit decision either way is fine, an
accidental one is a finding.

**Accessibility** — video captions, audio transcripts, and heading structure
in long articles. Ad iframes trapping keyboard focus is common and rarely
tested. Data visualisations need a text alternative carrying the same finding.

**CRO** — for subscription publishers, the newsletter is the funnel, not the
subscription. Check where the signup appears relative to where readers finish.

## Severity calls specific to publishers

Treat as **Critical**:

- Layout shift that moves the text a reader is currently reading
- Publish date absent on news or time-sensitive content
- Consent, paywall, and newsletter modals stacking on first visit
- Ads consuming the majority of the mobile first viewport
- Sponsored content not labelled as such
- Docs: a getting-started path that does not work as written

## Benchmarks to look up live

- Current Core Web Vitals thresholds and how the client's pages score in real
  user data — CrUX is public. LCP ≤2.5s, INP ≤200ms, CLS ≤0.1 at the 75th
  percentile are the current bars; confirm before citing
- Newsletter signup conversion benchmarks for the client's category
- Subscription paywall meter benchmarks, if the client operates one
- Two comparable publishers: capture their article pages and compare ad
  density and time-to-content side by side
