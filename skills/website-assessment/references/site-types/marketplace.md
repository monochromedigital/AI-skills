# Marketplaces, directories, and booking platforms

Two-sided platforms: property portals, job boards, travel and restaurant
booking, freelancer platforms, classifieds, business directories, ticketing.

**Conversion here** is a match — a booking, an application, an enquiry to a
listing owner. The site has two audiences with opposed interests, and auditing
only the demand side is the standard mistake. Supply-side acquisition is a
first-class part of the audit.

The other distinctive property: the platform does not control the content.
Listing quality is uneven by nature, and findings about it must be aimed at
the *system* that admits and displays listings, not at any one listing.

## What must be captured

1. Homepage, with the primary search entry
2. **Search results with filters applied**, and again with a filter combination
   that returns nothing
3. Two listing detail pages — one well-populated, one sparse
4. The enquiry, booking, or application flow to the confirmation step
5. The map view, if one exists
6. **The supply-side landing page** — "List your property", "Post a job",
   "Become a partner" — and its signup flow
7. Saved items / account area, if reachable
8. Search results and one listing at 390×844 mobile

## Search and filtering — the core product

- Search is on the homepage and is the dominant element; a marketplace that
  makes you navigate to search has buried its product
- Filters match how people actually decide, and the highest-use filter is not
  hidden behind "more filters"
- Filter state is in the URL and survives back navigation. Losing a
  15-filter search is Critical
- Applied filters are visible as removable chips, not only as form state
- Result counts shown per filter value before applying, where feasible
- Zero-result state relaxes a constraint and offers alternatives rather than
  saying "no results"
- Sort options are meaningful and the default is disclosed. If the default
  ranks by paid placement, that must be labelled — undisclosed paid ranking is
  both a trust finding and, in several jurisdictions, a legal one
- Map and list stay in sync; moving the map updates results predictably
- Pagination preserves position on return, since users bounce in and out of
  listings constantly

## Listing detail

- Listings with missing data degrade gracefully — a missing photo shows a
  labelled placeholder, not a broken frame
- The platform enforces a minimum: photos, price, location, availability,
  a description of a stated minimum length
- Price is complete. Fees added at the booking step are the same failure as
  ecommerce shipping costs, and in travel it is now regulated in several
  markets
- Availability is live, not a stale cache
- Contact route to the listing owner is on the listing, with a response-time
  expectation
- Trust signals per listing: verification badges with a stated meaning,
  reviews with count, owner join date, response rate
- Similar listings shown, so a rejected listing does not end the session
- Save / shortlist works without forcing an account, or the account gate is
  justified at the moment it appears

## Supply side

Audit this as seriously as the demand side.

- Route to list is discoverable from the homepage without hunting
- The value proposition to suppliers is stated: audience size, cost, what they
  get
- Pricing or commission stated before the signup form
- Listing creation flow: field count, whether it can be saved and resumed,
  whether a photo upload failure loses the draft
- Time-to-first-listing is the supply-side equivalent of time-to-value
- Dashboard shows the supplier what their listing is doing

## Type-specific notes per category

**Copy / Content** — the platform's own copy versus user-generated copy are
different audits. Check whether the platform provides guidance and structure
that improves listing quality at entry.

**UX Design** — the browse-compare-shortlist-decide loop is the journey.
Comparison is usually the weakest link: users open six tabs because the
platform gives them no way to compare.

**Development** — search performance under filters; result-set caching;
image handling for user-uploaded photos of wildly varying size. Check whether
uploaded images are processed or served at original weight.

**SEO** — this type lives or dies on indexable facets. Which filter
combinations are crawlable, which are canonicalised, and is there index bloat
from infinite combinations? Structured data per vertical is essential —
`JobPosting`, `RealEstateListing`, `Product`, `Event`, `Hotel`. Expired
listings need a strategy: 404, redirect, or a page that shows alternatives.
Duplicate listings across suppliers are a canonical problem.

**Accessibility** — map interfaces are the standard failure and need a list
equivalent that carries the same information. Filter panels need to announce
result changes. Date pickers in booking flows are frequently keyboard-hostile.
Infinite scroll needs a keyboard-reachable alternative.

**CRO** — the enquiry or booking is the conversion, but the shortlist is the
leading indicator. Findings that increase saved listings are conversion
findings.

## Severity calls specific to marketplaces

Treat as **Critical**:

- Filter or search state lost on back navigation
- Fees disclosed only at the final booking step
- Paid ranking presented as relevance without disclosure
- Availability shown that is not real
- Listing creation flow that loses a draft
- Map with no accessible list equivalent
- Expired listings returning soft 404s or empty pages

## Benchmarks to look up live

- Vertical-specific conversion benchmarks — a property portal and a job board
  behave nothing alike, so the global marketplace average is useless
- Disclosure and pricing-transparency regulation in the client's market for
  their vertical, particularly travel, property, and financial listings
- Two direct competitors: capture their search results page and their listing
  page. On this type the competitor comparison is the deck's centrepiece,
  because the visitor is genuinely choosing between platforms
