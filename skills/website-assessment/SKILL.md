---
name: website-assessment
description: Run a section-by-section UX/UI/SEO/accessibility audit of a website and deliver it as a Crackwits-branded slide deck (PPTX) and/or Figma slides, with numbered markers pinned to the exact elements, colour-coded category tags, severity, recommended fixes, and a summary slide with category counts. Use this whenever the user asks to assess, audit, review, critique, analyse, evaluate, or "look at" a website or web page — including phrases like "what's wrong with this site", "review this landing page", "check this site for accessibility", "do a UX audit", "assess a competitor's site", "prepare a website review for a client/prospect", or when they share a URL and want an opinion on it. Also use when they ask for a website assessment deck, site audit slides, or a UX/UI report. Trigger even if the user does not say "audit" or "deck" — a request to evaluate any live website is this skill.
---

# Website Assessment

Produces the Crackwits "Website UX/UI Assessment" deck: one slide per page
section, a device-framed screenshot with numbered markers pinned to the exact
element in question, matching numbered finding cards tagged by discipline, and
a summary slide with a narrative diagnosis plus counts per category.

## Before starting, confirm three things

Use AskUserQuestion unless the session is unattended:

1. **Which pages** — one page, the key journey (home + services + contact), or
   the whole site
2. **Audience** — prospect, existing client, or internal scoping. This changes
   framing and finding count, not the findings themselves (see `references/voice.md`)
3. **Output** — PPTX, Figma, or both

Do not ask about categories or severity. Those are fixed.

## Workflow

### 1 · Capture

Read `references/capture.md` and pick a route. In a cloud session the sandbox
cannot reach general websites, so **Claude in Chrome is the primary route** —
it uses the user's own browser and reaches authenticated and staging sites.
Playwright (`scripts/capture.py`) is fully automatic where the network allows.
HTML-only via WebFetch is the last resort and limits what can honestly be
assessed.

Then frame the screenshots:

```bash
python3 scripts/frame.py --in-dir audit/screens --out-dir audit/framed --device tablet
```

Keep the `screen_rect` it prints for each image.

### 2 · Look before writing

Actually **Read the screenshots**. This is a visual audit; findings written
without looking at the page are worthless and obvious to the client.

Then read `page-data.json` for the measured evidence — contrast ratios, alt
coverage, heading outline, form labels, load timing, tap targets. Every number
there is a finding you do not have to argue for.

### 3 · Write the findings

Read `references/categories.md` for what to look for per category and how to
assign severity, and `references/voice.md` for how findings are phrased. If the
`psychology-of-design` skill is available, read it before writing UX and CRO
findings so principle citations are accurate rather than decorative.

Work section by section, in page order. For each section ask: what is this
section for, and what stops it doing that job?

Write `findings.json` per `references/schema.md`. The essentials:

- 1–3 category tags per finding, never more
- Observation → consequence → fix, in that order, in that voice
- A number wherever a number exists
- `marker.x` / `marker.y` as fractions of the screenshot, taken from the `rel`
  boxes in `page-data.json`
- Severity used with discipline — roughly 10–20% Critical

Then the summary narrative: three short paragraphs, diagnosis → pattern →
gaps. The counts grid is generated automatically.

### 4 · Build

**PPTX:**

```bash
python3 scripts/build_deck.py --findings audit/findings.json --root audit --out assessment.pptx
```

**Figma:** hand the user `findings.json` and the framed PNGs, and point them at
`references/figma-setup.md`. The plugin cannot be run remotely — Figma's REST
API and MCP connector are read-only, so only a plugin running in their desktop
app can create the slides. Send the `figma-plugin/` folder if they have not
installed it yet.

### 5 · Verify before delivering

Non-negotiable. Convert and look at every slide:

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
- Nothing colliding with the footer

Fix and rebuild until it is clean. Then deliver with SendUserFile.

## The seven categories

Copy / Content · UX Design · UI Design · Development · SEO · Accessibility · CRO

Colours, selection rules, and per-category checklists are in
`references/categories.md`. Colours and layout live in `assets/brand.json` —
edit that file, never hard-code a value in a script.

## Files

| Path | What it is |
|---|---|
| `assets/brand.json` | Colours, type scale, layout fractions. Single source of truth |
| `assets/fonts/` | Urbanist TTFs (OFL) for installing locally |
| `scripts/capture.py` | Playwright capture — sections, element boxes, technical evidence |
| `scripts/frame.py` | Wraps screenshots in the device frame, reports `screen_rect` |
| `scripts/build_deck.py` | findings.json → PPTX |
| `figma-plugin/` | Figma plugin: same slides, native Figma frames |
| `references/capture.md` | The three capture routes, and what the data gives you |
| `references/categories.md` | Category definitions, checklists, severity, principles |
| `references/voice.md` | How findings are phrased; audience variants |
| `references/schema.md` | findings.json contract and marker coordinates |
| `references/figma-setup.md` | Plugin install and use |

## Things that go wrong

**Markers in the wrong place.** They are fractions of the *screenshot*, not the
framed PNG and not the slide. `screen_rect` from `frame.py` does the mapping —
if you omit it, every marker shifts by the bezel width.

**Cards overflowing.** Height is estimated from character counts. If text spills,
shorten the `detail` field or set `show_fix: false` in `meta` for a denser deck.
Pagination is automatic; never pre-split a section.

**Urbanist missing.** The deck names the font; the viewer needs it installed.
`assets/fonts/` has the TTFs. The Figma plugin falls back to Inter and says so.

**Findings that are really opinions.** "The design feels dated" is not a finding.
Name the element, the effect on the user, and the change. If it cannot be
written that way, it does not belong in the deck.

**Too many Critical findings.** If everything is urgent, nothing gets fixed.

## Rebranding for another agency

Everything visual is in `assets/brand.json`: agency name, footer strings,
colours, category set, type scale, layout fractions. Change it there and both
renderers follow. The Figma plugin accepts the same file as a drop-in override,
so a different agency needs no code changes.
