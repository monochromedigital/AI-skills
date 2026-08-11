# Audit procedure

Report first. Fix only after the user approves. On an existing codebase a layer
move rewrites import paths across the repo — that is the user's decision, not a
detail to slip into a refactor.

## 1. Detect and configure

```bash
python3 scripts/check_atomic.py --detect <project-root>
```

If the project has no `atomic.config.json`, the validator falls back to built-in
path patterns. On a repo using different folder names, write the config first —
mapping takes two minutes and turns every layer finding from noise into signal.
Files matching no layer pattern are `unknown`: still checked for hardcoded values
and duplication, exempt from layer rules.

## 2. Run the validator

```bash
python3 scripts/check_atomic.py <project-root> --json > /tmp/atomic.json
python3 scripts/check_atomic.py <project-root>          # readable summary
```

## 3. Read the flagged code

The script finds mechanical facts. It does not know which of them matter. Open the
files behind the findings and decide:

- **Duplicate markup** — is it the same thing twice, or two things that resemble
  each other today? Extract only when a change to one should always be a change to
  the other.
- **Oversized component** — a 300-line file that is one dense table renderer can be
  correct. A 300-line file with four sections and three responsibilities is three
  organisms wearing a trenchcoat.
- **Magic numbers** — some 2-digit literals are genuinely structural. Drop the ones
  that are.
- **Hardcoded copy at the page layer** — allowed if there is no content or i18n
  layer. Note it as a future item rather than a violation.

Findings you dismiss should be dismissed in the report with the reason, not
silently dropped. A report that lists only the survivors reads as a shorter audit;
a report that says "these 6 were flagged and here is why they're fine" reads as
one where somebody actually looked.

## 4. Look for what the script cannot see

Read the top-level structure yourself and check:

- Is there more than one token source? Two theme files, or a theme file plus a
  Tailwind config with its own literal values, is drift.
- Do the tokens have a real scale, or are there forty near-identical greys — the
  signature of values added one at a time under deadline?
- Are there components that should exist but don't? Look for the same *shape*
  assembled from different markup in several places — the script's hashing misses
  duplicates that were rewritten rather than pasted.
- Does the page layer actually own the data, or has fetching leaked into organisms?
- Are prop types naming domain entities in `components/ui/`? That is a domain
  organism filed in the wrong layer.

## 5. Write `ATOMIC-AUDIT.md`

At the project root. Structure:

````markdown
# Atomic Audit — <project>

<One paragraph: what the codebase is, what shape it's in, and the single change
that would improve it most. Concrete, not encouraging.>

**Stack:** Next.js 15 (App Router) · Tailwind v4 · shadcn/ui
**Scanned:** 148 files · **Errors:** 31 · **Warnings:** 12

## Errors

### Hardcoded design values (18)

Colour and spacing literals in components, while `app/globals.css` already defines
the matching tokens.

| File | Line | Found | Should be |
| --- | --- | --- | --- |
| `src/features/checkout/CheckoutForm.tsx` | 42 | `#2563eb` | `bg-brand` |
| `src/components/layout/SiteHeader.tsx` | 17 | `px-[14px]` | `px-3` |

<Repeat per check that fired. Group by check, not by file — the fix is per rule.>

### Duplicated markup — Rule of Two (4)

The product card block appears in three files. Same markup, same classes, no
component.

- `src/app/products/page.tsx:61-78`
- `src/app/category/[slug]/page.tsx:88-105`
- `src/features/search/SearchResults.tsx:33-50`

**Fix:** extract `features/catalog/components/ProductCard.tsx` taking `product`.
Three call sites become `<ProductCard product={p} />`.

### Layer violations (5)

`src/components/ui/UserBadge.tsx` imports `@/features/auth/useSession` — an atom
reaching upward into a feature, and reading session state besides. It cannot be
used outside a signed-in context and cannot be tested without an auth provider.

**Fix:** take `user` as a prop. The two call sites already have it.

## Warnings

<Same shape. These need judgement — say what the judgement is.>

## Dismissed

- `src/components/ui/DataTable.tsx` flagged as oversized (241 lines). It is one
  cohesive renderer with no separable sections. Leave it.

## Refactor plan

Ordered so each step unblocks the next.

1. **Consolidate tokens** — `tailwind.config.ts` still carries literal hex values
   that duplicate `globals.css`. One source. *(~30 min, unblocks step 2.)*
2. **Replace hardcoded values with tokens** — 18 sites, mechanical once step 1 is
   done. *(~1 hr.)*
3. **Extract the four duplicated blocks** — biggest structural win; removes ~140
   lines. *(~2 hrs.)*
4. **Fix the five layer violations** — lift data to the page layer, pass props
   down. Touches call sites. *(~2 hrs.)*
5. **Split the three oversized organisms** — do last; easier once 3 and 4 have
   removed the duplication inside them. *(~3 hrs.)*
6. **Wire `check_atomic.py` into CI** so this does not come back.
````

## 6. Present and stop

Summarise in chat: the count by severity, the one thing that matters most, and the
plan's first step. Then wait. Do not begin editing.

## 7. On approval

Work the plan in order — the ordering exists because doing step 5 before step 3
means splitting components that are about to lose half their content. Re-run the
validator at the end and report the new counts against the old ones.

## CI

```bash
python3 scripts/check_atomic.py src --strict
```

Exits `1` on any error, and on warnings too under `--strict`. Add it beside the
lint step so violations fail where they were introduced.
