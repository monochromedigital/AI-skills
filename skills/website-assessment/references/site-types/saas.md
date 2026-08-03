# SaaS sites

**Conversion here** is a qualified signup — a trial started, a demo booked, or
a plan bought. The site's job is to make a buyer understand a product they
cannot hold, price it against their situation, and believe the switch is safe.

Two things distinguish a SaaS audit. First, the pricing page carries more
weight than the homepage. Second, the site does not end at signup: the first
run of the product is part of the conversion path and belongs in the audit if
you can reach it.

## What must be captured

1. Homepage
2. **Pricing page** — with the monthly/annual toggle in both states
3. A product or feature page (the deepest one, not the overview)
4. The signup flow, up to the point of creating an account
5. The demo-request or contact-sales form
6. A use-case, industry, or solution page if the site segments by buyer
7. Docs or help centre entry point
8. Security / trust / compliance page if one exists
9. The post-signup first screen, if the client gives you an account
10. Homepage and pricing at 390×844 mobile

## Homepage

- The headline names the product category. "The platform for modern teams"
  tells a buyer nothing; they cannot tell if you are a CRM or a chat app
- A product visual above the fold — screenshot, short loop, or interactive
  demo. Abstract illustration where a product shot belongs is a real finding
- Two entry routes, differentiated: self-serve and sales-assisted. A single
  CTA forces enterprise buyers into a trial they will not run
- Social proof appropriate to the buyer's size — logos of comparable
  companies, not the three biggest names collected years ago
- Integrations named, since for most buyers the deciding question is whether
  it works with what they already run
- The problem stated before the solution; a features list with no problem
  framing converts only visitors who already knew what they wanted

## Pricing page — audit this hardest

- Prices shown. "Contact us" on every tier is a qualification decision the
  client may have made deliberately — raise it as a finding with the tradeoff
  stated, not as an error
- The unit of pricing is unambiguous: per seat, per usage, per month, billed how
- Annual/monthly toggle shows the saving, and the annual figure is stated as
  what it is (per month billed annually vs total) — ambiguity here is a trust
  finding, not a copy one
- One tier is recommended. Without an anchor, buyers default to the cheapest
  or to leaving (Anchoring Bias, and Hick's Law once you pass four tiers)
- Tier differences are expressed in outcomes, not internal feature names
- Limits are stated: seats, records, API calls, and what happens at the ceiling
- Overage and true cost at scale discoverable before signup
- Currency and tax handling appropriate to the visitor's market
- FAQ answers the objections that stop the purchase: cancellation, migration,
  data export, contract length, what happens to data if they leave
- A free tier or trial is distinguishable from the paid tiers at a glance

## Signup and trial

- Credit card requirement stated *before* the signup form starts. Discovering
  it at step two is one of the most damaging patterns on a SaaS site
- Field count at signup minimal — every field before the product is a tax
- SSO / Google / Microsoft where the buyer segment expects it
- Email verification does not block the first look at the product
- Trial length and what happens at the end stated on the signup screen
- If the trial is feature-limited rather than time-limited, that is stated
- The first screen after signup moves the user toward the aha moment rather
  than presenting an empty dashboard. An empty state with no next action is
  where most trials die

## Type-specific notes per category

**Copy / Content** — the category and the buyer are named in the first
sentence. Jargon is either the buyer's own vocabulary (correct) or the
vendor's internal naming (a finding). Feature names get a plain-language
gloss on first use.

**UX Design** — check the buyer's actual journey: can someone comparing three
vendors get from homepage to a pricing answer to an integration answer to a
security answer in four clicks? That path, not the marketing narrative, is the
real IA.

**Development** — marketing-site performance is a ranking and impression
factor; app subdomain performance is a retention factor. Do not merge them
into one finding. Check that the docs site is not a second design system.

**SEO** — comparison, alternative, and integration pages are the highest-value
SEO surface in SaaS and are usually missing or thin. Check `SoftwareApplication`
or `Product` structured data, and whether docs are indexable. Programmatic
pages (one per integration) must not be near-duplicates.

**Accessibility** — interactive product demos and embedded videos are the
usual failures: no keyboard route, no captions, autoplay ignoring
`prefers-reduced-motion`. Pricing toggles need to be real controls with state
announced. Data-heavy app screenshots need a text summary of what they show.

**CRO** — a trust or security page is a conversion asset for B2B, not a legal
formality; if the buyer's compliance team cannot self-serve SOC 2 or GDPR
answers, the deal stalls. Time-to-value beats feature count every time.

## Severity calls specific to SaaS

Treat as **Critical**:

- Credit card requirement not disclosed before the signup form
- Pricing that cannot be determined for a stated common use case
- No route for a buyer who cannot self-serve (no demo, no sales contact)
- Post-signup empty state with no first action
- Trial end behaviour undisclosed (does data survive?)
- Security/compliance claims with no evidence page behind them

## Benchmarks to look up live

- Free-trial to paid conversion rates, split by credit-card-required vs not,
  and by self-serve vs sales-assisted — the split is the useful part, since it
  is what argues the finding
- Freemium vs free-trial conversion comparison for the client's ACV band
- B2B demo-request form field-count benchmarks
- Whichever competitors the client names — capture their pricing pages and
  compare structure directly. A side-by-side pricing comparison is the single
  most persuasive slide in a SaaS audit
