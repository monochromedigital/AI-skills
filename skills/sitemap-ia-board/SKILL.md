---
name: sitemap-ia-board
description: Produce a complete visual sitemap + information architecture board as a single HTML artifact for any website project — page columns with section-level cards tagged for UX, CRO, SEO, and lead generation, plus plain-language explainers, phase tagging, conversion-flow logic, a CMS/database architecture spec for developers, and a jargon dictionary. Use this whenever the user asks for a sitemap, information architecture, IA, site structure, page structure, website planning, a "site map", website wireframe planning, or wants to plan the pages/sections of a new or redesigned website — for any industry (e-commerce, services, B2B, SaaS, restaurants, real estate, portfolios). Also trigger when a client brief for a new website/brand is shared and the deliverable is website structure or planning, even if the words "sitemap" or "IA" never appear.
---

# Sitemap + Information Architecture Board

Produce a single self-contained HTML file: a Relume-style visual board where each page of the website is a column of section cards, followed by conversion logic, a CMS/database architecture, and a jargon dictionary. The audience is mixed — client, designers, copywriters, SEO, and developers all read the same document — which is why it layers plain language on top of specialist annotations.

## Workflow

### 1. Gather inputs

Read whatever the user provided (brief, screenshot, description). You need five things before designing anything:

1. **Business model** — what is sold, to whom (B2B / B2C / both)
2. **Primary conversion** — the #1 action a visitor should take (quote request, booking, purchase, call)
3. **Markets & languages** — countries served, languages (multilingual changes URL structure, DB schema, and layout — RTL languages mirror the whole UI)
4. **Trust situation** — new company vs established (a new company has no testimonials; see phase discipline below)
5. **Post-launch plans** — content/SEO/ads retainers change what the architecture must be ready for

If the input is thin (e.g. "a website for my restaurant"), ask 3–4 questions covering the gaps using the AskUserQuestion tool before building. If the input is a full brief, extract these and proceed — don't interrogate someone who already wrote it all down.

### 2. Design the IA before touching the template

Decide pages and sections on paper first. Read `references/methodology.md` for the reasoning rules — it covers how to derive pages from a business model, the tagging system, phase discipline, lead-capture layering, SEO architecture (canonical URLs, geo pages, content hubs), and the DB modeling patterns. The board is only as good as this thinking; the template just renders it.

A typical build is 8–12 page columns. Every site gets: Home, primary offering page(s) + detail template, a dedicated conversion landing page, About, Contact, a content/education hub, and a Utility column (thank-you pages, legal, 404, search). Add industry-specific pages from the methodology's patterns.

### 3. Build from the template

Copy `assets/board-template.html` and fill it in. The template contains the complete CSS, the layout skeleton, one fully-worked example column showing the expected card quality, and HTML comments marking every insertion point. Keep the visual system exactly as-is (colors, tags, dashed Phase-2 style) — consistency across projects is part of the value.

Every page column needs, in order:
- **Column header**: page name + URL slug (templates marked like `(template)` with `{param}` slugs)
- **"In plain words" box**: 2–3 sentences a non-technical client understands, ending with a *concrete example scenario* with a named actor ("a procurement manager filters to…"). This is mandatory for every column — it's what makes the document readable by the whole team.
- **Section cards**: title + 1–2 sentence description that explains *why the section earns its place*, not just what it is. Tag each card with the relevant chips (UX / CRO / SEO / LEAD / language). A card with no reason to exist gets cut.

### 4. Apply the quality bar

Before writing the file, check the design against these — they come from real review cycles:

- **Home is 6–8 sections, not 12.** Merge overlapping sections (categories + featured items = one section; trust logos belong inside the hero). One lead hook on Home, not two competing ones.
- **Phase discipline.** Anything that needs content the client won't have at launch (testimonials, case studies, blog teasers) or real build cost that isn't launch-critical (comparison tools) becomes a dashed Phase 2 card. Empty social proof placeholders hurt credibility — never ship them.
- **One canonical URL per item.** Detail pages live at one URL regardless of navigation path (never nested under brand/category). Document this in the dev notes.
- **A dedicated conversion landing page** (distraction-free, multi-step form, per-type thank-you pages) exists whenever paid media is plausible.
- **FAQ is content-first.** Value = long-tail queries + AI answers (AI Overviews/ChatGPT). FAQ schema is optional — Google dropped FAQ rich results for most sites in 2023. One canonical FAQ hub; page-level FAQs stay short and link to it.
- **Lead capture is layered by intent stage**: cold (newsletter/guide), warm (gated spec/detail downloads), hot (quote/booking forms). If the board has only one form, it's underbuilt.

### 5. Database & CMS section

Fill the DB section of the template following the modeling rules in `references/methodology.md` (§ Database patterns): content tables vs system tables vs Phase 2 tables (dashed — schema created at launch, populated later), field-level localization (never duplicate records per language), a single typed `leads` table, country/region as a dimension not a fork, and dev notes explaining each non-obvious decision so it doesn't get undone.

### 6. Jargon dictionary

The template's glossary contains ~55 pre-written definitions in four groups (Marketing & Conversion, SEO, UX & Design, Technical & Database). Prune terms the document doesn't use, add ones it does. Rule: every specialist term that appears anywhere on the board must have an entry.

### 7. Deliver

Save as `sitemap-information-architecture.html` in the user's folder and present it. Summarize in a few sentences: page count, the conversion funnels, and 1–2 architecture decisions worth flagging (the kind a stakeholder might question later).

## Iterating after delivery

Boards live through review rounds (client, SEO, dev). When feedback arrives, edit the existing file rather than regenerating — preserve everything not under discussion. When a decision is debated and settled (e.g. URL strategy), record the *reasoning* in a dev note or card so it doesn't get re-litigated.
