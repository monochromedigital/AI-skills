# findings.json

The single contract between the audit and every renderer. It lives in the
project folder (`references/project-contract.md` §1) and it is written once:
then `build_deck.py` makes the PPTX, `build_data.py` → `build_site.py` makes
the interactive web report, the Figma plugin makes the same slides, and
`ia.json` points back at individual findings by id.

**Never fork this file per output.** A finding edited for the deck and not for
the report is how a client ends up quoting a number back at you that no longer
exists. Every renderer reads the same JSON, and each ignores the fields it does
not use.

**Nothing downstream writes it.** Contract §4 is one writer per file. The only
script that ever edits `findings.json` is `finding_ids.py`, and only to stamp
the ids below.

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
    "footer_right": "Website Audit"   // optional · overrides the default label
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
          "id": "f-2b7c7a60d1",                           // stamped by finding_ids.py
          "categories": ["UI Design", "Accessibility"],   // 1–3 tags
          "severity": "Moderate",                          // Critical|Moderate|Minor
          "observation": "The green header feels visually heavy and creates a low-contrast navigation area, making the menu harder to read and scan.",
          "detail": "Optional second paragraph for evidence or explanation.",
          "fix": "Concrete recommended change.",
          "benchmark": "Baymard Institute, 2026 — extra costs are the top abandonment reason, cited by 40%",   // optional, researched only
          "principle": "Visual Hierarchy",                 // optional, sparing
          "scope": "Applicable on all the website and also on footer",  // optional, renders bold
          "track": "now",                                  // optional: now | revamp (web report)
          "effort": "S",                                   // optional: S | M | L  (web report)
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

## `id`

Every finding carries one. It is the handle the IA uses to cite a finding, the
anchor a deep link resolves to, and the first column of the CSV export.

Do not write it by hand. Stamp the file after you finish writing findings:

```bash
python3 scripts/finding_ids.py --findings <project>/findings.json
python3 scripts/finding_ids.py --findings <project>/findings.json --check   # verify only
```

It derives `f-` plus ten hex characters from the finding's own page, section
and observation (contract §3), leaves any id already present alone, and fails
if two findings collide — which means two findings share a page, a section and
an observation, so one of them is a duplicate.

**Frozen once written.** Reword an observation and the id stays. That is the
point: an id that changed when someone fixed a typo would break every `fid` in
`ia.json` pointing at it.

**This replaces positional ids.** `s3f2` meant "third slide, second finding",
so reordering the slides silently repointed every reference — it did not error,
it pointed at the wrong finding. A content-derived id that no longer exists
fails the build instead.

`build_data.py` refuses to run on a `findings.json` with a missing or malformed
id rather than deriving one in memory, because an id that never reaches the
file is an id nothing else can reference.

## `track` and `effort`

Both are optional, both are read only by `build_site.py`, and both are ignored
by `build_deck.py` and the Figma plugin — adding them can never break the PPTX
path.

`track` — where the fix belongs in the programme of work:

- `"now"` — deliverable against the current build, no new foundation required
- `"revamp"` — needs a new content model, template set, or design system

Required only when the client asked for the now-vs-revamp split. Findings left
untracked collect under an "Unassigned" heading in the report rather than
disappearing, so a partial pass is visible rather than silent.

`effort` — implementation size, from the agency's side:

- `"S"` — under a day
- `"M"` — one to three days
- `"L"` — a week or more of structural work

Required only when effort sizing was requested. Action items sort by severity
first and effort second, so within a severity band the quick wins surface at
the top.

Cost bands are not a schema field. They are derived from `effort` at build time
via `build_site.py --cost-bands "S=...,M=...,L=..."`, because the mapping is
per-client and per-engagement and does not belong in a file you hand to anyone.

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
