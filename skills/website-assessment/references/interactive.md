# The interactive web report

Two scripts turn the project folder into a browsable report: the audit
annotated on the page itself, filterable, and linkable finding by finding.

It exists because the deck and the report do different jobs. The deck is for
the meeting — linear, presented, one section per slide. The report is for the
week after the meeting, when a developer wants only the Development findings,
a designer wants only the Critical ones, and someone wants to send a colleague
a link to finding 7 without attaching a 40 MB file.

```bash
python3 scripts/build_data.py --project audit/
python3 scripts/build_site.py --project audit/ --out audit/out/report.html
python3 scripts/build_site.py --project audit/ --out audit/out/report/ --mode folder
python3 scripts/build_site.py ... --cost-bands "S=\$500-1k,M=\$1-3k,L=\$3k+"
python3 scripts/build_site.py --project audit/ --no-ia --out audit/out/report.html
```

## Why it is three files

`render_report.py` holds every line of CSS, JS and HTML, and is carried
**byte-identically** by `sitemap-ia-board` too. `build_site.py` here and
`build_board.py` there are thin wrappers around it. An audit report and a
greenfield IA board are the same document with different sections present; the
moment they were two codebases they started looking like two agencies.

## Why the data step is separate

`build_data.py` reads `project.json`, `findings.json` and the screenshots and
writes `report-data.json`. `build_site.py` reads that, plus `ia.json` if it
exists, hands both to the renderer, and writes the HTML. Neither writes its own
input — project contract §4.

The split is not tidiness. The two halves fail differently. A screenshot path
that does not resolve, a marker outside the image, a finding with no id: those
are data problems, and they belong where the error can name the JSON path.
Routing, degradation and layout are rendering problems. Before the split, a
mistyped screenshot path surfaced as an empty panel in a report that had
already been sent.

`build_site.py` validates every cross-reference before it writes anything, and
on failure exits non-zero listing each problem by path, having written nothing.
A half-valid report is worse than no report, because it gets sent.

No framework, no build step, no network calls at runtime. Urbanist is embedded
from `assets/fonts/` as base64 so the file renders correctly on a machine that
has never heard of the typeface. Every colour, category name and severity
colour is read from `assets/brand.json` — same rule as the other scripts, never
hard-code a hex value.

It consumes the **raw** screenshots, not the framed PNGs. The report draws its
own browser chrome, so `frame.py` output is only needed for the deck. Where a
slide has only a framed image, marker coordinates are mapped through its
`screen_rect` automatically, so pins still land correctly either way.

## The views

Hash-routed, so the whole report is one file with several addresses.

**Four views** when the folder has only `findings.json`. Personas and Sitemap
slot in between Summary and Action items when `sitemap-ia-board` has left an
`ia.json`, and Database and Glossary follow them when that file carries a
content model or a term list. Eight is the maximum; nothing is padded to reach
it.

In the four-view build the two extra tabs and their Home cover cards are
**removed from the DOM**, not greyed out. A tab a user can see is a tab they
expect to work, and one that opens an empty view reads as a broken report —
which is the impression this document exists to avoid. `#/personas` on a
four-view build resolves to Home rather than rendering nothing, because people
paste links.

**Home** (`#/home`) — client, URL, date, and the headline counts: pages
audited, screens captured, findings, criticals. Three cards into the rest.

**Audit** (`#/audit/<page>`) — the annotated walkthrough, and the reason the
report exists. Left rail lists the pages with their finding counts. The centre
stacks that page's screenshots inside a browser frame with numbered pins
positioned from the existing `marker.x` / `marker.y` fractions. The right rail
carries the matching finding cards, in the same order and with the same
numbers as the pins.

**Summary** (`#/summary`) — the narrative paragraphs, the per-category counts
grid, a severity bar, and an at-a-glance metrics table.

**Personas** (`#/personas`, with `ia.json`) — who the site is for, each with a
weight badge stating the evidence behind them, a pull quote, what they need,
what stops them today, and their route through the proposed sitemap. Every
blocker that an audit finding explains carries that finding's id and expands to
show it.

