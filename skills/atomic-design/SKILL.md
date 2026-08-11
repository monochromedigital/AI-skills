---
name: atomic-design
description: Build, audit, and scaffold front-end code the atomic way — tokens first, smallest component first, nothing hardcoded, nothing repeated. Use whenever the user is writing or restructuring UI code: "build this page/screen/section", "create a component", "make this reusable", "extract a component", "componentize this", "refactor this file, it's too big", "set up a design system", "add design tokens", "stop hardcoding colors/spacing/strings", "is this structured right", "review my component structure", "atomic design", "atoms molecules organisms", or when they paste a large single-file component and want it broken up. Also trigger when a new front-end project is being started and the folder structure, token layer, or component conventions have not been established yet. Detects the project's framework and styling layer rather than assuming one, enforces dependency direction between layers, and ships a validator (`scripts/check_atomic.py`) that finds hardcoded values, duplicated markup, oversized components, and illegal cross-layer imports.
---

# Atomic Design

Front-end code built the way Brad Frost's *Atomic Design* describes the interface — from the smallest piece upward — with the engineering rules that make it hold: values live in one place, components never repeat, and each layer only knows about the layers beneath it.

Two laws govern everything in this skill. Everything else is detail.

**Law 1 — Nothing is hardcoded.** Not a colour, not a spacing value, not a string of copy, not a URL, not a threshold. Every value has exactly one home and everything else refers to it.

**Law 2 — Nothing is built top-down, and nothing repeats.** You build the button before the form, the form before the page. The *second* time a piece of markup appears, it stops being markup and becomes a component. Not the third time. The second.

Law 2's second half is the Rule of Two, and it is the one people break most: a header copy-pasted into four routes, a card re-typed per page, a button styled inline "just this once". Each of those is a bug that hasn't happened yet.

## Which mode you're in

Read the request and pick one. If it's ambiguous, ask.

