---
name: sitemap-ia-board
description: Produce a complete visual sitemap + information architecture board for any website project — evidence-grounded personas, page columns with section-level cards tagged for UX, CRO, SEO, and lead generation, plus plain-language explainers, phase tagging, conversion-flow logic, a CMS/database architecture spec for developers, and a jargon dictionary. Delivers a structured `ia.json` plus either a standalone HTML board or a combined report rendered alongside an existing site audit. Use this whenever the user asks for a sitemap, information architecture, IA, site structure, page structure, website planning, a "site map", website wireframe planning, personas for a website, or wants to plan the pages/sections of a new or redesigned website — for any industry (e-commerce, services, B2B, SaaS, restaurants, real estate, portfolios). Also trigger when a client brief for a new website/brand is shared and the deliverable is website structure or planning, even if the words "sitemap" or "IA" never appear.
---

# Sitemap + Information Architecture Board

A browsable board where each page of the website is a column of section cards,
preceded by the personas that justify them and followed by conversion logic, a
CMS/database architecture, and a jargon dictionary. It renders through the same
engine as the audit report, so a client who gets a board and a client who gets
an audit are looking at one design system. The
audience is mixed — client, designers, copywriters, SEO and developers all read
the same document — which is why it layers plain language on top of specialist
annotations.

Read `references/project-contract.md` first. It governs where the work lives,
how this skill talks to the site-audit skill, and what happens when a file it
expects is missing. Where the contract and this file disagree, the contract
wins.

## Two modes

The folder decides, not the user:

| In the project folder | What this skill does |
|---|---|
| `findings.json` is present | **Redesign.** There is a diagnosis attached. Cite it, write `ia.json`, and let the assessment skill's `build_site.py` render the combined report. Do not build a second board competing with it |
| no `findings.json` | **Greenfield.** Write `ia.json` and render it with `build_board.py`, so the skill delivers on its own — same renderer, same look |

## Workflow

### 1 · The project folder

Ask for it at the start, in the same `AskUserQuestion` call as everything else
— contract §1. Default the name to a slug of the client, confirm the parent
directory, and **reuse the folder if it already exists** rather than creating a
second one.

Then read `project.json` if it is there. Another skill has already established
the client, URL, market, audience, languages and brand tokens; take them and do
not ask again. Asking a second time invites a different answer, and now two
documents disagree about the client's own name. If it is not there, create it
per contract §2.

### 2 · Gather what the IA needs

Whatever `project.json` did not settle. Read what the user provided — brief,
screenshot, description — and get to five things:

1. **Business model** — what is sold, to whom (B2B / B2C / both)
2. **Primary conversion** — the #1 action a visitor should take
3. **Markets & languages** — multilingual changes URL structure, DB schema and
   layout; RTL languages mirror the whole UI
4. **Trust situation** — new company vs established (a new company has no
   testimonials; see phase discipline)
5. **Post-launch plans** — content/SEO/ads retainers change what the
   architecture must be ready for

If the input is thin, ask 3–4 questions covering the gaps. If it is a full
brief, extract and proceed — don't interrogate someone who already wrote it all
down.

### 3 · Read the audit, if there is one

If `findings.json` is in the folder, this is a redesign with a diagnosis
attached, not a greenfield build. Read it, and use it twice:

- **To justify sections.** A section that exists because of a finding carries
  that finding's `fid` — one reference, the id only, never a copy of the audit's
  text. Contract §7 explains why copying is the failure mode
- **To inform the structure.** A page whose absence caused a Critical finding
  is not optional. If the audit says six services share one URL and none can
  rank, the IA has six service pages, and each cites that finding

With no `findings.json`, build greenfield and emit **no `fid` anywhere**. Never
invent one — a `fid` in a greenfield project fails validation, which is exactly
what should happen.

### 4 · Personas

New to this skill, and they come **before** the IA because they are the
argument for it. Read `references/personas.md` — how to ask what they are
grounded in, why the basis goes in the deliverable even when the answer is "no
research", how to derive the set from a client's own published archive, and
what each persona carries.

Two things are non-negotiable:

- **Be honest about the basis in the output**, not just in conversation
- **A persona that does not change the IA does not belong in the document**

