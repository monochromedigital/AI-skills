# Ecommerce sites

**Conversion here** is a completed order. Every finding should ultimately
connect to one of three things: does the visitor find the product, does the
visitor trust the product enough to add it, does the visitor finish paying.

The default audit fails ecommerce by auditing only the homepage. The homepage
is the least important page in a catalogue business. The product detail page
and the checkout are where the money is lost.

## What must be captured

Do not write an ecommerce audit without these. If any are unreachable, say so
in the summary rather than skipping silently.

1. Homepage
2. A category / product listing page, with filters visible
3. **Two product detail pages** — one in stock, one out of stock or low stock
4. The cart, with at least one item in it
5. **Every step of checkout**, up to the payment step (stop before paying)
6. Search results for a real query, and for a deliberate misspelling
7. Delivery/returns policy page
8. The whole of steps 3–5 again at 390×844 mobile

Checkout usually needs Route A (the user's own browser) because it depends on
session state. Add an item, then walk it. If the client will not allow a live
cart, ask for a staging URL — auditing an ecommerce site without seeing the
checkout should be declared a limitation, not glossed over.

## Product listing page

- Filters reflect how customers choose, not how the warehouse is organised —
  size, price, use case, availability before SKU attributes
- Filter state survives navigation and back; the URL is shareable
- Out-of-stock items are filterable out, not just labelled
- Sort defaults to something defensible; "featured" with no logic is a dark pattern
- Product cards carry price, and price *including* the decisive variant
- Card imagery is consistent in crop and background — inconsistency here reads
  as a low-trust marketplace even when every product is first-party
- Pagination or lazy load does not reset scroll position on back
- Result count stated; empty states offer a route out, not a dead end

## Product detail page — the highest-value slide in the deck

- Price, delivery cost, and delivery *date* all visible without scrolling.
  Extra cost at checkout is the single most-cited abandonment reason (40%)
- Stock state is explicit and specific ("3 left", "back in stock 12 March"),
  not just an absent Add to Cart
- Image gallery: zoom, scale reference, and the product on/in context
- Variant selection shows unavailable combinations as unavailable *before* the click
- Returns window and process stated on the page, not linked to a policy PDF
- Reviews present, with count, and negative reviews not filtered out
- Size, spec, or compatibility guidance where the product needs it
- Add-to-cart gives explicit feedback; a silent cart-count increment is not feedback
- Cross-sells are relevant and do not push the primary action below the fold
- Mobile: Add to Cart reachable without scrolling back up — a sticky bar is
  the standard answer

## Cart

- Line items editable without a page reload; removal is undoable
- Full order total — including shipping and tax — calculable *in* the cart
- Promo code field does not send the user off to hunt for a code
- Continue-shopping route preserved
- Stock and price changes since adding are surfaced honestly

## Checkout — audit every step

- Guest checkout offered. Forced account creation drives 18% of abandonment
- Step count visible and honest; no surprise steps after the user commits
- Address autocomplete, and postcode lookup where the market expects it
- Payment methods appropriate to the market — the local wallet or BNPL
  option missing is a revenue finding, not a preference
- Card fields: correct `autocomplete` attributes, correct mobile keyboards,
  inline validation that fires on blur not on submit
- Errors preserve entered data. Losing a filled form is Critical
- Trust markers at the payment step — security, returns, contact route
- No navigation away from checkout except a deliberate exit; nav and footer
  links are a leak
- Delivery date confirmed before payment, not after
- Order confirmation states what happens next and when

## Type-specific notes per category

**Copy / Content** — product copy answers the buying question, not the SEO
brief. Delivery, returns, and sizing are written once and authoritatively.
Stock and price language is consistent across listing, PDP, and cart.

**Development** — image weight is the dominant performance problem in
catalogues; check the listing page's total transfer, not just the homepage's.
Variant switching should not trigger a full page load. Check that the cart
survives a refresh.

**SEO** — Product and Offer structured data with price and availability;
BreadcrumbList; unique titles per variant page or a canonical strategy that
does not cannibalise. Faceted-navigation URLs are the classic index-bloat
failure — check what is crawlable. Out-of-stock products should not 404.

**Accessibility** — variant swatches are the most common keyboard trap;
colour-only swatches need names. Star ratings need a text equivalent. Quantity
steppers need labels. Checkout error messages need to be announced, not just
coloured red.

**CRO** — the fastest wins are almost always: total cost earlier, guest
checkout, and a delivery date on the PDP.

## Severity calls specific to ecommerce

Treat as **Critical** even where a generic audit would say Moderate:

- Any cost that first appears at the payment step
- Forced account creation before checkout
- A checkout step that loses entered data on error
- Add to Cart with no confirmation on mobile
- Out-of-stock state discoverable only after adding to cart
- A payment method the market expects being absent

## Benchmarks to look up live

Fetch these at audit time via `references/research.md` — do not cite from
memory, the figures move every year:

- Documented average cart abandonment rate and the ranked reasons — Baymard
  Institute maintains the aggregate across ~50 studies (70.22% as of the last
  check, with extra costs at 40% the top reason)
- Average ecommerce conversion rate **for the client's vertical**, not the
  global average — the spread between verticals is wider than most gaps you
  will find
- Mobile vs desktop conversion and abandonment split, since most of your
  mobile findings are best argued with it
