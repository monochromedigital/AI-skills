# IA Methodology — Reasoning Rules

How to think through the board. Read before designing; the template only renders these decisions.

## Deriving pages from the business model

Start from what is sold and how buyers decide, not from a generic sitemap:

- **Catalog businesses** (dealerships, e-commerce, real estate): listing page with faceted filters → detail template → conversion page. Indexable filter URLs (`/vehicles/micro-trucks`) turn categories into SEO landing pages.
- **Service businesses** (agencies, clinics, contractors): one page per service (each is an SEO target), process/how-we-work section to de-risk hiring, results/portfolio.
- **B2B**: a dedicated "solutions" money page where ads land, with an ROI/value calculator and a qualifying consultation form. Decision-makers buy in committees — comparison/sharing features and downloadable assets (spec sheets, PDFs) matter because they circulate internally.
- **B2C local** (restaurants, salons, gyms): menu/offering, booking/ordering as primary conversion, Google Business Profile alignment, hours/location prominence.
- **SaaS**: features, pricing (a page of its own — highest-intent visitors), use cases per persona, docs/help.

Brands/manufacturers represented by the business get their own pages when their names carry search volume (e.g. `/products/brands/{brand}`) — trust summary elsewhere links to them.

## The tagging system

Every section card carries chips explaining which discipline it serves:

- **UX** — helps visitors find/decide/act with less friction
- **CRO** — moves visitors toward conversion (trust, proof, CTAs, friction removal)
- **SEO** — earns organic visibility (headings, schema, internal links, content)
- **LEAD** — captures contact info (forms, gated content, calculators)
- **Language chip** (e.g. EN/AR) — where localization has layout consequences (RTL mirrors everything)
- **PHASE 2** — dashed card: planned, not launch scope

A card that earns no chip earns no place.

## Phase discipline

Launch scope = what converts on day one with content the client actually has.

Push to Phase 2 (dashed cards): testimonials/case studies before real clients exist (an empty "what clients say" section is anti-proof), blog/content teasers before content exists, comparison tools and other real build-cost features that aren't launch-critical, market expansions (e.g. country subfolders) that depend on budget.

The board should visibly separate the two — it becomes the scope line in the commercial proposal.

## Lead capture layering

Map captures to intent temperature; a single contact form only catches the ~5% ready today.

- **Cold**: newsletter, downloadable guide (gated) — captures researchers
- **Warm**: gated per-item downloads (spec sheets, brochures, price lists) — captures item-level intent, a strong signal for sales
- **Hot**: quote/booking/consultation forms — short enough to convert, with enough qualifying fields to score the lead (company, size, timeline)
- **Always-on**: the region-appropriate instant channel (WhatsApp in MENA/LATAM, phone for local services) floating on every page, tracked as a first-class conversion

Every form type gets its own thank-you page — that's how conversions get attributed per channel when paid media starts.

## Conversion architecture

- Define 1–2 named funnels and write them into the board's conversion-logic section (e.g. "Product funnel: Home → Listing → Detail → Quote").
- Every "primary CTA" across the site points at one dedicated conversion landing page: minimal nav, multi-step form (low-commitment ask first, contact details last, progress bar), context pre-filled via URL param when arriving from a detail page, trust sidebar.
- All forms share one submission pipeline (typed lead record → CRM webhook → routed notification → typed thank-you redirect). Build once, reuse.

## SEO architecture

- **Intent mapping**: commercial intent → category/listing/brand pages; geo intent → standalone location/country pages (a subsection of About cannot rank — geo pages need their own URLs); informational intent → education hub with evergreen pillar guides.
- **Canonical URLs**: one URL per item (`/products/{item}`), never nested under category or brand. Multiple paths = split link equity + duplicate content. Context is expressed by breadcrumb, not URL. Write this in dev notes — it's the decision devs most often undo.
- **Multi-region**: country subfolders (`/lb/`, `/sy/`) only when content genuinely differs per country (pricing, inventory, local presence). Otherwise: standalone coverage pages + country as a CMS dimension so the subfolder flip later is config, not rebuild. Note subfolders ≠ subdomains — subfolders consolidate authority and are usually preferable.
- **Schema**: Organization + LocalBusiness sitewide, Product on detail pages. FAQ schema is optional/informational — Google dropped FAQ rich results for most sites (2023). FAQ content still earns long-tail and AI-answer visibility.
- **Multilingual**: hreflang pairs, per-locale slugs, one record per item with field-level translations.
- **Hygiene**: XML sitemap, Core Web Vitals budget, no thin pages (geo pages need real local substance).

## Database patterns

Design the content model so a dev can count tables and see the joins.

- **Three groups**: content tables (CMS-edited), system tables (form submissions — app DB, not CMS), Phase 2 tables (dashed: schema created at launch, populated later — migrations on a live DB are the expensive part, empty tables are free).
- **Field-level localization**: one record holds all languages; never duplicate records per language. Mark localized fields (`loc`) and foreign keys (`FK`) visibly in the spec.
- **One typed `leads` table** for all forms: `type` enum + flexible JSON payload + nullable FKs to relevant entities + locale/source/UTM columns + status enum. One table keeps CRM sync and attribution simple.
- **Repeated content gets a table, not page blocks**: anything rendered on 2+ pages (warranties/commitments, trust badges, FAQs with `show_on[]`) must be a structured record — one source of truth, so promises never contradict between pages.
- **Country/region as a dimension**, not a fork: a small `countries`/`locations` table powering geo pages, local contacts, and lead attribution. One database, one site.
- **Singleton** `site_settings` for contact info, hours, socials, response-time promise (address must byte-match the Google Business Profile).
- **Dev notes are part of the spec**: every non-obvious decision (canonical URLs, localization strategy, why Phase 2 tables exist empty) gets a note with its *reasoning*, so it survives team changes and review rounds.

## Writing the "In plain words" boxes

Formula: (1) what the page is, in a metaphor or plain phrase — "the shop window", "the order desk", "the due-diligence page"; (2) one concrete scenario with a named actor and a specific action. Bad: "This page showcases our products." Good: "A procurement manager filters to 'micro trucks, 1-ton payload', gets 3 matches, opens one." If the client's cousin can't follow it, rewrite it.