| The user is… | Mode | Go to |
| --- | --- | --- |
| Writing a new page, screen, section, or feature | **Build** | [Mode: Build](#mode-build) |
| Pointing at existing code and asking what's wrong with it | **Audit** | [Mode: Audit](#mode-audit) |
| Starting a project with no structure or token layer yet | **Scaffold** | [Mode: Scaffold](#mode-scaffold) |

All three start with the same step.

## Step 0 — Detect the stack. Never assume it.

There is no default framework and no default styling system. Read the project before writing a line.

```bash
python3 scripts/check_atomic.py --detect <project-root>
```

Or do it by hand — read `package.json` dependencies, then the config files:

| Signal | Tells you |
| --- | --- |
| `next`, `react`, `vue`, `svelte`, `@angular/core`, `react-native`, `expo` | Framework and therefore file/component conventions |
| `tailwindcss` + `tailwind.config.*` or `@theme` in a CSS file | Tokens belong in the Tailwind theme + CSS variables |
| `styled-components`, `@emotion/*`, `@vanilla-extract/*`, `stitches` | Tokens belong in a typed TS theme object |
| `*.module.css`, `sass`, `less` | Tokens belong in CSS custom properties in one file |
| `components/ui/*.tsx` + `components.json` | shadcn/ui — the vendored files **are** the atom layer |
| `@mui/*`, `@chakra-ui/*`, `@mantine/*`, `antd`, `@radix-ui/*` | `node_modules` library — must be wrapped |
| `react-native` with no CSS | Tokens are a TS theme consumed by `StyleSheet` |

Then read `references/stacks.md` for the token strategy that matches. **Match the project's existing conventions before imposing new ones** — if the repo already has a working token file under a different name, use it; don't create a second source of truth. A second source of truth is the same bug as a hardcoded value.

## The layer model

The atomic vocabulary stays. What changes is that a component's layer is determined by **what it knows about**, not by which folder someone filed it in — because "is a Card a molecule or an organism" is an argument with no answer, and "does this component know your business exists" has exactly one.

| Layer | Default home | May import | Knows about your business? |
| --- | --- | --- | --- |
| **Tokens** | `src/tokens/` | nothing | no |
| **Atoms** | `src/components/ui/` | tokens | no |
| **Molecules** | `src/components/ui/` | tokens, atoms | no |
| **Organisms** (generic) | `src/components/layout/` | tokens, ui | no |
| **Organisms** (domain) | `src/features/<feature>/components/` | tokens, ui, layout, own feature | yes |
| **Templates** | route layout, or `src/components/templates/` | tokens, ui, layout | no — structure only |
| **Pages** | `app/**/page.tsx`, `pages/**`, route components | anything | yes — this is where logic lives |

**Dependency direction is the enforcement mechanism.** Imports point downward only:

- Nothing imports a page.
- `components/ui/` imports tokens and other `ui` — never a feature, never a store, never an API client, never a router hook.
- A feature never imports another feature's internals. Shared things move down to `ui` or `layout`.
- Data fetching, global state, routing, and API calls live at the **page** layer and arrive everywhere else as props. This is the single rule that makes components testable, portable between projects, and extractable into a library without a refactor.

If a component in `ui/` needs `useSelector`, `useQuery`, `useRouter`, or `fetch`, it is in the wrong layer or it is taking the wrong input. Lift the data to the page and pass it down.

Full definitions, the classification test, and how the model maps onto existing repos that use different folder names: `references/layers.md`.

## UI libraries

The rule depends on how the library ships, not which one it is.

**Copy-in libraries (shadcn/ui and anything vendored into your repo).** The copied file already lives in your codebase — it *is* your atom. Edit it so it consumes your tokens. Do not wrap it in another component that only forwards props; that is a layer that does nothing and hides the real one.

**`node_modules` libraries (MUI, Radix, Chakra, Mantine, Ant).** Wrap. One thin atom per primitive in `components/ui/`, applying your tokens and exposing your prop names. Feature and page code imports `@/components/ui/Button` and never `@mui/material`. When the vendor changes or gets replaced, you touch those files and nothing else.

Either way the invariant is the same: **no file outside `components/ui/` imports a vendor UI package directly.** The validator checks this.

## Mode: Build

The order is not negotiable. Building top-down is how hardcoded values and duplicated markup get created in the first place — you write the page, then notice the button, and by then there are six of them.

1. **Read the design or the request and list the distinct pieces.** Name every repeated element you can see. A header appearing on three screens is one component, listed once.
2. **Tokens first.** Every colour, spacing step, radius, font size, weight, shadow, breakpoint, and motion duration the work needs must exist as a token before any component uses it. If a needed value has no token, add the token — never inline the value "for now".
3. **Atoms.** Build the smallest elements: button, input, label, icon, text. No business logic, no data fetching, no copy baked in. Every visual value comes from a token.
4. **Molecules.** Compose atoms into single-purpose units — a labelled field, a price with a currency, a search box. Still generic, still no business knowledge.
5. **Organisms.** Compose molecules into meaningful sections — site header, product card, checkout form. Domain-aware organisms go under their feature; site-wide ones go under `layout`.
6. **Template.** Lay the organisms out with no real data. If the template can't render in isolation with props alone, it is coupled to app state — fix that before continuing.
7. **Page.** Now, and only now, wire in data: API calls, state, routing, auth. The page passes everything downward as props.

Before you say it's done, run the validator (below) and fix what it finds.

**The Rule of Two in practice.** The moment you are about to write a second copy of anything — markup, a style block, a conditional, a formatting helper — stop and extract it. Put it at the lowest layer both users can reach. If two features need it, it belongs in `ui` or `layout`, not duplicated in each.

## Mode: Audit

Read `references/audit.md` for the full procedure and report format. Short version:

1. Detect the stack (Step 0).
2. Run the validator across the target:
   ```bash
   python3 scripts/check_atomic.py <project-root> --json > /tmp/atomic.json
   ```
3. Read the flagged files yourself. The script finds mechanical violations; it does not know which duplicated block is worth extracting or which oversized component is actually fine. Judge each one.
4. Write `ATOMIC-AUDIT.md` at the project root: violations grouped by severity, each with `file:line`, what the rule is, and the specific fix. End with a refactor plan ordered by what unblocks the most other fixes — which is almost always tokens first, then the Rule of Two extractions, then layer moves.
5. **Present the report and stop.** Do not edit code until the user approves the plan. On an existing codebase, layer moves touch import paths across the repo; that is their call, not yours.
6. Once approved, work the plan in order and re-run the validator at the end.

## Mode: Scaffold

Greenfield only. After Step 0:

1. Create the token layer in the form the detected stack wants (`references/stacks.md`). Populate it with a real scale — not placeholders — covering colour, spacing, radius, type, shadow, breakpoints, motion.
2. Create the folder structure from the layer table above.
3. Create `atomic.config.json` at the project root so the validator knows the layout:
   ```json
   {
     "root": "src",
     "layers": {
       "tokens":  ["src/tokens/**", "tailwind.config.*"],
       "ui":      ["src/components/ui/**"],
       "layout":  ["src/components/layout/**"],
       "feature": ["src/features/*/**"],
       "page":    ["src/app/**", "app/**", "src/pages/**", "pages/**"]
     },
     "maxComponentLines": 150,
     "duplicateMinLines": 4
   }
   ```
4. Build a starter atom set that proves the token wiring works end to end — Button, Input, Text, Stack, Card — each consuming tokens only.
5. Run the validator so the project starts clean.
6. Add the validator to the project's lint/CI step if one exists, so violations fail there instead of in review.

## The validator

`scripts/check_atomic.py` — stdlib Python 3, no dependencies, **read-only**. It never edits code; it reports so you can propose fixes and the user can approve them.

```bash
python3 scripts/check_atomic.py <path>              # human-readable report
python3 scripts/check_atomic.py <path> --json       # machine-readable findings
python3 scripts/check_atomic.py <path> --strict     # warnings fail too
python3 scripts/check_atomic.py --detect <path>     # stack detection only
python3 scripts/check_atomic.py <path> --only hardcoded-color,duplicate-markup
```

What it catches:

| Check | Severity | Catches |
| --- | --- | --- |
| `hardcoded-color` | error | `#hex`, `rgb()`, `hsl()` outside the token layer |
| `hardcoded-dimension` | error | Raw px/rem in inline styles and style objects |
| `arbitrary-utility` | error | Tailwind escape hatches like `w-[327px]`, `text-[#fff]` |
| `duplicate-markup` | error | The same block of markup appearing twice — Rule of Two |
| `layer-violation` | error | An import pointing upward, or across features |
| `vendor-import` | error | A vendor UI package imported outside `components/ui/` |
| `logic-in-component` | error | Data fetching, store, or router hooks below the page layer |
| `hardcoded-url` | error | Literal `http(s)://` outside config |
| `hardcoded-copy` | error | User-facing text baked into a `ui/` or feature component |
| `oversized-component` | warning | A file past `maxComponentLines` — an organism that never got split |
| `magic-number` | warning | Unexplained numeric literals outside a constants file |

Errors exit `1`. Warnings need judgement — an oversized file can be legitimate, and the script says so rather than pretending it knows.

Any check can be switched off per project via `"disable": ["hardcoded-copy"]` in `atomic.config.json`. `hardcoded-copy` is the one worth disabling on a project that has deliberately chosen not to have a content layer — leaving it on there produces noise, not findings. Turning off any of the others is a decision to state in the report, not a default.

## Non-negotiables

Check these before calling any front-end work finished.

- [ ] Every colour, spacing, radius, font size, shadow, and duration comes from a token. No literals in components.
- [ ] Nothing appears twice. Every repeated header, footer, button, card, or block is one component used many times.
- [ ] User-facing copy arrives as props or from a content layer — never baked into a `ui/` or feature component.
- [ ] URLs, endpoints, keys, and flags come from config or env.
- [ ] Named constants for thresholds, limits, and business rules — no bare numbers.
- [ ] Imports point downward only. No feature imports another feature.
- [ ] Nothing below the page layer fetches data, reads a store, or touches the router.
- [ ] No vendor UI package imported outside `components/ui/`.
- [ ] The work was built atoms-upward, not page-downward.
- [ ] `check_atomic.py` exits clean.

## References

- `references/layers.md` — the five layers in full, the classification test, mapping onto existing repos
- `references/no-hardcoding.md` — the five categories with before/after in each idiom
- `references/stacks.md` — detection and the token strategy per stack
- `references/audit.md` — audit procedure and the `ATOMIC-AUDIT.md` format

Source material: Brad Frost, *Atomic Design* (atomicdesign.bradfrost.com) for the layer model; "Atomic Design for Developers: Atomic Engineering" for the engineering translation — components decoupled from application logic by dependency injection, with state, API calls, and routing owned by the page layer.
