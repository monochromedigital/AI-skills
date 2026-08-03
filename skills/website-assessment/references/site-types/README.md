# Site types

The seven categories in `categories.md` apply to every website. They are the
floor, not the audit. What separates a competent audit from one that wins the
work is the type-specific layer: the sections, flows, and failure modes that
only exist because of what this particular site is *for*.

Read `categories.md` first, then exactly one file from this folder. The
type file is **additive** — it never replaces a check in `categories.md`, it
adds the ones a generic checklist cannot know about, and it redefines what
"conversion" means for this site.

| File | Covers |
|---|---|
| `ecommerce.md` | Product catalogues, carts, checkouts — anything transacting on-site |
| `saas.md` | Software products sold by subscription: trials, pricing tiers, product-led signup |
| `service-business.md` | Local and professional services, agencies, clinics, trades — enquiry-led |
| `corporate.md` | Brand, corporate, institutional, embassy, and government sites — informational and reputational |
| `content-publisher.md` | Media, news, magazines, blogs, documentation — attention and subscription |
| `marketplace.md` | Two-sided platforms, listings, directories, booking aggregators |
| `nonprofit-education.md` | Charities, NGOs, schools, universities — donation and enrolment |

## Identifying the type

Do this **after capture, before writing findings** — the signals live in the
captured pages, not in the URL. Assign one primary type. If a second type
genuinely applies to a distinct part of the site (a SaaS product with a real
content marketing hub, a corporate site with a small shop), read the second
file too and note in the finding which part of the site it governs.

| Signal in the captured pages | Points to |
|---|---|
| Product listing + product detail + add-to-cart + a `/cart` or `/checkout` route | Ecommerce |
| Pricing page with tiers, "Start free trial", "Book a demo", a `/signup` or app subdomain | SaaS |
| Prominent phone number, service pages, "Book an appointment", enquiry form, service-area or location pages | Service business |
| About / Leadership / News / Investors / Careers, no transaction anywhere, brand or institutional identity dominant | Corporate |
| Article feed, author bylines, categories or tags, publish dates, newsletter or paywall prompts | Content publisher |
| Search-with-filters over supply someone else provides, listing detail pages, two signup routes (buy side and sell side) | Marketplace |
| "Donate", "Give", "Apply", programme or course pages, impact reporting, term dates | Nonprofit / education |

Platform signals from `page-data.json` corroborate but do not decide it: a
Shopify store front-end can be a brand site with no cart, and a WordPress
install can be any of the seven.

## Confirming with the user

Once identified, confirm before writing — one AskUserQuestion, the detected
type first and marked as detected, the two next-most-likely as alternatives.
State the signal that drove the detection so the user can correct it cheaply:

> Detected **Ecommerce** — 48 product pages, a cart route, and Shopify
> checkout. Is that the right lens?

In an unattended session, proceed with the detected type and state the
assumption on the summary slide.

## When the type is wrong or absent

If nothing matches — a portfolio, a single-page event site, an internal tool —
do not force a file. Audit against `categories.md` alone, and say plainly in
the summary that the assessment is structural rather than type-specific. A
mis-applied lens produces findings about a checkout that does not exist, which
is worse than no lens at all.
