# findings.json

The single contract between the audit and both renderers. Write this file, then
`build_deck.py` makes the PPTX and the Figma plugin makes the same slides.

```jsonc
{
  "meta": {
    "client": "Embassy of Lebanon — United Arab Emirates",  // cover + group name
    "url": "https://example.com",
    "audited_on": "2026-08-03",
    "audience": "prospect",          // prospect | existing | internal (framing only)
    "site_type": "ecommerce",        // which site-types/ file governed the audit
    "cover": true,                   // include a cover slide
    "show_severity": true,           // severity pill on each card
    "show_fix": true,                // "Fix: ..." line
    "show_benchmark": true,          // "Benchmark: ..." line
    "show_principle": true,          // "Principle: ..." line
    "priority_slide": true,          // ranked Critical/Moderate slide at the end
    "footer_right": "Website UX/UI Assessment"
  },

  "slides": [
    {
      "page": "Landing Page",        // eyebrow (blue)
      "section": "Nav Bar",          // title (white)
      "framed": "framed/home__00-nav-bar.png",   // output of frame.py
      "screenshot": "screens/home__00-nav-bar.png", // raw, used if framed missing
      "screen_rect": {               // from frame.py — maps marker coords
        "x": 0.043, "y": 0.055, "w": 0.914, "h": 0.889
      },
      "findings": [
        {
          "categories": ["UI Design", "Accessibility"],   // 1–3 tags
          "severity": "Moderate",                          // Critical|Moderate|Minor
          "observation": "The green header feels visually heavy and creates a low-contrast navigation area, making the menu harder to read and scan.",
          "detail": "Optional second paragraph for evidence or explanation.",
          "fix": "Concrete recommended change.",
          "benchmark": "Baymard Institute, 2026 — extra costs are the top abandonment reason, cited by 40%",   // optional, researched only
          "principle": "Visual Hierarchy",                 // optional, sparing
          "scope": "Applicable on all the website and also on footer",  // optional, renders bold
          "marker": { "x": 0.050, "y": 0.047 }             // see below
        }
      ]
    }
  ],

  "summary": {
    "image": "framed/home__00-nav-bar.png",
    "narrative": ["para 1", "para 2", "para 3"],
    "counts": { "Copy / Content": 14, "UX Design": 13 }   // omit to auto-count
  }
}
```

## `site_type` and `benchmark`

`meta.site_type` records which file in `site-types/` governed the audit. It is
not rendered; it exists so a rebuild, a second-round audit, or another person
picking up the deck applies the same lens. Use the filename without the
extension: `ecommerce`, `saas`, `service-business`, `corporate`,
`content-publisher`, `marketplace`, `nonprofit-education`, or `none`.

`benchmark` renders as its own muted line under the fix, in the same slot as
`principle`. It carries external evidence and nothing else:

- Only for figures researched **during this session** and recorded in
  `research.json`. Never from memory
- Attribute it — source and year, e.g.
  `Baymard Institute, 2026 — 50-study average`
- Never use it for a number measured from the client's own page; that belongs
  in the observation, where it is stronger
- One per finding, and on far fewer findings than you will be tempted to. A
  deck where every card cites a statistic reads as padding

Set `show_benchmark: false` in `meta` for a denser deck; the text stays in the
JSON for the client's record.

## Marker coordinates

`marker.x` and `marker.y` are fractions **of the live screenshot**, where
`0,0` is its top-left and `1,1` its bottom-right — *not* of the framed PNG and
*not* of the slide. Both renderers map them through `screen_rect` to account
for the device bezel and drop shadow.

Get them from `page-data.json`, which `capture.py` writes. Every element
carries a `rel` block relative to its section:

```json
{ "tag": "a", "sel": "header > nav > a:nth-of-type(1)", "text": "HOME",
  "rel": { "x": 0.39, "y": 0.03, "w": 0.05, "h": 0.04 } }
```

Point the marker at the element's edge, not its centre, so the label stays
readable: `x = rel.x`, `y = rel.y + rel.h / 2` puts it on the left edge.
For a whole-region finding (a full header, a whole section), place it on the
left margin at the region's vertical midpoint.

Markers are numbered automatically, in array order, starting at 01 per slide.

## Pagination

Cards are measured and split automatically — a section with 9 findings becomes
two slides, the second titled "Nav Bar (cont.)". Do not pre-split.

If cards are running long and you want denser slides, set `show_fix` or
`show_principle` to `false` in `meta`; the copy stays in the JSON for the
client's own record.

## Counts

Omit `summary.counts` and the count is derived from the findings — a finding
with two tags counts once under each, which is why the reference deck's totals
exceed its finding count. Supply `counts` explicitly only when reconciling with
a hand-built number.
