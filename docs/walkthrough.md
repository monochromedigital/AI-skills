# Walkthrough: one client, both skills

How `website-assessment` and `sitemap-ia-board` work on the same project, and
what the shared contract in `references/project-contract.md` is actually for.

Read this before either SKILL.md if you have never used them together. It is a
worked example, not a specification — where it and the contract disagree, the
contract wins.

The client here is invented. The failure modes are not.

---

## The setup

Meridian Dental: three clinics, one website, no relationship with the agency
yet. Week one is a pitch. Week two, if the pitch lands, is the redesign.

Two sessions, eight days apart, on two different machines, remembering nothing
between them. Everything that survives the gap is a file in one folder.

---

## Act one — the audit

> *Audit meridiandental.example for a pitch.*

### What it asks

Four questions, in one `AskUserQuestion` call:

| | Answer |
|---|---|
| Project folder | `meridian-dental`, under `~/Clients` |
| Which pages | The decisive journey for this kind of site |
| Audience | Prospect |
| Output | Interactive web report **and** PPTX deck |

Because the report was chosen, two follow-ups ride along in the same call:
delivery mode (single file, since this is going in an email) and action-items
depth (effort sizing and the now-vs-revamp split).

It does not ask about categories, severity, or the site type. The first two are
fixed. The third it works out in step two and confirms, which is cheaper for
you and more accurate than asking.

### What it does

Captures the homepage first, because that is what types the site. Reads it as a
service business, says so, and names the signal that drove it. Then goes back
for what a service-business audit actually requires — the service page and the
enquiry form — rather than collecting more homepage screenshots.

Researches the benchmarks it intends to cite, before writing, and records each
one in `research.json`. A benchmark found afterwards is decoration attached to
a finding that was already written.

Then it looks at the screenshots. Then it writes.

### The folder, after writing

```
~/Clients/meridian-dental/
  project.json          client, URL, market, languages, audience, site type
  findings.json         31 findings across 6 sections
  research.json         every benchmark, with its source
  page-data.json        contrast ratios, alt coverage, tap targets
  screens/              the raw captures
  framed/               device-framed, for the deck only
```

`project.json` is the part that matters in eight days. It is the only reason
the second session knows who this client is.

### Stamping and checking

```bash
python3 scripts/finding_ids.py --findings ~/Clients/meridian-dental/findings.json
python3 scripts/check_prose.py --project ~/Clients/meridian-dental
```

The first gives every finding a stable id derived from its own page, section
and observation. The second reads what you wrote:

```
findings.json: slides[2].findings[1].fix - "consider adding", "user-friendly" (agency cliche)
findings.json: slides[4].findings[0].observation - "seamless", "robust" (tier 1)
findings.json: summary.narrative[1] - "in terms of" (filler)
```

Three fields, rewritten before anything renders. Both outputs build from this
one file, so the fix cannot land in the deck and miss the report.

Quoting the client's own copy is exempt. This passes, and is the stronger
observation anyway:

> The hero reads "Comprehensive dental solutions, seamlessly delivered", which
> names neither a treatment nor a clinic.

### Building

```bash
python3 scripts/build_data.py --project ~/Clients/meridian-dental
python3 scripts/build_site.py --project ~/Clients/meridian-dental \
    --out ~/Clients/meridian-dental/out/report.html
python3 scripts/build_deck.py --findings ~/Clients/meridian-dental/findings.json \
    --root ~/Clients/meridian-dental --out ~/Clients/meridian-dental/out/assessment.pptx
```

The report comes out with **four views** — Home, Audit, Summary, Action items.
There is no `ia.json` in the folder, so Personas and Sitemap are absent from
the nav and absent from the Home cards. Not greyed out. Absent.

Then the verification step, which is not optional: open the report in Chromium,
screenshot every view at desktop and mobile width, cold-load each route
directly, confirm the pins sit on the elements the findings describe. Render
the deck to PNGs and look at every slide.

---

## Act two — the redesign, eight days later

The pitch landed. New session, new machine, no memory of the first.

> *Do the sitemap and IA for meridian dental.*

### What it does not ask

You give it the folder. It reads `project.json` and says nothing further about
the client name, the URL, the markets, the languages, or the audience. Those
were settled in week one.

This is the whole point. Ask a second time and you get a slightly different
answer, and now the audit deck says "Meridian Dental Group" on page one while
the IA says "Meridian Dental" on page four, and a client who notices that
wonders what else is inconsistent.

### Redesign, not greenfield

It finds `findings.json` and switches modes. There is a diagnosis attached, so
this is not a blank-page exercise, and the IA has to answer the diagnosis.

A page whose absence caused a Critical finding is not optional. The audit found
that all six treatments share one URL and none of them can rank; the IA has six
treatment pages, and each one cites that finding.

### Personas

It asks what to ground them in. There is no research budget, so you say
whatever is on the site. It finds their case archive — 38 procedures — and
clusters them:

| Cluster | Count |
|---|---|
| Implants | 17 |
| Orthodontics | 13 |
| Cosmetic | 8 |

