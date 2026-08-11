# The layers

Brad Frost's five layers, plus the one underneath them that his book assumes and
code cannot: tokens. The definitions below are written so a component's layer can
be decided by asking questions about the component, not by taste.

## Tokens

The values every other layer refers to. Colour, spacing scale, radii, type scale,
font weights, shadows, breakpoints, z-index steps, motion durations and easings.

Tokens import nothing. They are the bottom of the graph, and they are the only
place a raw value may appear in the codebase.

A token layer with two homes is not a token layer. If the project has a
`tailwind.config.js` theme *and* a `theme.ts` *and* a `variables.css`, one of them
is real and the others are drift — consolidate before doing anything else.

## Atoms

The smallest useful element: button, input, label, icon, text, avatar, badge,
spinner, divider.

An atom:

- imports tokens and nothing else
- has no state beyond its own presentational state (hover, focus, open/closed)
- fetches nothing, reads no store, touches no router
- contains no user-facing copy — text arrives as `children` or a prop
- would make sense, unchanged, in a completely different product

That last line is the test. If you cannot imagine this file in someone else's app
without editing it, it is not an atom.

## Molecules

Atoms combined into one unit with one job: a labelled input with its error message,
a search field (input + button), a price with its currency and strike-through, an
avatar with a name beside it.

A molecule:

- imports tokens and atoms
- may hold local state that only coordinates its own atoms
- still knows nothing about your business
- is still copy-free — labels and placeholders arrive as props

The distinction from an atom is composition, not complexity. A molecule is made of
atoms; an atom is made of markup.

## Organisms

A meaningful, self-contained section of an interface: site header, product card,
comment thread, checkout form, pricing table, nav.

An organism:

- composes molecules and atoms
- often handles a variable number of children — `{children}`, `items.map(...)`
- may orchestrate state across its parts (which tab is open, which row expanded)
- receives its data as props; it does not go and get it

Organisms split into two kinds, and this is the split that decides where the file
lives:

**Generic organisms** know nothing about your domain — a site header, a footer, a
modal shell, a data table that renders whatever columns it is given. They live in
`components/layout/` and are importable by every feature.

**Domain organisms** know your business exists — `ProductCard`, `CheckoutForm`,
`InvoiceRow`. Their prop types name your entities. They live under
`features/<feature>/components/` and are importable only by that feature and by
pages.

## Templates

The page's skeleton: organisms placed into a layout, with no real data. Slots,
regions, grid, spacing.

A template must render standalone from props alone. The practical test, from the
atomic-engineering source: if the template cannot be rendered in Storybook — or in
any isolated harness — **without wrapping it in providers**, it is coupled to
application state and it is not a template yet.

Templates may use presentational libraries. They may not use your store, your
router, your API client, or your auth context.

In a Next.js App Router project, `layout.tsx` is usually the template. In other
setups, a `*Template.tsx` under `components/templates/`.

## Pages

The template filled with real data. **This is where application logic lives, and it
is the only layer where it may live.**

A page:

- calls the API, reads and writes global state, reads the router, checks auth
- handles loading, empty, and error states
- passes everything downward as props

Everything above this layer is a pure function of its props. That is the entire
point of the arrangement: it makes components testable without mocks beyond props,
portable between projects, and extractable into a component library without
touching application logic.

## The classification test

Four questions, in order. The first "yes" is the answer.

1. **Is it a raw value?** → token
2. **Does it own data fetching, global state, routing, or auth?** → page
3. **Does its API name your business entities?** → domain organism, under its feature
4. **Is it built from other components?** → molecule if it does one job from atoms;
   generic organism if it composes molecules, takes variable children, or coordinates
   state across parts

Otherwise: atom.

When 3 and 4 both seem true, 3 wins — domain knowledge decides the folder, and the
molecule/organism distinction inside a feature has no consequences.

## Dependency direction

The rule that replaces the naming argument. Each layer has a rank; imports may only
point at an equal or lower rank.

```
tokens (0)  ←  ui (1)  ←  layout (2)  ←  feature (3)  ←  page (4)
```

- Nothing imports a page. Ever.
- `ui` imports tokens and `ui`.
- `layout` imports tokens, `ui`, `layout`.
- `feature` imports tokens, `ui`, `layout`, and **its own feature only**.
- `page` imports anything.

Cross-feature imports are violations even though both sides are rank 3. If
`features/checkout` needs something from `features/catalog`, that something is
shared and belongs at a lower rank — move it to `ui` or `layout`. The alternative
is two features that cannot be deleted independently, which is how a codebase stops
being modular without anyone deciding it should.

`scripts/check_atomic.py` enforces exactly this graph by reading import specifiers.

## Mapping onto an existing repo

Existing projects rarely use these folder names, and renaming everything is not the
job. Map instead — write the mapping into `atomic.config.json` and the same rules
apply to the folders that are already there:

```json
{
  "layers": {
    "tokens":  ["src/theme/**", "tailwind.config.ts"],
    "ui":      ["src/components/common/**", "src/components/ui/**"],
    "layout":  ["src/components/shared/**"],
    "feature": ["src/modules/*/**"],
    "page":    ["src/views/**", "app/**"]
  }
}
```

Any file matching no pattern is `unknown` and is checked for hardcoded values and
duplication but exempted from layer rules — so a partial mapping is useful
immediately and can be tightened over time. Do not propose a mass folder rename in
an audit unless the user asks for one; the dependency rules deliver most of the
value without moving a single file.
