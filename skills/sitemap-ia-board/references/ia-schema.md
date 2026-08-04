# ia.json

The structured record of the board. It is what the shared renderer in the
`website-assessment` skill consumes to draw the Personas and Sitemap views, and
what any later skill reads to know what was proposed.

**It is a serialisation of the thinking, not a replacement for it.** The quality
bar in `SKILL.md`, the phase discipline, the lead-capture layering and the
In-plain-words formula in `references/methodology.md` all still apply — do that
work first, then write it down in this shape. A file filled in without the
reasoning behind it produces a board that validates and says nothing.

Written into the project folder as `ia.json`. Contract §4: this skill owns it,
everyone else reads it.

```jsonc
{
  "schema": 1,

  "evidence": {
    "note": "Where the personas come from, in plain language. Say so when there is no research.",
    "counts": { "installations": 50, "with_named_client": 41 },
    "clusters": [ { "name": "Bonded warehousing", "n": 22 } ]
  },

  "personas": [{
    "id": "p-ops-manager",          // unique within personas[]
    "name": "Rana",
    "role": "Operations manager, food importer",
    "weight": "22 of 50 installations",
    "colour": "#DF6630",
    "quote": "I need to know you can hold 40 pallets bonded before I call anyone.",
    "context": "Two or three sentences: what they are judged on, how they buy.",
    "wants": ["Bonded capacity in square metres, stated on the page"],
    "blocked_by": [
      { "text": "Cannot tell from the homepage whether the service exists",
        "fid": "f-c4d0510ece" }   // the id ONLY, never the finding's words
    ],
    "journey": ["home", "bonded-warehousing", "enquiry"],   // pages[].id values
    "needs_pages": ["bonded-warehousing", "enquiry"]        // the pages this persona caused
  }],

  "funnels": [{
    "name": "Service funnel",
    "temp": "hot",                  // hot | warm | cold
    "path": "Home → Service page → Enquiry → Thank you",
    "note": "Why it exists, or what is wrong with the one that exists today."
  }],

  "pages": [{
    "id": "bonded-warehousing",     // unique within pages[]; what journey/needs_pages point at
    "name": "Bonded warehousing",
    "slug": "/services/bonded-warehousing",
    "phase": 1,                     // 1 launch · 2 later
    "template": true,               // renders many records from one design
    "isnew": true,                  // does not exist on the current site
    "plain": "The In-plain-words box. Metaphor, then one named actor doing one thing.",
    "sections": [{
      "t": "Capability header",
      "d": "Why this section earns its place — not what it is.",
      "chips": ["SEO", "CRO"],      // UX · CRO · SEO · LEAD, plus language codes
      "phase": 1,
      "fid": "f-51ef98a384"         // optional: the finding that justifies it
    }]
  }],

  "db": { },        // optional · standalone board only · the shared renderer ignores it
  "glossary": [ ]   // optional · standalone board only · the shared renderer ignores it
}
```

## The rules that are actually enforced

`scripts/validate_ia.py` fails the build on each of these, naming the JSON path:

- `schema` is `1`
- `pages[].id` and `personas[].id` are present and unique within their arrays
- every `journey` and `needs_pages` entry resolves to a `pages[].id`
- every `fid` matches `^f-[0-9a-f]{10}$` **and** resolves against
  `findings.json`
- **no `fid` at all** when the project has no `findings.json`
- every chip is `UX`, `CRO`, `SEO`, `LEAD`, or a language code
- every `phase` is `1` or `2`
- every page has a `plain` box and at least one section
- every section has a title, a description and at least one chip — a card that
  earns no chip earns no place
- every persona has `needs_pages` — a persona that changes nothing does not
  belong in the document
- `evidence.note` is present when an audit exists

```bash
python3 scripts/validate_ia.py --ia <project>/ia.json
python3 scripts/validate_ia.py --ia <project>/ia.json --board <project>/out/sitemap.html
```

## `db` and `glossary`

They stay here, and they stay in the standalone board. The shared renderer
ignores them rather than failing on them, so this skill can keep emitting them
without the assessment skill needing to know what a CMS table is.

Everything about how to design them is in `references/methodology.md`
§ Database patterns.
