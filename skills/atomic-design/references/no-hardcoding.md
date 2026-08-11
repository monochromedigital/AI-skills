# Nothing is hardcoded

Five categories. Each one has the same shape: a value that exists in more than one
place, or in the wrong place, is a change you will have to make more than once.

## 1. Design tokens

Colour, spacing, radius, font size, font weight, line height, shadow, breakpoint,
z-index, motion duration and easing.

**Never in a component:** `#1a1a1a`, `rgb(26,26,26)`, `padding: 12px`,
`fontSize: '14px'`, `borderRadius: 8`, `boxShadow: '0 2px 4px rgba(0,0,0,.1)'`,
`w-[327px]`, `text-[#fff]`, `duration-[350ms]`.

```tsx
// ✗
<div style={{ padding: 16, background: '#f5f5f5', borderRadius: 8 }} />
<button className="bg-[#2563eb] px-[14px] rounded-[6px]" />

// ✓
<div className="p-4 bg-surface-subtle rounded-md" />
<button className="bg-brand px-3 rounded-sm" />
```

Tailwind's arbitrary-value syntax is the most common leak, because it does not look
like hardcoding — it looks like Tailwind. `w-[327px]` is a magic number with square
brackets around it. The exceptions the validator allows are references, not values:
`w-[var(--sidebar)]`, `grid-cols-[--layout-cols]`.

**If a value you need has no token, add the token.** The pressure to inline "just
this one value" is exactly how a scale becomes a list of forty near-identical greys.
If the design genuinely needs a one-off, it still gets a name.

## 2. Copy and strings

Every piece of user-facing text arrives from outside the component.

```tsx
// ✗  in components/ui/EmptyState.tsx
<p>No results found. Try a different search.</p>

// ✓
<p>{message}</p>
```

The rule scales with the layer:

- **`ui/` and feature components:** never contain literal copy. Text arrives as
  `children` or a prop. Same reason as the atom test — a component with English in
  it cannot be reused in a different context, let alone a different language.
- **Pages:** may pass literal strings down only if the project has no content or
  i18n layer. The moment one exists, pages read from it too.

This covers `aria-label`, `alt`, `placeholder`, `title`, and every other
user-visible prop — not just visible text nodes.

## 3. Config, URLs, and keys

API base URLs, endpoints, external links, feature flags, analytics IDs, anything
that differs between environments.

```ts
// ✗
const res = await fetch('https://api.example.com/v2/orders')

// ✓
const res = await fetch(`${env.API_URL}/orders`)
```

Keys and secrets never appear in source at all — env only, and never in a file that
ships to the client. External links (social profiles, docs, legal pages) belong in
one config object so they can be audited and changed in one place.

## 4. Magic numbers and business rules

Limits, thresholds, page sizes, timeouts, retry counts, tax rates, discount bands,
minimum ages, character limits.

```ts
// ✗
if (cart.items.length > 20) showWarning()
const shipping = subtotal > 75 ? 0 : 9.99

// ✓  src/constants/cart.ts
export const MAX_CART_ITEMS = 20
export const FREE_SHIPPING_THRESHOLD = 75
export const STANDARD_SHIPPING_FEE = 9.99
```

A bare number in a condition tells the next reader what happens but not why, and
when the rule changes, finding every `75` in the codebase is a search that cannot
be done safely. Named constants live in one module per domain.

`0`, `1`, `-1`, and `2` in obvious structural positions (array indexing, increments,
comparisons against empty) are not magic and are not flagged.

## 5. Anything that appears twice — the Rule of Two

This is the one that matters most in practice, and the one the other four are
really instances of.

**The second time a piece of markup appears, it becomes a component.**

Headers, footers, nav bars, buttons, cards, badges, section wrappers, modals, form
rows, empty states, loading skeletons. If it is on two screens, it is one component
imported twice — not two copies that will drift the first time one of them gets a
fix.

```tsx
// ✗  the same block in ProductPage.tsx and CategoryPage.tsx
<div className="rounded-md border p-4 flex flex-col gap-2">
  <img src={p.image} className="aspect-square rounded-sm" />
  <span className="font-medium">{p.name}</span>
  <span className="text-muted">{p.price}</span>
</div>

// ✓  features/catalog/components/ProductCard.tsx, imported by both
<ProductCard product={p} />
```

It applies past markup: a duplicated conditional, a repeated formatting expression,
a copy-pasted `useEffect`, the same `className` string in two files. Extract to the
lowest layer both callers can reach — if two features need it, it goes to `ui` or
`layout`, never a copy in each.

**Two things that look alike but are not.** Do not force a shared component over
two blocks that merely resemble each other today and answer to different rules. The
test is whether a change to one should always be a change to the other. If yes,
extract. If no, they are coincidence — leave them and note why.

`check_atomic.py` finds repeated blocks by normalising and hashing sliding windows
of lines, so it catches copies that were reindented or had their variable names
left alone. It cannot tell a real duplicate from a coincidence; that judgement is
yours, and the audit report should say which is which.
