# Stacks: detection and token strategy

There is no default stack. Read the project, then use the matching strategy. If the
project already has a working token layer under a different name, use that one —
adding a second is the same failure as hardcoding.

## Detection

```bash
python3 scripts/check_atomic.py --detect <project-root>
```

Manually: read `package.json` `dependencies` + `devDependencies`, then look for the
config files below. Two things are being identified — the **framework** (which
decides file conventions and where the page layer lives) and the **styling layer**
(which decides the token format).

| Found | Framework |
| --- | --- |
| `next` | Next.js — pages are `app/**/page.tsx` or `pages/**`; `layout.tsx` is the template |
| `react` without `next` | React SPA — pages are route components |
| `react-native`, `expo` | React Native — no CSS at all |
| `vue`, `nuxt` | Vue — SFCs, tokens in `<style>` or a theme module |
| `svelte`, `@sveltejs/kit` | Svelte — `+page.svelte` is the page layer |
| `@angular/core` | Angular — tokens in global SCSS, components are `.component.ts` |

| Found | Styling layer |
| --- | --- |
| `tailwindcss` | Tailwind — see below |
| `styled-components`, `@emotion/*`, `stitches` | CSS-in-JS — typed theme object |
| `@vanilla-extract/*` | vanilla-extract — `createThemeContract` |
| `*.module.css`, `sass`, `less` | CSS Modules — custom properties in one file |
| `components.json` + `components/ui/*` | shadcn/ui on top of Tailwind |
| none of the above | Plain CSS — custom properties in one file |

## Tailwind (v3 and v4)

Tokens are CSS custom properties, surfaced as theme keys so utilities carry
meaning. Components use the semantic utility, never the raw value.

**v4** — one CSS file, `@theme`:

```css
@theme {
  --color-brand: oklch(0.55 0.19 260);
  --color-surface: oklch(0.99 0 0);
  --color-surface-subtle: oklch(0.97 0 0);
  --spacing-gutter: 1.5rem;
  --radius-md: 0.5rem;
  --font-sans: "Inter", system-ui, sans-serif;
}
```

**v3** — `tailwind.config.ts`, pointing at variables so themes can swap at runtime:

```ts
theme: {
  extend: {
    colors: {
      brand:   'rgb(var(--color-brand) / <alpha-value>)',
      surface: 'rgb(var(--color-surface) / <alpha-value>)',
    },
    borderRadius: { md: 'var(--radius-md)' },
    spacing:      { gutter: 'var(--spacing-gutter)' },
  },
}
```

Then `bg-brand`, `p-gutter`, `rounded-md`. Never `bg-[#2563eb]`, never `p-[24px]`.

Register `tailwind.config.*` and the CSS file holding `@theme` as the `tokens`
layer in `atomic.config.json` so the validator does not flag the raw values there —
that file is the one place they are allowed.

## shadcn/ui

shadcn copies source into your repo. Those files **are** your atom layer. Do not
wrap them; retoken them.

1. Point `components.json` at `components/ui`.
2. Replace the default CSS variables in your globals file with your real scale —
   the shadcn variable names (`--background`, `--primary`, `--muted-foreground`,
   `--radius`) stay, their values become yours.
3. Edit the vendored components' variants to use your tokens. When a component
   needs a variant your design has and shadcn does not, add it to the vendored file
   rather than overriding with `className` at every call site.
4. Feature code imports `@/components/ui/button` — the vendored path is now your
   own atom path, so this is not a vendor import.

## CSS-in-JS (styled-components, Emotion, Stitches)

A typed theme object is the token layer, provided once at the root.

```ts
// src/tokens/theme.ts
export const theme = {
  color:   { brand: '#2563eb', surface: '#ffffff', textMuted: '#6b7280' },
  space:   { xs: '4px', sm: '8px', md: '16px', lg: '24px', xl: '40px' },
  radius:  { sm: '4px', md: '8px', full: '9999px' },
  font:    { sans: '"Inter", system-ui, sans-serif' },
  size:    { body: '16px', h1: '40px' },
  shadow:  { card: '0 1px 3px rgba(0,0,0,0.08)' },
  motion:  { fast: '120ms', base: '200ms' },
} as const

export type Theme = typeof theme
```

Components read `({ theme }) => theme.space.md` and never a literal. Register
`src/tokens/**` as the `tokens` layer.

## vanilla-extract

```ts
// src/tokens/contract.css.ts
export const vars = createThemeContract({
  color: { brand: null, surface: null },
  space: { sm: null, md: null, lg: null },
})
```

Themes implement the contract; components reference `vars.*` only. The contract and
theme files are the `tokens` layer.

## CSS Modules / plain CSS / Sass

One file of custom properties on `:root`, imported once at the app entry.

```css
/* src/tokens/tokens.css */
:root {
  --color-brand: #2563eb;
  --color-surface: #ffffff;
  --space-md: 16px;
  --radius-md: 8px;
  --shadow-card: 0 1px 3px rgb(0 0 0 / 0.08);
}
```

Module files use `var(--space-md)` and never a literal. Sass variables are
acceptable as an authoring layer but the runtime values still come from custom
properties, otherwise theming at runtime is impossible.

## React Native

No CSS. The theme is a plain TS object; there is no cascade, so it must be passed
through context or imported directly.

```ts
// src/tokens/theme.ts
export const theme = {
  color:   { brand: '#2563eb', surface: '#ffffff' },
  space:   { xs: 4, sm: 8, md: 16, lg: 24 },   // numbers, not strings
  radius:  { sm: 4, md: 8 },
  type:    { body: { fontSize: 16, lineHeight: 24 } },
}
```

`StyleSheet.create` reads from `theme`; no numeric literal appears in a style
object. The layer model is unchanged — `components/ui/` holds the RN primitives
wrapped as atoms (`Text`, `Pressable`, `View` compositions), features hold domain
organisms, screens are the page layer and own navigation and data.

## Vue / Nuxt

Tokens as custom properties in one global stylesheet, or a Tailwind theme if
Tailwind is present. The layer model maps directly: `components/ui/` for atoms and
molecules, `components/layout/`, `components/<feature>/` or `features/`, and
`pages/**` or `app/**` as the page layer. Composables that fetch data or read the
router belong to the page layer, not to components.

## Svelte / SvelteKit

Custom properties in `app.css`, or Tailwind. `+page.svelte` and `+page.ts` are the
page layer and own `load`, stores, and navigation. `$lib/components/ui/` is the atom
layer. Component-scoped `<style>` blocks must still reference `var(--token)`.

## Angular

Tokens as custom properties in `styles.scss`. Components at every layer are
`.component.ts` + template + scoped styles; the layer distinction is made by what
the component injects. A component injecting `HttpClient`, a store, or `Router` is
a page-layer component — those injections do not belong in a shared UI component.

## Wrapping vendor libraries

For anything installed from `node_modules` — MUI, Radix, Chakra, Mantine, Ant —
write one thin atom per primitive:

```tsx
// src/components/ui/Button.tsx
import { Button as MuiButton } from '@mui/material'
import type { ReactNode } from 'react'

type Props = { variant?: 'primary' | 'ghost'; onClick?: () => void; children: ReactNode }

export function Button({ variant = 'primary', ...rest }: Props) {
  return <MuiButton disableElevation color={variant === 'primary' ? 'primary' : 'inherit'} {...rest} />
}
```

The wrapper exposes *your* prop vocabulary, not the vendor's. Forwarding the
vendor's entire prop type defeats the purpose — the coupling just moves into the
type signature. Feature and page code import `@/components/ui/Button`, and the
validator flags any file outside `components/ui/` that imports the vendor path
directly.
