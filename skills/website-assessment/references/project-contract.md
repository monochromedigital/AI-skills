# The project contract

The shared agreement between every skill that works on the same website
project: `website-assessment`, `sitemap-ia-board`, and anything added later.

It exists because these skills produce documents that must agree with each
other. An audit says the site has no service pages; an IA proposes them; the
proposal quotes the audit. If each skill invents its own folder, its own
identifiers, and its own copy of the other's text, the three documents drift
apart the first time anyone edits one of them.

The contract fixes four things: **where** files live (§1), **what** they are
called and who may write them (§2, §4, §5), **how** one document points at
something inside another (§3, §7), and **what happens when a file is missing**
(§8). §6 is the check that all of it held.

Where this file and a skill's own prompt disagree, this file wins.

---

## §1 · The project folder

Every run works inside one folder per client project. Ask for it at the start,
in the same `AskUserQuestion` call as the skill's other opening questions —
never as a separate round trip.

- **Default the name to a slug of the client.** `Northgate Logistics` →
  `northgate-logistics`. Lowercase, ASCII, hyphens, no dates in the name — a
  project is not a run.
- **Confirm the parent directory.** Do not assume the working directory. In a
  connected-desktop session this is a folder on the user's own machine and they
  care where it lands.
- **Reuse an existing folder.** If the folder is already there, work inside it.
  Never create `northgate-logistics-2`, never append a suffix, never start a
  fresh folder because the last run was a while ago. A second folder is how a
  client ends up with two sitemaps and no way to tell which one is current.
- **Everything the run produces goes inside it.** Screenshots, JSON, rendered
  reports, exports. Nothing lands in a temp directory and nothing lands beside
  the folder.

In an unattended session, take the client slug under the current working
directory, state the assumption in the first line of the output, and proceed.

---

## §2 · `project.json`

The folder's identity card. The first skill to run writes it; every later skill
reads it and does not ask again for anything it already contains.

```jsonc
{
  "schema": 1,
  "slug": "northgate-logistics",
  "client": "Northgate Logistics",
  "url": "https://northgate.example",
  "market": ["Lebanon", "United Arab Emirates"],
  "languages": ["en", "ar"],
  "audience": "prospect",          // prospect | existing | internal
  "site_type": "service-business", // which site-types/ file governs, or "none"
  "agency": "daydream",            // §2a · required · no default
  "brand": null,                   // path, relative to the project folder, or null
  "created": "2026-08-04",
  "runs": [                        // append-only; one entry per skill run
    { "skill": "website-assessment", "on": "2026-08-04", "wrote": ["findings.json"] }
  ]
}
```

Rules:

- **Read before asking.** If `project.json` exists, the client, URL, market,
  audience, languages and brand are settled. Asking again invites the user to
  give a different answer, and now two documents disagree about the client's
  own name.
- **Extend, never overwrite.** A later skill may add fields it needs. It may
  not rewrite a field another skill set. If a value is genuinely wrong, tell
  the user and let them decide.
- **Append to `runs`.** It is the only record of what has been done in this
  folder, and it is what tells the next skill whether an audit exists.
- **`brand`** points at a brand file inside the project folder for a one-off
  override — a white-label report delivered under the client's own branding.
  Otherwise `null`, and `agency` governs. Setting both is not an error: the
  path wins, because it is the more specific instruction.

---

## §2a · `agency`

Which of the operator's agencies the deliverable goes out under. One slug,
resolved identically by every renderer through `scripts/brandkit.py`, which is
carried byte-identically alongside `render_report.py` for the same reason.

```
assets/brand.json                    the shared base · belongs to no agency
assets/brands/<slug>/brand.json      the agency · name, copyright line, palette
assets/brands/<slug>/logo-dark.svg   optional · for the dark header and slides
assets/brands/<slug>/logo.svg        optional · for light surfaces
```

Resolution order, first hit wins:

1. an explicit `--agency` flag on the command line — a one-off, not recorded
2. `project.json["brand"]` — the file-path override above
3. `project.json["agency"]` — the normal path
4. nothing. **The build fails.**

Rules:

- **There is no default agency.** The agencies are peers; none is the house
  one. A run that does not say which agency it belongs to fails, listing the
  installed slugs. This is the one degradation rule §8 does not get: every
  other missing file changes what the document contains, and the gap is
  visible. Wrong branding changes nothing visible — the document looks
  entirely finished, and nothing downstream catches it.
