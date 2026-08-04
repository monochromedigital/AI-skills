# Agency brands

One folder per agency the work goes out under. The folder name is the slug that
goes in `project.json["agency"]`, and it is the only thing a run needs to be
told to wear the right branding everywhere.

**There is no default agency.** The four are peers. A run that does not say
which one it belongs to fails and lists the installed slugs, rather than
picking one — every other missing input leaves a visible gap in the document,
but wrong branding produces something that looks entirely finished, so the
build is the only place it can be caught.

```
brands/
  crackwits/
    brand.json        overlay - only what differs from ../brand.json
    logo-dark.svg     for the report header and every deck slide (both dark)
    logo.svg          for light surfaces (optional today, used if added)
  monochrome/
  daydream/
  all-in/
```

## Overlays, not copies

`assets/brand.json` is the **shared base, and it belongs to no agency**. It
stays byte-identical across both skills, exactly as the contract requires, and
it carries everything shared: the seven category colours, the three severity
colours, all deck layout geometry, all type tokens.

Its palette is a deliberate **neutral grey** — a placeholder, not a brand.
That is what makes an incomplete agency file safe: a palette missing half its
keys renders as visibly unfinished, and `brandkit` prints which keys fell
through. If the base carried a real agency's colours, the same mistake would
render as a finished-looking document belonging to the wrong company.

An agency file carries its name, its footers and its palette. Anything absent
is inherited from the neutral base. Deep-merged, so an agency that overrides
one colour keeps the rest; lists are replaced whole rather than concatenated,
because a partial list of category colours would be meaningless.

A handful of colour keys are structural rather than brand — `panel`, `card`,
`title`, `marker_text`, `tag_text`, `rule`. Inheriting those is normal and
draws no warning.

## Category colours stay constant on purpose

The seven discipline colours (Copy blue, UX orange, UI green, Dev purple, SEO
pink, Accessibility grey, CRO teal) are functional encoding, not decoration. A
client who reads three of these reports learns them. An agency that recolours
them is making its own documents harder to read for no gain.

Nothing prevents an override — it just has to be typed deliberately into the
agency file rather than inherited by accident.

## Logos

No logo files ship with this repo, on purpose: a placeholder wordmark that
reaches a client is worse than no logo at all. Every surface degrades to the
agency name as text when a logo is absent, which looks intentional.

To add one, drop `logo-dark.svg` into the agency folder. Requirements:

- **SVG, not PNG.** It is embedded as a base64 data URI in a single-file HTML
  report and scales to any header height. PNG is accepted but looks soft on a
  retina screen.
- **Legible on a dark background.** The report header is `colors.background`
  and every deck slide is too. If the wordmark is dark ink, you need a light
  variant, not the original file.
- **Roughly 4:1 or wider.** It renders at 20px tall in the header. A tall
  stacked lockup shrinks to nothing at that height — use the horizontal
  version.
- **Small.** Under ~20 KB. It is inlined into every report, and an oversized
  embedded raster is the fastest way to a 40 MB deliverable.

Add `logo.svg` as well if a light-background variant exists; it is picked up
automatically when a light surface needs it.

## Checking your work

```bash
python3 scripts/brandkit.py
```

Prints every installed agency, the display name it resolves to, and whether a
logo was found. Run it after adding a folder, before a client run depends on
it.

## Before the first real run

`crackwits` is complete — its palette is the one these documents have always
used, moved out of the base into its own file so it stops being structurally
privileged.

The other three are not. `monochrome` and `daydream` carry placeholder
palettes, chosen only so a report renders legibly during setup. `all-in` is
seeded from the indigo/emerald tokens used on the CompoundIn work, which may be
that project's design system rather than the agency's own brand.

Replace all three with real values. `python3 scripts/brandkit.py` and the
build's own stderr will both tell you which colour keys are still falling
through to the neutral base.
