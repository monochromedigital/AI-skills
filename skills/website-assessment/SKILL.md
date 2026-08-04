---
name: website-assessment
description: Run a live, section-by-section UX/UI/SEO/accessibility audit of a website, typed to the kind of site it is (ecommerce, SaaS, service, corporate, publisher, marketplace, nonprofit/education), and deliver it as an interactive web report, a Crackwits-branded PPTX deck, and/or Figma slides — numbered markers pinned to the exact elements, category tags, severity, fixes, benchmarks and counts. Use this whenever the user asks to assess, audit, review, critique, analyse, evaluate, or "look at" a website or page — including "what's wrong with this site", "review this landing page", "audit my store/checkout", "review our pricing page", "check this site for accessibility", "do a UX audit", "assess a competitor's site", "prepare a website review for a client", or when they share a URL and want an opinion on it. Also use when they ask for a website assessment deck, site audit slides, or a UX/UI report. Trigger even if they never say "audit" or "deck" — a request to evaluate any live website is this skill.
---

# Website Assessment

Produces the Crackwits "Website UX/UI Assessment" deck: one slide per page
section, a device-framed screenshot with numbered markers pinned to the exact
element in question, matching numbered finding cards tagged by discipline, and
a summary slide with a narrative diagnosis plus counts per category.

Two rules govern the whole workflow:

**The site is always browsed live.** Never assess from memory, from a
description, or from markup alone without saying so. See `references/research.md`.

**The audit is always typed.** A generic checklist produces a generic audit.
Identify what kind of site this is and audit it as that kind of site. See
`references/site-types/`.

## Before starting, confirm four things

Use AskUserQuestion unless the session is unattended. All four go in **one**
call, not four.

1. **Project folder** — every run works inside one folder per client, and
   everything it produces goes inside it. Default the name to a slug of the
   client (`Northgate Logistics` → `northgate-logistics`) and confirm the
   parent directory rather than assuming the working directory. **If the folder
   already exists, reuse it** — never `-2`, never a fresh one because the last
   run was a while ago. A second folder is how a client ends up with two
   sitemaps and no way to tell which is current. Read
   `references/project-contract.md` §1–§2 first: if `project.json` is already
   in the folder, the client, URL, market, audience and languages are settled
   and you do not ask for them again
2. **Which pages** — a single page, the decisive journey for this kind of site
   (the site-type file lists it), or the whole site
3. **Audience** — prospect, existing client, or internal scoping. This changes
   framing and finding count, not the findings themselves (see `references/voice.md`)
4. **Output** — four options:
   - **Interactive web report (HTML)** — a filterable, browsable report with the
     annotations pinned onto the page screenshots
   - **PPTX deck** — the existing Crackwits assessment deck
   - **Both** — deck for the meeting, web report for the follow-up
   - **Figma slides** — the existing plugin route

When the interactive report is chosen, ask two follow-ups **in the same
AskUserQuestion call** rather than coming back a second time:

- **Delivery** — a single self-contained HTML file (images inlined, works
  offline, roughly 1 MB per 6 screens) or a folder to upload to a subdomain
  (images as separate lazy-loaded files; the only viable option above ~20 screens)
- **Action items depth** — prioritised list only, effort sizing (S/M/L), a
  now-vs-revamp track split, or cost bands. Multi-select

Also ask for the client's two or three main competitors if the user has not
named them. They feed the research step and produce the deck's most persuasive
slide.

Do not ask about categories or severity. Those are fixed. Do not ask for the
site type — detect it in step 2 and confirm it, which is cheaper for the user
and more accurate.

## Workflow

### 1 · Capture

Read `references/capture.md` and pick a route. In a cloud session the sandbox
cannot reach general websites, so **Claude in Chrome is the primary route** —
it uses the user's own browser and reaches authenticated and staging sites.
Playwright (`scripts/capture.py`) is fully automatic where the network allows.
HTML-only via WebFetch is a declared-limitation fallback, not a normal route:
if you end up there, get the user's agreement and flag it on the summary slide.

Capture the homepage first — it carries the signals you need to type the site.

Then frame the screenshots:

```bash
python3 scripts/frame.py --in-dir audit/screens --out-dir audit/framed --device tablet
```

Keep the `screen_rect` it prints for each image.

### 2 · Identify the site type, then capture its journey

Read `references/site-types/README.md` and match the captured pages against
the signal table. Confirm the detected type with the user in one question,
stating the signal that drove it. In an unattended session, proceed and state
the assumption on the summary slide.

Then read the matching type file and **go back and capture what it requires**.
This is the step that makes the audit worth paying for. An ecommerce audit
that never opens the cart, or a SaaS audit that never toggles the pricing page
to annual, is a homepage review with a longer title.