- **The base is nobody's brand.** `assets/brand.json` carries the category
  colours, the severity colours, the type scale and the deck geometry, and a
  neutral grey palette that is a placeholder rather than a brand. An agency
  file that forgets half its palette therefore renders as visibly unbranded
  instead of as some other agency's work, and the build says which keys fell
  through.

- **Asked once, in the opening `AskUserQuestion` call** (§1), alongside the
  project folder. Never as a separate round trip, and never a second time —
  the first skill to run writes it, and every later skill reads it. A skill
  that asks again invites a different answer, and now the audit and the board
  are branded by two different agencies.
- **An unknown slug fails the build**, non-zero, listing what is installed. A
  typo quietly falling back to the default is how a Monochrome deck goes out
  in Crackwits colours, and nothing about the output would say so.
- **Overlays, never copies.** An agency file carries only what it changes;
  everything else is inherited from the base and deep-merged. Copying the base
  and editing it means the next change to a category colour has to be made
  four times, and will be made in three.
- **Category and severity colours are shared, not per-agency.** They are
  functional encoding — a reader learns that orange means UX across every
  report they receive. An agency may override them, but it has to be typed
  deliberately into the agency file rather than inherited by accident.
- **A missing logo degrades to text**, which is what happened before logos
  existed. It is not a build failure. A broken `<img>` in a document already
  sent to a client is worse than no logo at all.
- **Logos are embedded, never linked.** These documents are single files that
  have to open offline, in an email client, and after the CDN link has rotted.

---

## §3 · Finding identifiers

Every finding carries an `id`. It is the handle other documents use to point at
it, and the anchor a deep link resolves to.

**Content-derived, generated once, then frozen.**

```
key = normalise(page) + "\x1f" + normalise(section) + "\x1f" + normalise(observation)
id  = "f-" + sha256(key.utf8).hexdigest()[:10]
```

`normalise` is: Unicode NFKC, casefold, collapse all whitespace runs to a
single space, strip. Nothing else — no punctuation stripping, because
punctuation is meaning in a sentence.

The id matches `^f-[0-9a-f]{10}$`.

- **Generated on first write.** A finding written without an `id` gets one
  derived from its own content at the moment `findings.json` is written.
- **Frozen once present.** A finding that already has an `id` keeps it, even if
  its observation is later reworded. The derivation is how the id is *born*,
  not a checksum re-verified on every build. This is the whole point: an id
  that changed when someone fixed a typo would break every reference to it.
- **Unique across the project.** Assert it at write time. A collision means two
  findings share a page, a section and an observation — that is a duplicate, not
  a hash accident, and the build fails so it gets fixed rather than silently
  merged.
- **Positional ids are the failure this replaces.** `s3f2` resolves to whatever
  is third-and-second *today*. Reorder the slides and every reference in every
  other document silently points at a different finding — it does not error, it
  lies. A content-derived id that no longer exists fails loudly instead.

---

## §4 · File layout and ownership

```
<project-folder>/
  project.json          §2   first skill writes · everyone reads
  findings.json         §3   website-assessment writes · everyone reads
  ia.json               §5   sitemap-ia-board writes · everyone reads
  research.json              website-assessment writes · everyone reads
  page-data.json             capture.py writes · everyone reads
  report-data.json      §6   build_data.py writes · build_site.py reads
  brand.json                 optional per-project brand override
  screens/                   raw screenshots
  framed/                    device-framed screenshots (deck only)
  out/                       every rendered deliverable
    report.html  ·  report/  ·  assessment.pptx  ·  sitemap.html  ·  *.csv
```

**One writer per file.** The owning skill writes it; everyone else opens it
read-only. A renderer never writes its own input — `build_site.py` reading and
rewriting `findings.json` would mean the deck and the report were built from
different files while appearing to share one.

**Nothing outside `out/` is a deliverable.** The JSON is working state. When the
user asks for the report, they get `out/`.

---

## §5 · `ia.json`

The information-architecture document, written by `sitemap-ia-board` and read
by the shared renderer. Full field notes live in that skill; the contract fixes
only the shape and the cross-references.