Where a site already exists, prefer evidence the client has published over
invention — a projects archive, a client list, case studies. Derive the persona
set from what they actually sold and state the count behind each one ("15 of 50
installations").

### 5 · Design the IA before writing any JSON

Decide pages and sections on paper first. Read `references/methodology.md` for
the reasoning rules — deriving pages from a business model, the tagging system,
phase discipline, lead-capture layering, SEO architecture, DB modelling
patterns. The board is only as good as this thinking; `ia.json` just records
it and the renderer just draws it.

A typical build is 8–12 page columns. Every site gets: Home, primary offering
page(s) + detail template, a dedicated conversion landing page, About, Contact,
a content/education hub, and a Utility column. Add industry-specific pages from
the methodology's patterns.

### 6 · Apply the quality bar

Before writing anything, check the design against these — they come from real
review cycles:

- **Home is 6–8 sections, not 12.** Merge overlapping sections (categories +
  featured items = one section; trust logos belong inside the hero). One lead
  hook on Home, not two competing ones
- **Phase discipline.** Anything needing content the client won't have at launch
  (testimonials, case studies, blog teasers) or real build cost that isn't
  launch-critical becomes a dashed Phase 2 card. Empty social proof placeholders
  hurt credibility — never ship them
- **One canonical URL per item.** Detail pages live at one URL regardless of
  navigation path, never nested under brand or category. Document it in the dev
  notes
- **A dedicated conversion landing page** (distraction-free, multi-step form,
  per-type thank-you pages) whenever paid media is plausible
- **FAQ is content-first.** Value = long-tail queries + AI answers. FAQ schema
  is optional — Google dropped FAQ rich results for most sites in 2023. One
  canonical FAQ hub; page-level FAQs stay short and link to it
- **Lead capture is layered by intent stage**: cold (newsletter/guide), warm
  (gated downloads), hot (quote/booking). If the board has only one form, it's
  underbuilt

### 7 · Write `ia.json`

Read `references/ia-schema.md` and write it into the project folder. This is
the file the shared renderer consumes, and the record any later skill reads.

Read `references/ai-writing.md` before writing any of its prose. The
In-plain-words boxes, the section descriptions, the persona context and the
evidence note are the parts a client actually reads, and they are exactly where
"a robust, holistic ecosystem that empowers users" creeps in. A board written
that way reads as a template with the client's name dropped into it, which is
the opposite of what an IA is meant to prove.

It is a **serialisation of the thinking above, not a replacement for it**. The
quality bar, phase discipline, lead-capture layering and the In-plain-words
formula all still apply — do the work, then write it down in this shape.

`db` and `glossary` are optional and belong to the standalone board. The shared
renderer ignores them rather than failing on them.

### 8 · Build the output

Both modes call the same renderer, `scripts/render_report.py`, which this skill
carries byte-identically with `website-assessment`. A greenfield board and an
audit report are the same document with different sections present. Nothing is
hand-written into HTML any more.

**Redesign mode** — `ia.json` is this skill's deliverable. Hand it to the
assessment skill:

```bash
python3 ../website-assessment/scripts/build_data.py --project <project>
python3 ../website-assessment/scripts/build_site.py --project <project> \
    --out <project>/out/report.html
```

Personas and Sitemap slot in beside the audit, and Database and Glossary follow
when `ia.json` carries them. Do not also build a standalone board — two
documents saying the same thing diverge, and the client reads whichever one they
opened last. `build_board.py` refuses in this case and says so.

**Greenfield mode:**

```bash
python3 scripts/build_board.py --project <project> --out <project>/out/sitemap.html
```

Home, Personas and Sitemap, plus Database and Glossary when the file carries
them. No Audit, Summary or Action items, because there are no findings — those
tabs are absent from the nav rather than empty.

### 9 · Validate, then look at it

Both. Neither is optional because the run "went fine".

```bash
python3 scripts/validate_ia.py --ia <project>/ia.json
python3 scripts/validate_ia.py --ia <project>/ia.json --board <project>/out/sitemap-*.html
python3 scripts/check_prose.py --project <project>
```

Every `fid` must resolve against `findings.json`. It fails loudly with the JSON
path of any that does not.

`check_prose.py` does the same for the writing, flagging AI-writing vocabulary
by JSON path. Text inside double quotes is exempt, so quoting the client's own
copy never trips it.

Then open the rendered output in a browser and check it:

- Columns render, and nothing has collapsed into a single column
- The phase toggle and the discipline filters change the visible counts
- Evidence expanders open the **right** finding — click one and read it
- The board scrolls correctly at mobile width, with no page-level horizontal
  overflow

### 10 · Deliver

Present it in a few sentences: page count, the conversion funnels, and 1–2
architecture decisions worth flagging — the kind a stakeholder might question
later.

## Iterating after delivery

Boards live through review rounds (client, SEO, dev). When feedback arrives,
edit the existing files rather than regenerating — preserve everything not
under discussion, and keep `ia.json` and the rendered board in step. When a
decision is debated and settled (e.g. URL strategy), record the *reasoning* in
a dev note or card so it doesn't get re-litigated.

## Files

| Path | What it is |
|---|---|
| `assets/brand.json` | Colours and type. Byte-identical in `website-assessment` |
| `assets/ai-writing.json` | The AI-writing word lists. Edit here, never a pasted copy |
| `assets/fonts/` | Urbanist TTFs (OFL), embedded into the rendered board |
| `scripts/render_report.py` | All the CSS, JS and HTML. Byte-identical in `website-assessment` |
| `scripts/build_board.py` | Thin wrapper: validates, then renders the greenfield board |
| `scripts/validate_ia.py` | Validates ia.json — schema, ids, chips, phases, and every `fid` |
| `scripts/check_prose.py` | Flags AI-writing vocabulary in the client-facing prose, by JSON path |
| `references/project-contract.md` | The shared agreement with the other project skills |
| `references/ia-schema.md` | The `ia.json` contract, field by field, and what is enforced |
| `references/personas.md` | Grounding, honesty about the basis, and what each persona carries |
| `references/methodology.md` | The reasoning rules: pages, tags, phases, SEO, DB patterns |
| `references/ai-writing.md` | Writing that does not read as generated, and which upstream rules do not apply here |

## Things that go wrong

**A `fid` that does not resolve.** Usually a finding was deleted after the IA
cited it, or an id was retyped rather than copied. `validate_ia.py` names the
JSON path. Fix the reference — never delete the check.

**Copying audit text into `ia.json` instead of referencing it.** This is the one
that does not error. A section card that quotes the finding reads better in
review, and then someone rewords the finding — and the two documents disagree
for the rest of the project, with nothing to signal it. Store the `fid`; the
renderer resolves it and shows the current wording.

**Inventing a `fid` on a greenfield project.** There is no audit, so there is
nothing for it to point at. Emit none.

**A second project folder.** The client already has one; a later run creates
`client-2`; now there are two sitemaps and no way to tell which one the proposal
quoted. Reuse the folder (contract §1).

**Building a standalone board when an audit exists.** Two documents covering the
same structure diverge, and the client reads whichever they opened last. In
redesign mode `ia.json` is the deliverable and the combined report draws it.
`build_board.py` refuses rather than letting it happen quietly.

**Hand-editing the rendered HTML.** It is generated from `ia.json` and will be
overwritten on the next build. Change the JSON. If something cannot be
expressed in `ia.json`, that is worth saying out loud — it usually means the
schema is missing a field the work actually needs.

**Personas that decorate.** If cutting a persona would not remove a page, a
section, a form field or a funnel, it was describing the market rather than
shaping the site. Cut it.

**Personas presented without their basis.** An unsourced persona reads as fact,
gets quoted in a proposal, and becomes the reason a page exists. Say what it is
built on — including when the answer is "nothing but the brief".

**Empty social proof.** A "what clients say" section before there are clients is
anti-proof. It is a dashed Phase 2 card, every time.

**In-plain-words boxes that are not plain.** The formula exists because the
box is the one part of the board a non-specialist reads end to end. "This page
serves as a comprehensive gateway to our robust service ecosystem" fails it
twice — no metaphor, no named actor, and the vocabulary of a document nobody
wrote. `check_prose.py` catches the words; the formula in
`references/methodology.md` is what makes the sentence worth reading.

**A card with no reason to exist.** If it earns no chip, it earns no place.
`validate_ia.py` enforces this, because it is the rule that slips first when a
board is being padded to look thorough.