Three personas, weighted by what the practice actually sold, each carrying its
count as an evidence badge. The deliverable states in plain language that no
primary research was commissioned and that the weightings describe sales rather
than the market.

Blockers cite the audit by id:

```jsonc
{ "text": "Cannot tell which of the three clinics does implants",
  "fid": "f-51ef98a384" }
```

The id, and nothing else from the finding. Never the wording.

Any persona whose `needs_pages` is empty fails validation, because a persona
that changes nothing about the structure was describing the market rather than
shaping the site.

### Writing and validating

```bash
python3 scripts/validate_ia.py --ia ~/Clients/meridian-dental/ia.json
python3 scripts/check_prose.py --project ~/Clients/meridian-dental
```

The first catches a mistyped reference by path:

```
ia.json: pages[4].sections[1].fid = "f-51ef98a385" does not resolve against findings.json
```

One character wrong. Without the check it renders as a card claiming evidence
that does not exist, and nobody finds out until a client clicks it.

The second reads the In-plain-words boxes, the persona context and the section
descriptions — the parts a non-specialist actually reads end to end, and where
"a comprehensive gateway to our robust service ecosystem" arrives if nobody is
watching.

### Rebuilding

```bash
python3 scripts/build_data.py --project ~/Clients/meridian-dental
python3 scripts/build_site.py --project ~/Clients/meridian-dental \
    --out ~/Clients/meridian-dental/out/report.html
```

Same commands as week one. Same output file. **Personas and Sitemap have
appeared** between Summary and Action items, with Database and Glossary after
them because `ia.json` carries a content model and a term list. Every section
card that exists because of a finding expands to show it.

Nobody passed a flag. The folder's contents decided.

### If there had been no audit

Meridian came with one. A brand-new brand would not, and then the same
`ia.json` renders on its own:

```bash
python3 scripts/build_board.py --project ~/Clients/meridian-dental \
    --out ~/Clients/meridian-dental/out/sitemap.html
```

Home, Personas, Sitemap, Database, Glossary. No Audit, Summary or Action items,
because there are no findings — those tabs are absent rather than empty. Same
renderer, so it is the same document with fewer sections, not a different
deliverable that happens to cover similar ground.

---

## What the contract bought

**One folder, reused.** Week two works inside week one's folder rather than
beside it. Two folders is how a client ends up with two sitemaps and no way to
tell which one the proposal quoted.

**One writer per file.** `findings.json` is written by the audit and read by
everything else. `ia.json` is written by the sitemap skill and read by
everything else. No renderer edits its own input, so the deck and the report
cannot be built from quietly different data.

**References by id, never by copied text.** Reword a finding in month two and
the sitemap keeps showing the current wording, because it only ever stored the
id. Copy the text instead and the two documents disagree the moment one
changes, with nothing to signal it.

**Absence is a defined state.** No `ia.json` means four views, with the other
two removed rather than disabled. `#/personas` on a four-view build resolves to
Home, because people paste links.

**Checks fail loudly, by path.** Every validator names the JSON node. None of
them write a partial file — a half-valid report is worse than no report,
because it gets sent.

---

## When it goes wrong

| Symptom | Cause | Fix |
|---|---|---|
| `.id is missing - run scripts/finding_ids.py` | Findings written but never stamped | Run `finding_ids.py`, then rebuild |
| `fid = "f-…" does not resolve` | A finding was deleted, or the id was retyped rather than copied | Update the IA. Do not re-stamp the ids |
| `but this project has no findings.json` | A `fid` on a greenfield project | Remove it. Never invent one |
| `personas[n].needs_pages is empty` | A persona that changes nothing | Cut the persona, or find the page it requires |
| `chips is empty` | A section card with no discipline | Cut the card. If it earns no chip, it earns no place |
| `findings.json exists, so this project has an audit` | `build_board.py` in a redesign project | Render the combined report with `build_site.py` instead |
| Report has two active nav tabs | A routing bug — see the note on `classList.toggle` in `references/interactive.md` | Compare an explicit view key |
| An inline report too heavy to open | More than ~20 screens as data URLs | Rebuild with `--mode folder` |
| `differs across skills` from `package.sh` | A shared file edited in one skill only | Copy it across. They must be byte-identical |

---

## Command reference

```bash
P=~/Clients/meridian-dental

# audit
python3 scripts/finding_ids.py --findings $P/findings.json
python3 scripts/check_prose.py --project $P
python3 scripts/build_data.py  --project $P
python3 scripts/build_site.py  --project $P --out $P/out/report.html
python3 scripts/build_site.py  --project $P --out $P/out/report/ --mode folder
python3 scripts/build_deck.py  --findings $P/findings.json --root $P --out $P/out/deck.pptx

# information architecture
python3 scripts/validate_ia.py --ia $P/ia.json
python3 scripts/build_board.py  --project $P --out $P/out/sitemap.html   # greenfield only

# anywhere, no skill installed
python3 scripts/check_prose_standalone.py --project $P
python3 scripts/check_prose_standalone.py --file /some/other/findings.json
```