### 3 · Research

Read `references/research.md`. Confirm the standards you are about to cite,
look up the vertical benchmark, check what regulation applies, and capture the
equivalent page from two competitors. Record sources in `research.json` as you
go.

Do this before writing, not after — research done afterwards becomes
decoration attached to findings that were already written.

### 4 · Look before writing

Actually **Read the screenshots**. This is a visual audit; findings written
without looking at the page are worthless and obvious to the client.

Then read `page-data.json` for the measured evidence — contrast ratios, alt
coverage, heading outline, form labels, load timing, tap targets. Every number
there is a finding you do not have to argue for.

### 5 · Write the findings

Read `references/categories.md` for what to look for per category and how to
assign severity, then the site-type file for what that checklist cannot know,
and `references/voice.md` for how findings are phrased. If the
`psychology-of-design` skill is available, read it before writing UX and CRO
findings so principle citations are accurate rather than decorative.

Work section by section, in page order, and cover the type's decisive journey
even where it is unglamorous — the checkout and the pricing page carry more
value than the hero.

For each section ask: what is this section for, and what stops it doing that job?

Write `findings.json` into the project folder, per `references/schema.md`. The
essentials:

- 1–3 category tags per finding, never more
- Observation → consequence → fix, in that order, in that voice
- A number wherever a number exists
- A `benchmark` line only where researched evidence genuinely sizes the finding
- `track` and `effort` on every finding **only when** the action-items depth
  asked for them (see `references/schema.md`)
- `marker.x` / `marker.y` as fractions of the screenshot, taken from the `rel`
  boxes in `page-data.json`
- Severity used with discipline — roughly 10–20% Critical, plus whatever the
  type file marks Critical for this kind of site

Then the summary narrative: three short paragraphs, diagnosis → pattern →
gaps. The counts grid is generated automatically.

Then stamp the ids. Every finding needs one before anything can reference it:

```bash
python3 scripts/finding_ids.py --findings <project>/findings.json
```

### 6 · Build

Branch on the chosen output. Capture, framing and finding-writing are shared —
never duplicate them per output, and never fork `findings.json`.

**Interactive web report** — two steps, because the generator and the renderer
fail differently. `build_data.py` catches data problems and names the JSON path;
`build_site.py` catches routing and reference problems and refuses to write a
partial file.

```bash
python3 scripts/build_data.py --project <project>
python3 scripts/build_site.py --project <project> --out <project>/out/report.html
python3 scripts/build_site.py --project <project> --mode folder --out <project>/out/report/
```

Add `--cost-bands "S=...,M=...,L=..."` when cost bands were requested. If
`ia.json` is in the folder — the `sitemap-ia-board` skill has run on this
project — the report builds six views instead of four, adding Personas and
Sitemap. `--no-ia` forces the four-view build. Read
`references/interactive.md` first. Note it consumes the **raw** screenshots,
not the framed PNGs.

**PPTX:**

```bash
python3 scripts/build_deck.py --findings <project>/findings.json --root <project> \
    --out <project>/out/assessment.pptx
```

**Figma:** hand the user `findings.json` and the framed PNGs, and point them at
`references/figma-setup.md`. The plugin cannot be run remotely — Figma's REST
API and MCP connector are read-only, so only a plugin running in their desktop
app can create the slides. Send the `figma-plugin/` folder if they have not
installed it yet.

### 7 · Verify before delivering

Non-negotiable, for whichever output was built.

**Web report** — open the built file in Chromium via Playwright and screenshot
every view at desktop (1440) and mobile (390) width, then check:

- Pin numbers match card numbers, per section
- Pins sit on the element each finding describes
- Filters change the visible counts correctly
- A deep link (`#/audit/<page>/<id>?sev=Critical&cat=CRO`) restores both filter
  state and focus
- **Exactly one** nav tab is active on every view, and still exactly one after
  repeated re-renders
- No console errors
- Every route cold-loads directly — navigate straight to each `#/…` on a fresh
  page rather than clicking through from Home
- The mobile layout does not overflow — `scrollWidth - clientWidth` is 0 at 390px

With `ia.json` present, also check the two extra views: the evidence expander
on a section card opens the finding its `fid` names, the discipline chips and
the Phase 2 toggle change the visible section count, and the board scrolls
cleanly at mobile width.

**PPTX** — convert and look at every slide:

```bash
soffice --headless --convert-to pdf assessment.pptx --outdir render
pdftoppm -png -r 90 render/assessment.pdf render/slide
```

Read the rendered PNGs and check:

- No text overflowing its card, no clipped tag pills
- Markers sit on the element each finding describes — this is the most common
  failure, and the most visible one
- Marker numbers on the screenshot match the card numbers
- Category counts on the summary reconcile with the findings
- Every benchmark cited has a source recorded in `research.json`
- Nothing colliding with the footer

Fix and rebuild until it is clean. Then deliver with SendUserFile.

## The seven categories

Copy / Content · UX Design · UI Design · Development · SEO · Accessibility · CRO

Colours, selection rules, and per-category checklists are in
`references/categories.md`; what each means for a specific kind of site is in
`references/site-types/`. Colours and layout live in `assets/brand.json` —
edit that file, never hard-code a value in a script.

## Files

| Path | What it is |
|---|---|
| `assets/brand.json` | Colours, type scale, layout fractions. Single source of truth |
| `assets/fonts/` | Urbanist TTFs (OFL) for installing locally |
| `scripts/capture.py` | Playwright capture — sections, element boxes, technical evidence |
| `scripts/frame.py` | Wraps screenshots in the device frame, reports `screen_rect` |
| `scripts/finding_ids.py` | Stamps stable ids into findings.json. The only script that writes it |
| `scripts/build_deck.py` | findings.json → PPTX |
| `scripts/build_data.py` | project folder → report-data.json (the renderer's input) |
| `scripts/build_site.py` | report-data.json + optional ia.json → interactive web report |
| `figma-plugin/` | Figma plugin: same slides, native Figma frames |
| `references/project-contract.md` | The shared agreement with the other project skills |
| `references/capture.md` | The three capture routes, and what the data gives you |
| `references/interactive.md` | The web report: views, interactions, delivery modes, hosting |
| `references/site-types/` | Detection, and the type-specific audit for each kind of site |
| `references/research.md` | The mandatory live-browsing and benchmark research step |
| `references/categories.md` | Category definitions, checklists, severity, principles |
| `references/voice.md` | How findings are phrased; audience variants |
| `references/schema.md` | findings.json contract and marker coordinates |
| `references/figma-setup.md` | Plugin install and use |

## Things that go wrong

**Auditing the homepage and calling it a site audit.** The homepage is rarely
where the value is. On ecommerce it is the PDP and checkout; on SaaS it is
pricing and signup; on a service site it is the service page and the enquiry
form. If the deck is 80% homepage slides, step 2 was skipped.

**Applying the wrong type.** Findings about a checkout on a site with no
checkout destroy credibility instantly. If the type is genuinely unclear,
audit against `categories.md` alone and say so.

**Markers in the wrong place.** They are fractions of the *screenshot*, not the
framed PNG and not the slide. `screen_rect` from `frame.py` does the mapping —
if you omit it, every marker shifts by the bezel width.

**Inlining a report that should have been a folder.** Above roughly 20 screens
the single-file build produces an HTML file too heavy to open comfortably —
data URLs are ~33% larger than the PNGs they encode, and the browser parses all
of it before painting anything. `build_site.py` warns on stderr when it happens;
rebuild with `--mode folder` rather than sending it anyway.

**A second project folder.** The client already has a folder; a later run
creates `client-2` beside it, and now there are two `findings.json` files, two
sitemaps, and no way to tell which one the proposal quoted. Reuse the folder
(contract §1). If the previous run's contents look wrong, say so and let the
user decide — do not route around it with a new directory.

**Editing findings.json after the ids are stamped.** Rewording is fine — ids
are frozen and every reference survives. *Deleting* a finding that `ia.json`
cites is not: the next build fails with the JSON path of the dangling `fid`,
which is the intended behaviour, but the fix is to update the IA, not to
re-stamp the ids.

**Cards overflowing.** Height is estimated from character counts. If text spills,
shorten the `detail` field or set `show_fix: false` in `meta` for a denser deck.
Pagination is automatic; never pre-split a section.

**Urbanist missing.** The deck names the font; the viewer needs it installed.
`assets/fonts/` has the TTFs. The Figma plugin falls back to Inter and says so.

**Findings that are really opinions.** "The design feels dated" is not a finding.
Name the element, the effect on the user, and the change. If it cannot be
written that way, it does not belong in the deck.

**Benchmarks quoted from memory.** Every number that is not measured from the
client's own page must have been fetched during this session and recorded in
`research.json`. A stale statistic is worse than no statistic.

**Too many Critical findings.** If everything is urgent, nothing gets fixed.

## Rebranding for another agency

Everything visual is in `assets/brand.json`: agency name, footer strings,
colours, category set, type scale, layout fractions. Change it there and both
renderers follow. The Figma plugin accepts the same file as a drop-in override,
so a different agency needs no code changes.