```jsonc
{
  "schema": 1,
  "evidence": { "note": "...", "counts": {}, "clusters": [] },
  "personas": [{
    "id": "p-ops-manager", "name": "...", "role": "...",
    "weight": "...", "colour": "#...", "quote": "...", "context": "...",
    "wants": ["..."],
    "blocked_by": [{ "text": "...", "fid": "f-1a2b3c4d5e" }],
    "journey": ["home", "services"],
    "needs_pages": ["services"]
  }],
  "funnels": [{ "name": "...", "temp": "hot|warm|cold", "path": "...", "note": "..." }],
  "pages": [{
    "id": "services", "name": "Services", "slug": "/services",
    "phase": 1, "template": false, "isnew": true,
    "plain": "the In-plain-words box",
    "sections": [{
      "t": "...", "d": "...", "chips": ["UX", "CRO", "SEO", "LEAD"],
      "phase": 2, "fid": "f-1a2b3c4d5e"
    }]
  }],
  "db": { },        // optional · standalone board only · renderer ignores
  "glossary": [ ]   // optional · standalone board only · renderer ignores
}
```

- `pages[].id` and `personas[].id` are author-chosen slugs, unique within their
  own array. `journey` and `needs_pages` hold `pages[].id` values.
- `phase` is `1` (launch) or `2` (later). Absent means `1`.
- `chips` come from `["UX", "CRO", "SEO", "LEAD"]` plus language codes.
- `db` and `glossary` are for the standalone board. The shared renderer ignores
  them rather than failing on them, so the skill can keep emitting them.

---

## §6 · Validation

The renderer validates before it emits anything. A build that would produce a
broken document fails instead, non-zero, with the JSON path of every offending
node. **It never writes a partial file** — a half-valid report is worse than no
report, because it gets sent.

`build_site.py` checks, in order:

1. `report-data.json` carries the expected `schema`.
2. Every finding has an `id` matching `^f-[0-9a-f]{10}$`.
3. Ids are unique across the whole project.
4. Every `marker.x` / `marker.y` is within `0…1`.
5. Every image path referenced resolves to a file that exists, or the section
   is explicitly marked as having no screenshot.
6. `stats.findings` reconciles with the number of findings actually present.
7. **If `ia.json` is present:** its `schema` matches; every `sections[].fid`
   and every `personas[].blocked_by[].fid` resolves against `findings.json`;
   every `journey` and `needs_pages` entry resolves to a `pages[].id`; every
   chip is in the allowed set; every `phase` is `1` or `2`; `pages[].id` and
   `personas[].id` are each unique.

Error format, one line per failure:

```
ia.json: personas[2].blocked_by[0].fid = "f-9f3c1a77b0" does not resolve
ia.json: pages[4].sections[1].chips[2] = "PERF" is not an allowed chip
findings.json: slides[1].findings[3].id is missing
```

---

## §7 · Cross-references

One document points at another **by id and only by id**.

- A section card that exists because of an audit finding carries that finding's
  `fid`. One reference, the id alone.
- **Never copy the audit's text into `ia.json`.** The renderer resolves the
  `fid` and shows the finding's current wording. Copied text is a snapshot: the
  moment anyone rewords the finding, the IA quotes something the audit no
  longer says, and nothing errors — the two documents just quietly disagree.
- **Never invent a `fid`.** If no audit exists, emit no `fid` anywhere. A
  reference that does not resolve fails the build (§6), which is the intended
  behaviour, but a build that fails because someone guessed is wasted time.
- One `fid` per section card. If two findings justify a section, the section is
  probably two sections, or one of the two findings is the real reason.

---

## §8 · Degradation

Each file is optional, and the absence of one changes the output rather than
breaking it.

| Present | Views |
|---|---|
| `findings.json` + `ia.json` | Home · Audit · Summary · **Personas** · **Sitemap** · Action items |
| `findings.json` only | Home · Audit · Summary · Action items |
| `ia.json` only | Home · **Personas** · **Sitemap** — the greenfield board, same renderer |
| either, plus `ia.db` | adds **Database** |
| either, plus `ia.glossary` | adds **Glossary** |
| neither | Nothing to render |

One renderer draws all of these — `scripts/render_report.py`, carried
byte-identically by every skill that produces a report. An audit report and a
greenfield board are the same document with different sections present. The
moment they were two codebases they started looking like two agencies.

**Remove, do not disable.** In the four-view build, the Personas and Sitemap
nav items and their Home cover cards are absent from the DOM — not greyed out,
not present-and-erroring on click. A user who can see a tab expects it to work,
and a tab that opens an empty view reads as a broken report, which is exactly
the impression these documents exist to avoid.

Routes are defensive to match: `#/personas` on a four-view build resolves to
Home rather than rendering nothing. People paste links.

Exactly one nav tab is active on every view, including after a re-render.
Two active tabs, or none, is the visible symptom of a routing bug —
see the note on `classList.toggle(cls, force)` in the skills' own docs.
