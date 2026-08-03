# Capturing the site

Three routes, in order of preference. Try each until one works — do not ask the
user to choose unless all three fail.

## Route A — Claude in Chrome (the user's own browser)

Best route in a cloud session, and the only one that reaches staging sites,
intranets, and anything behind a login. The user's browser is already
authenticated.

1. `list_connected_browsers`, then **ask the user which browser to use** via
   AskUserQuestion — list every browser as its own option, plus the exact option
   "Open a confirmation screen in every connected Chrome extension and let me
   select the right one there." This ask is mandatory.
2. `tabs_create_mcp` for a fresh tab, then `navigate`.
3. Run the inventory script with `javascript_tool`. Paste the body of
   `PAGE_JS` from `scripts/capture.py` — it is written to run standalone and
   returns sections, element boxes, and technical evidence as one object.
4. Screenshot each section: `computer` with `action: "scroll_to"` using the
   section's coordinates, then `action: "screenshot"`. Save with
   `save_to_disk: true` so the PNG lands in the workspace.
5. For mobile, `resize_window` to 390×844 and repeat for the key pages.

Chrome captures the **viewport**, not arbitrary element clips, so scroll each
section to the top of the screen before shooting. Sections taller than the
viewport need two shots or a narrower section definition.

## Route B — Playwright in this workspace

Fully automatic and produces exact element clips, but only works where the
environment can reach the site. **The Anthropic cloud sandbox routes egress
through an allowlist proxy and cannot reach general websites** — a `goto` there
fails with `ERR_TUNNEL_CONNECTION_FAILED`. This route works when the task is
running on the user's own computer, or when the target is allowlisted.

```bash
python3 scripts/capture.py --url https://example.com --out ./audit
python3 scripts/capture.py --url https://a.com/x --url https://a.com/y --out ./audit
python3 scripts/capture.py --url https://example.com --crawl 6 --out ./audit
```

Writes `audit/screens/*.png` and `audit/page-data.json`. Test reachability
first with a cheap `WebFetch` — if that fails too, fall back to Route A.

## Route C — HTML only

No visuals. `WebFetch` the pages and assess markup and copy. Findings are
limited to Copy/Content, SEO, and some Development; UI, UX detail, and visual
Accessibility cannot be judged honestly without seeing the page.

Say so plainly in the deck rather than guessing: add a note to the summary that
the audit was performed on markup only, and skip the section screenshots.
Never invent a visual finding from HTML alone.

## Framing the screenshots

Once the raw PNGs exist:

```bash
python3 scripts/frame.py --in-dir audit/screens --out-dir audit/framed --device tablet
```

Devices: `tablet` (matches the reference deck), `phone`, `laptop`, `plain`.
Prints a `screen_rect` per image — copy each into the matching slide entry in
`findings.json` so markers land correctly.

Sections taller than 1.6× their width are cropped from the top by default
(`--max-h-ratio`); the finding text carries what is below the fold.

## What page-data.json gives you for free

Do not hand-check things the capture already measured. `technical` per page
carries: contrast failures with ratios and the elements affected, images
missing alt, oversized images, heading outline and level skips, `h1` count,
title and meta description lengths, canonical, `lang`/`dir`, structured data
types, vague link text, unlabelled form fields, suppressed focus outlines,
small tap targets, load timing, transfer weight, and the heaviest resources.

Turn each into a finding with the number attached. That is where the audit's
authority comes from — a client can dismiss "the contrast looks low"; they
cannot dismiss "2.14:1 against a 4.5:1 minimum, on 23 elements".

## Choosing sections

The capture splits pages automatically, but review the result before writing
findings. Good sections are what a person would name when describing the page:
Nav Bar, Hero, Services, Testimonials, Contact, Footer. Merge auto-detected
sections that are really one thing, and split any that are doing two jobs.
Rename them in `findings.json` — the auto-labels are a starting point.