**Sitemap** (`#/sitemap`, with `ia.json`) — the proposed architecture as page
columns of section cards, with the named funnels above it, discipline chips
(UX / CRO / SEO / LEAD) and a Phase 2 toggle as filters, and an evidence
expander on any card whose existence an audit finding justifies.

**Action items** (`#/actions`) — every fix, ordered by severity then effort,
split into tracks when the client asked for it, with a CSV export built in the
browser from a Blob. Each item links back to its pin on the page.

The Personas and Sitemap views never store a copy of the audit's words. They
hold the finding's id and resolve it at render time, so rewording a finding can
never leave the two documents quietly disagreeing (contract §7).

## Interaction rules

- Hover a pin → floating finding card. Click → locks it and highlights the
  matching card in the rail. Clicking a rail card scrolls its pin into view and
  flashes it. Esc clears. Up/Down arrows step pin to pin.
- **Hover is never the only route to content.** It fails on touch, and it fails
  on anyone presenting from a tablet. Click must always work, and the tooltip
  is suppressed entirely below 820px and on coarse pointers.
- Filter chips for all seven categories and three severities, plus track when
  the data carries one. Non-matching pins dim to 16% and stop taking pointer
  events rather than disappearing — the page still has to read as a page, and a
  screenshot with holes punched in it reads as a bug.
- Filter state and the focused finding live in the URL:
  `#/audit/<page>/<findingId>?sev=Critical&cat=CRO`. Any filtered view, and any
  single finding, is a shareable link.
- Responsive: rails unstick and stack below 1000px, the header nav scrolls
  horizontally below 820px, and the hover tooltip is suppressed on small screens.

Track, effort and cost pills appear only on the action-items view. On the
walkthrough they crowd out the finding itself.

## The two delivery modes

**`inline` (default)** — one self-contained `.html`. Images become data URLs,
fonts are embedded, and the file opens from a `file://` URL with no server and
no internet. Roughly 1 MB per 6 screens. This is the right choice for emailing
a prospect, because it survives being forwarded and cannot break.

**`folder`** — `index.html`, `assets/*.png`, and a `robots.txt`. Images are
separate files loaded lazily, so the initial paint is fast regardless of how
many screens there are. This is the only viable mode above about 20 screens.
Upload the folder to a subdomain; it is static files, so any host will do.

The script warns on stderr when an inline build exceeds 20 screens. Believe the
warning — a 30 MB HTML file technically works and is miserable to open.

## Hosting and privacy

These reports are usually about a company that has not hired the agency yet.
Treat the URL as sensitive.

- `<meta name="robots" content="noindex,nofollow,noarchive,nosnippet">` is
  always emitted, and the folder build also writes a `robots.txt` with
  `Disallow: /`
- Static files only. There is no server component, no analytics, and no
  outbound request at runtime — nothing phones home from a prospect's browser
- Use an unlisted URL, not a guessable one: `/r/8f2c-northgate/`, not
  `/clients/northgate/`
- Neither measure is access control. If the contents are genuinely sensitive,
  put the folder behind basic auth or send the inline file instead

## Verifying before delivery

Same standard as the deck: build it, open it, look at it. Open the built file
in Chromium via Playwright and screenshot every view, then check:

- Pin numbers match card numbers, per section
- Pins sit on the element each finding describes
- Filters change the visible counts correctly
- A deep link restores both filter state and focus
- Exactly one nav tab is active on every view, and still exactly one after
  repeated re-renders
- Every route cold-loads directly, not just by clicking through from Home
- No console errors
- The mobile layout does not overflow (`scrollWidth - clientWidth` is 0)

Fix and rebuild until clean.

## Two bugs worth knowing about

Both were hit building this, and both are silent.

**`classList.toggle(cls, force)` with `force` evaluating to `undefined` does
not clear the class** — it falls back to a plain flip. Chaining `||`
expressions to compute the force argument is how a report ends up with two
active nav tabs after a re-render, or none. Compare an explicit view key
instead.

**View functions defined in a later block than the initial `render()` call.**
A cold load straight to that view dies in the temporal dead zone before it
paints anything, while clicking through from Home works fine — so it survives
casual testing and fails for whoever you sent the deep link to. Call `render()`
last, after every view function is defined, and cold-load every route when
verifying.
