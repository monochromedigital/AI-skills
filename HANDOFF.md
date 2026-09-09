# Handoff

Written 2026-09-09 for a fresh Claude Code session on a new machine and a new
Claude account, with no access to prior conversation history and nothing from
`~/.claude`. Everything below was verified against the repo on that date at
commit `f787b6e`. Where something could not be verified from the files, it says
**unverified** rather than guessing.

Read `CLAUDE.md` first — it carries the one hard rule. This file is the context
behind it.

---

## 1 · Project identity

**What it is.** A monorepo of custom [Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)
for Claude — usable in Cowork, Claude Code, and the Claude API. Each directory
under `skills/` is one self-contained skill: a `SKILL.md` with YAML frontmatter
(`name`, `description`) plus the `references/`, `assets/` and `scripts/` it
needs. Six skills ship today:

| Skill | Job |
|---|---|
| `website-assessment` | Live section-by-section UX/UI/SEO/accessibility audit → interactive HTML report, branded PPTX deck, and/or Figma slides |
| `sitemap-ia-board` | Visual sitemap + information architecture board → `ia.json` plus a standalone board or a combined report |
| `atomic-design` | Builds/audits/scaffolds front-end code atomically; ships a stdlib validator |
| `psychology-of-design` | 50 behavioural-psychology principles for design review |
| `linear-ticket-writing` | Turns vague tasks into agent-executable Linear tickets |
| `morning` | Renders a styled morning brief as an HTML artifact |

**Who it's for.** Monochrome Digital — Johnny Bou Malhab
(`johnny@monochrome.digital`, GitHub `johnny-bm`). The two client-facing skills
deliver under one of **four peer agency brands**: `all-in` (ALL IN),
`crackwits` (Crackwits), `daydream` (Daydream), `monochrome` (Monochrome).
None of the four is the house default — see §2a of the project contract.

**Where it's deployed.** Nowhere, in the runtime sense. There is no server, no
hosting, no database, no deploy config anywhere in the repo. Distribution is:

- GitHub: `https://github.com/monochromedigital/AI-skills` — **private**, org on
  the free plan (which is why required status checks are unavailable; see §7).
- `.skill` bundles built by `./package.sh` into `dist/` (gitignored), uploadable
  in Claude's skill settings. CI also uploads them as a `skill-bundles` artifact
  on every push and PR.
- Copy or symlink a skill folder into `~/.claude/skills/` (personal) or a
  project's `.claude/skills/` (per-project).

**Purpose.** These skills exist so that a client deliverable — an audit, a
sitemap, a deck — comes out the same way every time regardless of who runs it,
which machine it runs on, or how many sessions the project spans. The design
centre of gravity is not the prompts; it is the small set of invariants that
stop two documents about one client from quietly disagreeing with each other:
one project folder, one writer per file, content-derived identifiers that
survive rewording, one renderer shared byte-identically between skills, and a
branding resolution that fails loudly rather than guessing. Most of the code in
this repo is enforcement of those invariants; most of the prose is the record of
the specific failure that made each one necessary.

---

## 2 · Stack and setup

### Languages and runtimes

| | Version | Where it matters |
|---|---|---|
| Python | 3 (CI pins **3.11**; the old machine had 3.13.5) | Every script. `make check` and every repo-level tool are **stdlib-only** |
| Node | 22.23.2 on the old machine | Only the Figma plugin (plain ES5-ish JS, no build step) and the `morning` skill's Playwright screenshot snippet |
| Make | GNU make | Task runner — `Makefile` is the entry point |
| Bash | zsh/bash | `package.sh`, `.githooks/pre-push` |

**There is no package manager and no manifest.** No `package.json`, no
`pyproject.toml`, no `requirements.txt`, no lockfile — verified by absence. The
Figma plugin has no build step; `code.js` and `ui.html` are loaded directly by
Figma.

### Install and run

```bash
git clone https://github.com/monochromedigital/AI-skills.git
cd AI-skills
make hooks      # once per clone — git does not clone hooks
make check      # shared-file byte-identity, Python syntax, agencies resolve
```

Everything else:

```bash
make            # == make check
make sync       # copy shared files website-assessment -> sitemap-ia-board
make brands     # list installed agencies and whether each has a logo
make zip        # make check, then ./package.sh (all skills)
make clean      # rm dist/*.skill and __pycache__

./package.sh website-assessment      # one skill -> dist/website-assessment.skill
./package.sh                         # every skill

python3 scripts/build_standalone.py           # regenerate the portable checker
python3 scripts/build_standalone.py --check   # fail if the committed copy is stale
```

Skill-level commands, run from inside a skill directory against a client project
folder `$P` (full reference at the end of `docs/walkthrough.md`):

```bash
python3 scripts/capture.py     --url https://client.example --out $P
python3 scripts/finding_ids.py --findings $P/findings.json
python3 scripts/check_prose.py --project $P
python3 scripts/build_data.py  --project $P
python3 scripts/build_site.py  --project $P --out $P/out/report.html
python3 scripts/build_site.py  --project $P --out $P/out/report/ --mode folder
python3 scripts/build_deck.py  --findings $P/findings.json --root $P --out $P/out/deck.pptx
python3 scripts/validate_ia.py --ia $P/ia.json
python3 scripts/build_board.py --project $P --out $P/out/sitemap.html   # greenfield only
python3 scripts/brandkit.py                                            # what agencies exist
python3 scripts/check_prose_standalone.py --project $P                 # repo root; runs anywhere
```

### Third-party Python — only three scripts need any

Verified by import scan. Everything not listed is stdlib-only, including the
whole of `make check`, both renderers, both validators, and `check_atomic.py`.

| Script | Needs |
|---|---|
| `skills/website-assessment/scripts/build_deck.py` | `python-pptx`, `Pillow`, `lxml` |
| `skills/website-assessment/scripts/capture.py` | `playwright` + a Chromium binary |
| `skills/website-assessment/scripts/frame.py` | `Pillow` |

On the old machine, **none of these four packages were installed** for the
system `python3` — `make check` passed anyway because it never touches them.
These scripts normally run inside Claude's sandbox, where the packages and a
prebuilt Chromium at `/opt/pw-browsers/chromium` already exist. If you need them
locally, install into a venv; do not add a requirements file to the repo without
deciding whether the sandbox path or the local path is the supported one
(**open question — see §6**).

### Environment variables

Names and purpose only. Both are optional; neither is needed for `make check`.

| Variable | Purpose |
|---|---|
| `BRANDFETCH_CLIENT_ID` | Free client ID for the Brandfetch API, used by `skills/website-assessment/scripts/fetch_logo.py` to pull a **client's** logo into a project folder. Can also be passed as `--client-id`. Agency logos are never fetched — they are committed files. |
| `CHROMIUM_PATH` | Override for the Chromium executable `capture.py` launches. Defaults to `/opt/pw-browsers/chromium` (the sandbox path); if that file is absent, Playwright's own resolution is used. |

There is no `.env` file and no `.env.example` in the repo. `.env` is gitignored
as a precaution, not because one exists.

### External services and integrations

| Service | Used for | Auth needed |
|---|---|---|
| **GitHub** (`monochromedigital/AI-skills`, private) | Source of truth, PRs, Actions CI | `gh auth login` |
| **GitHub Actions** (`.github/workflows/skills.yml`) | Runs `make check` then `make zip` on every push and PR; uploads `dist/*.skill` | — |
| **Brandfetch API** | `fetch_logo.py`, client logos only. Note their terms ask for live CDN embedding; this script downloads and caches deliberately, because the report must open offline. `--link-only` stays inside the intended usage. | `BRANDFETCH_CLIENT_ID` |
| **Figma desktop app** | `skills/website-assessment/figma-plugin/` is a development plugin that writes native slides. The Figma **REST API / MCP connector cannot create frames** — only the Plugin API writes, so the deck cannot be generated remotely. Install per `references/figma-setup.md`. | Figma account (free tier is enough for dev plugins) |
| **Linear** | Only as the *subject* of `linear-ticket-writing`. The repo itself is not tracked in Linear (verified, §6). The Linear MCP server was connected on the old machine. | MCP re-auth |
| **npm registry** | Fallback font fetch (`npm pack @fontsource/fraunces`) in the `morning` skill | — |

Explicitly **not** used, despite being connected as MCP servers on the old
machine: Supabase, Vercel, Sentry, Framer. No config for any of them exists in
this repo.

---

## 3 · Architecture

### Folder map

```
.
├── CLAUDE.md                   # agent rules — the merge gate lives here
├── HANDOFF.md                  # this file
├── README.md                   # human-facing: what's here, how to install, how to add a skill
├── Makefile                    # task runner; `check` is the gate everything else leans on
├── package.sh                  # skill folder -> dist/<name>.skill (a zip Claude installs)
├── .githooks/pre-push          # runs `make check`; installed by `make hooks`, bypassable
├── .github/workflows/skills.yml# CI: make check, make zip, upload bundles
├── docs/walkthrough.md         # one invented client through both project skills, end to end
├── scripts/
│   ├── build_standalone.py     # generates the portable checker AND enforces shared-file identity
│   └── check_prose_standalone.py  # GENERATED — never hand-edit
└── skills/
    ├── website-assessment/     # the audit skill (largest; owns findings.json)
    │   ├── SKILL.md
    │   ├── figma-plugin/       # manifest.json + code.js + ui.html, imported into Figma desktop
    │   ├── references/         # project-contract, categories, voice, research, capture,
    │   │                       #   interactive, schema, figma-setup, ai-writing, site-types/
    │   ├── assets/             # brand.json (base), brands/<slug>/, fonts/ (Urbanist), ai-writing.json
    │   └── scripts/            # capture, frame, finding_ids, build_data, build_site,
    │                           #   build_deck, render_report, brandkit, check_prose, fetch_logo
    ├── sitemap-ia-board/       # the IA skill (owns ia.json); carries the shared files
    │   ├── references/         # project-contract (identical), ia-schema, methodology, personas
    │   └── scripts/            # build_board, validate_ia, render_report, brandkit, check_prose
    ├── atomic-design/          # standalone; references/ + scripts/check_atomic.py (900 lines, stdlib)
    ├── psychology-of-design/   # SKILL.md only
    ├── linear-ticket-writing/  # SKILL.md only
    └── morning/                # SKILL.md + assets/fonts/ (Fraunces woff2)
```

`references/site-types/` holds seven lenses — `ecommerce`, `saas`,
`service-business`, `corporate`, `content-publisher`, `marketplace`,
`nonprofit-education` — one of which types every audit.

### Key entry points

| To do this | Start here |
|---|---|
| Understand the invariants | `skills/website-assessment/references/project-contract.md` — **the governing document**. Where it and a SKILL.md disagree, it wins. |
| See the whole thing work | `docs/walkthrough.md` |
| Understand the checks | `Makefile` → `scripts/build_standalone.py` |
| Change how any report looks | `skills/*/scripts/render_report.py` — **1166 lines, byte-identical in both skills** |
| Change branding resolution | `skills/*/scripts/brandkit.py` — byte-identical in both skills |
| Add an agency | `skills/*/assets/brands/<slug>/brand.json` in **both** skills (`make sync`) |

### Data flow

Everything happens inside **one folder per client project** (contract §1),
never a temp directory:

```
capture.py ──> page-data.json + screens/
                     │
   (you write)       ▼
              findings.json ──> finding_ids.py stamps content-derived ids
                     │              (frozen once present)
                     ├──────────> check_prose.py   (AI-writing vocabulary gate)
                     │
                     ├──> build_data.py ──> report-data.json ──> build_site.py ──> out/report.html
                     │                                              │ (uses render_report.py)
                     │                                              └─ or out/report/ (--mode folder)
                     │
                     └──> build_deck.py ──> out/assessment.pptx     (frame.py device-frames first)

ia.json (sitemap-ia-board) ──> validate_ia.py
                     │
                     ├──> build_board.py ──> out/sitemap.html    (greenfield only — refuses if
                     │                                             findings.json exists)
                     └──> read by build_site.py, adding Personas + Sitemap views to the same report
```

One writer per file. A renderer never rewrites its own input.

### Non-obvious design decisions, and why

**One renderer, carried byte-identically.** `render_report.py` is duplicated in
both skills rather than shared through an import, because a skill has to be a
self-contained folder that can be zipped and installed alone. Byte-identity is
then machine-enforced. An audit report and a greenfield IA board are the same
document with different sections present — the moment they were two codebases
they started looking like two agencies.

**Findings ids are content-derived, generated once, then frozen.**
`id = "f-" + sha256(nfkc_casefold(page ⋮ section ⋮ observation))[:10]`. Positional
ids (`s3f2`) were the failure this replaces: reorder the slides and every
cross-reference silently points at a different finding — it does not error, it
lies. A content-derived id that no longer exists fails loudly instead. The
derivation is how an id is *born*, not a checksum re-verified on each build, so
rewording a finding is safe and deleting one that `ia.json` cites correctly
fails the build.

**Cross-references are by id and only by id.** Never copy the audit's text into
`ia.json`. Copied text is a snapshot; the moment anyone rewords the finding the
two documents disagree and nothing errors.

**There is no default agency, and a missing one fails the build.** This is the
one degradation rule the contract does *not* grant (§8 grants it to everything
else). Every other missing file changes what the document contains, visibly.
Wrong branding changes nothing visible — the document looks entirely finished
and nothing downstream catches it.

**`assets/brand.json` is a neutral grey base that belongs to no agency.** Agency
files are deep-merged **overlays** carrying only what differs. So an incomplete
agency file renders as visibly unbranded rather than as some other agency's
work, and the build names the keys that fell through. Category and severity
colours deliberately stay in the base: they are functional encoding a reader
learns across reports.

**A value that differs per skill must never live in a shared file.** This is the
half of the rule that is easy to miss, and the one that actually broke.
`footer_right` sat in all four agency overlays in both skills — eight copies of
one string in files required to match. When one was renamed, the byte-identity
check failed while pointing at the *wrong fix*: syncing the copies would have
labelled a sitemap as an audit. The label belongs to the skill (`DELIVERABLE` in
`build_data.py`), and `FORBIDDEN_BRAND_KEYS` in `build_standalone.py` now makes
putting it back fail immediately.

**`check_prose_standalone.py` is generated, not written.** The in-skill checker
reads word lists from `assets/ai-writing.json` — right inside a skill, useless
outside one, because you cannot drag a two-file checker into a chat. The
standalone bakes the lists in. Editing it directly recreates the exact drift the
JSON was meant to prevent.

**The shared-file invariant lives in exactly one list.** `build_standalone.py`
already had to know it to generate the checker, so `make check` calls that
rather than keeping a second list in a shell script. It scans every skill under
`skills/`, so a third skill picking up a shared file is covered with no edit.

**The Python syntax check globs `skills/*/scripts/*.py`.** It used to name the
two skills explicitly, which read as harmless while those were the only two with
code — until `atomic-design` arrived with a 900-line validator that `make zip`
packaged and nothing ever parsed. A check that silently covers a subset is worse
than one that covers nothing, because the green tick is read as coverage.

---

## 4 · Current state

| | |
|---|---|
| Branch | `claude/project-handoff-doc-08cbe2` |
| Commit | `f787b6e` — *Scan `${...}` as code in mask_source, tracking brace depth (#8)* |
| Relation to `main` | **Identical.** `main`, this branch, and `claude/install-frontend-design-skill-e8865a` all point at `f787b6e` |
| Working tree | **Clean.** No modified, staged, or untracked files |
| Stashes | **None** (`git stash list` empty) |
| `make check` | **Passes**, exit 0 |
| CI on `main` | **Green** — last run 2026-08-20, 14s |
| Open PRs | **None.** PRs #1–#8 all merged |
| Open issues | **None** |

### What's done

The repo is at a natural stopping point. All eight PRs are merged and the last
five were specifically about closing the gaps that let a bad change through:

- `#3` moved the deliverable label out of the shared brand files
- `#4` wrote the shared-file rule into the contract (§2b) and enforced its other half
- `#5` made the syntax check cover every skill rather than two named ones
- `#6` added the pre-push hook
- `#7` added `CLAUDE.md` and the never-merge-over-red rule
- `#8` fixed a real bug in `check_atomic.py`'s `mask_source()` — template-literal
  interpolations were not scanned as code, so from the first nested backtick every
  span was inverted. Fixing it took one real repo's magic-number count from 32 to 34.

### What's in progress

**Nothing.** No uncommitted work, no half-finished branch, no WIP commit.

### What's broken

Nothing is broken in the "CI is red" sense. Two things are **deliberately
incomplete** and marked as such in the files themselves:

- **Three of four agency palettes are placeholders.** `crackwits` is complete —
  it holds the values these documents have always used, moved out of the base so
  Crackwits stops being structurally privileged. `monochrome` and `daydream`
  carry a `TODO` in their `_comment` saying the palette was chosen only so a
  report renders legibly during setup. `all-in` is seeded from the
  indigo/emerald tokens used on the CompoundIn work, which may be that
  project's design system rather than the agency's brand. Source:
  `skills/*/assets/brands/README.md`, "Before the first real run".
- **No agency has a logo.** `python3 scripts/brandkit.py` prints `logo=-` for
  all four. This is on purpose — a placeholder wordmark reaching a client is
  worse than none, and every surface degrades to the agency name as text. It is
  still work that has to happen before a client run under a brand that has a logo.

### Uncommitted / local-only state

None in the repo. Two things live outside it and do not travel — see §9:
`.claude/settings.local.json` (ignored via the machine's **global** git ignore)
and `.git/info/exclude` (holds `.claude/worktrees/`).

### Branches

| Branch | State |
|---|---|
| `main` / `origin/main` | `f787b6e` — current |
| `claude/project-handoff-doc-08cbe2` | this one, `f787b6e` |
| `claude/install-frontend-design-skill-e8865a` | `f787b6e`, a worktree branch with no commits of its own |
| `multi-agency-branding` / `origin/multi-agency-branding` | **Stale — safe to delete.** `8caff66`, merged as PR #1 but landed on `main` as the differently-hashed `76a15ff`, so `git branch --contains` does not show it as merged. It is 2108 lines *behind* `main`. Its content is fully in `main`; nothing is lost by deleting it. |

Git worktrees on the old machine (these do not travel):
`.claude/worktrees/distracted-mendeleev-c9d747` and
`.claude/worktrees/project-handoff-doc-08cbe2`.

---

## 5 · Decisions log

Settled. Do not relitigate without new evidence.

| Decision | Rejected alternative | Why |
|---|---|---|
| Skills are self-contained folders; shared files are **duplicated and byte-checked** | A shared library imported by both skills | A skill has to zip and install alone. Duplication plus machine-enforced identity beats an import that breaks on install. |
| `website-assessment` is the source of truth for shared files; `make sync` copies one way | Bidirectional sync, or a symlink | One direction is auditable. Symlinks do not survive zipping. |
| The shared-file list lives **only** in `build_standalone.py` | A second list in the Makefile or `package.sh` | A rule kept in two files is the same drift the contract exists to prevent. |
| Finding ids are content-derived and frozen | Positional ids (`s3f2`); UUIDs | Positional ids silently lie after a reorder. Content-derived ids fail loudly and survive rewording. UUIDs carry no meaning and cannot be regenerated. |
| **No default agency**; an absent or unknown slug fails the build | Fall back to Crackwits (the original behaviour) | A typo would ship a Monochrome deck in Crackwits colours with nothing in the output saying so. |
| Base palette is neutral grey and belongs to no agency | Keep Crackwits values in the base | With Crackwits as the base, an incomplete agency file renders as a finished-looking *Crackwits* document. Grey reads as unfinished, which is the point. |
| Category and severity colours are shared, overridable only explicitly | Per-agency category colours | Functional encoding — a client who reads three reports learns orange means UX. |
| Agency files are overlays, deep-merged | Copy the base and edit per agency | Otherwise the next category-colour change has to be made four times, and will be made in three. |
| The deliverable's name is a per-skill `DELIVERABLE` constant | `footer_right` in the brand files | It was in eight files, drifted, and the drift's obvious fix would have labelled a sitemap as an audit. |
| Client logos are **downloaded and cached**, not live-linked | Brandfetch's intended live CDN embed | The report is a single file that must open offline, in an email client, and after the CDN link rots. A deliberate departure from their terms — `--link-only` is provided for whoever disagrees. |
| Agency logos are committed files, never fetched | Fetch all logos from Brandfetch | Four fixed logos that are yours: a network call would trade certainty for nothing. |
| The Figma deck is built by a **plugin the user runs**, not remotely | The Figma REST API / MCP connector | Those are read-only. Only the Plugin API can create frames. Not a preference — a platform constraint. |
| The pre-push hook is bypassable (`--no-verify`) | An unskippable hook | A hook you cannot skip is a hook people uninstall the first time it is wrong. |
| The merge gate is an instruction in `CLAUDE.md` | A required status check | Required checks need a paid plan on a private repo; the org is on free. |
| Anthropic-bundled skills (`docx`, `pdf`, `pptx`, `xlsx`, `skill-creator`) are **not** vendored | Vendor them for completeness | They ship with the product and carry their own license. |
| Logos are embedded as data URIs | `<img src="https://…">` | These documents must open offline and years later. |
| Above ~20 screens, reports build as a folder | Always inline | Data URLs are ~33% larger than the PNGs, and the browser parses all of it before painting. |

---

## 6 · Open work

**No Linear tickets track this repository.** Verified 2026-09-09 with two
searches of the Monochrome Digital workspace (`skill`, and
`website assessment sitemap IA board agency branding`) — every result is client
work (MC-31, MC-42, MC-54/55/58/61, MC-70/71/73, MC-87/88, MC-94, MC-121,
MC-133/134/137, MC-142/144/145, MC-170/173, MC-246 …) and none concerns
`AI-skills`. If this work should be tracked, the team is **Monochrome Digital**
(`MC-` prefix) and `skills/linear-ticket-writing/SKILL.md` is the house format.

Priority order:

### P1 — Replace the three placeholder agency palettes

`monochrome`, `daydream` and `all-in` carry palettes chosen only so a report
renders legibly. Each says so in its own `_comment`. **Blocks any client
deliverable under those three brands.** Not a code change: edit
`skills/website-assessment/assets/brands/<slug>/brand.json`, keeping it an
overlay (only keys that differ from `assets/brand.json`), then `make sync` to
propagate to `sitemap-ia-board`, then `make check`. `python3 scripts/brandkit.py`
and the build's own stderr both name the keys still falling through to the
neutral base. Context: `skills/*/assets/brands/README.md`, final section.

### P2 — Add `logo-dark.svg` for each agency that has one

All four print `logo=-`. Drop the file into
`assets/brands/<slug>/`, **in both skills**. Requirements, from
`assets/brands/README.md`: SVG (PNG accepted but soft on retina); legible on a
dark background (the report header and every deck slide are dark); roughly 4:1
or wider (it renders 20px tall); under ~20 KB (it is inlined into every report).
Add `logo.svg` too if a light-surface variant exists. Verify with
`python3 scripts/brandkit.py`. A missing logo is a *degradation*, not a
failure — so this is real work, not a blocker.

### P3 — The Figma plugin still hardcodes Crackwits

`skills/website-assessment/figma-plugin/manifest.json` is named
`"Crackwits Website Assessment"` with id `crackwits-website-assessment`, and
`figma-plugin/code.js:247` writes `'Crackwits © ' + year + '. All Rights
Reserved'` onto every slide. That directly contradicts contract §2a — a deck
built through the plugin for a Monochrome project carries a Crackwits copyright
line. The plugin already accepts a merged `brand.json` as a drop-in override, so
the fix is to read `agency.footer_left` from the dropped brand file and fall
back to text rather than to a hardcoded name. The manifest name is cosmetic but
misleading; renaming it changes the id, which means every installed copy must be
re-imported (`references/figma-setup.md` describes the install). Decide those two
separately.

### P4 — Delete the stale `multi-agency-branding` branch

Merged as PR #1, landed on `main` as `76a15ff`, now 2108 lines behind. It reads
as live work and is not.

```bash
git push origin --delete multi-agency-branding && git branch -D multi-agency-branding
```

### P5 — Decide how the three non-stdlib scripts declare their dependencies

`build_deck.py`, `capture.py` and `frame.py` need `python-pptx`, `Pillow`,
`lxml` and `playwright`. Nothing in the repo says so — it is discoverable only by
reading imports, and `make check` passes without them. The reason it has not
mattered is that these run in Claude's sandbox where the packages already exist.
Options: a `requirements.txt` that CI never installs (documentation only), a
docstring line per script, or a note in each `SKILL.md`. **Open question, not a
decided direction** — pick one deliberately rather than adding a manifest that
implies a local-install workflow nobody uses.

### P6 — `check_prose.py`'s word lists have never been reviewed against real output

The AI-writing checker is the floor, not the standard (`voice.md` is the
standard). Worth a pass over `assets/ai-writing.json` after the next few real
client runs, adding terms that actually surfaced. Low priority, no deadline.

---

## 7 · Gotchas

**Never merge over a red check.** This is in `CLAUDE.md` and it is the only gate.
`gh pr merge` does not refuse a failing check, and a required status check needs
a paid plan on a private repo. The incident: PR #2's check concluded red at
`08:53:26Z` on 2026-08-11 and the PR merged at `08:54:14Z` — 48 seconds later.
`main` had already been red since `2026-08-10T10:38:16Z` (commit `e958fc2`,
pushed straight to main) and stayed red until `825da6c` fixed it — about 22½
hours. Before any merge:

```bash
gh pr view <N> --json statusCheckRollup --jq '[.statusCheckRollup[]|{name,conclusion}]'
```

Every entry must read `SUCCESS`. An **empty** `conclusion` means the run is
still going — wait, do not merge on an incomplete rollup. If a check is red and
you believe the merge is still correct: **say so and ask.**

**When a shared-file check fails, do not just copy one skill's version over the
other.** That is the reflex the failure appears to demand and it is how a
sitemap gets labelled as an audit. Check that both skills genuinely want the
same bytes first. Reasoning: contract §2b.

**The pre-push hook reads the working tree, not the commits being pushed.** Push
with a dirty tree and it checks what is on disk rather than what the other end
receives. CI is the authority. It also has to be installed per clone
(`make hooks`); git does not clone hooks. `core.hooksPath` lives in the shared
config, so several worktrees only need it once.

**Never hand-edit `scripts/check_prose_standalone.py`.** It is generated.
Change `skills/*/assets/ai-writing.json`, run `python3 scripts/build_standalone.py`,
commit both.

**Never hand-edit a rendered report or board.** They are generated from
`findings.json` / `ia.json` and are overwritten on the next build. If something
cannot be expressed in the JSON, that is worth saying out loud — it usually
means the schema is missing a field the work needs.

**Never create a second project folder for a client.** `client-2` beside
`client` means two `findings.json` files and no way to tell which one the
proposal quoted. Reuse the folder (contract §1). If the previous run's contents
look wrong, say so and let the user decide — do not route around it.

**Deleting a finding that `ia.json` cites breaks the build, and that is
correct.** Rewording is always safe (ids are frozen). The fix for a dangling
`fid` is to update the IA, never to re-stamp the ids.

**Sandbox network restrictions (Claude's environment, not this machine):**
- `fonts.googleapis.com` is reachable but `fonts.gstatic.com` is **blocked** by
  the egress proxy. The failure appears only *after* the CSS step seems to have
  succeeded — `urllib` dies with `Tunnel connection failed: 403`, curl exits 56.
  Fonts ship in each skill's `assets/fonts/`; use those.
- **Do not run `playwright install`.** Browser downloads are blocked; it wastes
  minutes and then fails. `npm install playwright` is fine — only the browser
  download is blocked. Launch with an explicit
  `executablePath: '/opt/pw-browsers/chromium'`; a bare `chromium.launch()`
  looks for an uninstalled revision and helpfully suggests the command you must
  not run.

**Urbanist must be installed for the PPTX to render as designed.** The deck names
the font; the viewer needs it. TTFs are in `assets/fonts/`. The Figma plugin
falls back to Inter and says so in the plugin window.

**Reports above ~20 screens must build as a folder.** `build_site.py` warns on
stderr; rebuild with `--mode folder` rather than sending it.

**Markers are fractions of the screenshot, not the framed PNG and not the
slide.** `screen_rect` from `frame.py` does the mapping. Omit it and every
marker shifts by the bezel width.

**`build_board.py` refuses to run when `findings.json` exists.** That is not a
bug — a standalone board plus an audit means two documents covering the same
structure, and the client reads whichever they opened last. Use `build_site.py`
for the combined report.

**Brandfetch returns a scraped favicon as readily as a real wordmark** for small
brands. Always look at what landed before it reaches a client.

**`git stash` is shared across worktrees.** If you work in a worktree, never use
bare `git stash` / `git stash pop` — prefer a temporary WIP commit.

---

## 8 · Conventions

### Commits

Observed across all 12 commits on `main`. No conventional-commits prefix, no
scope, no emoji, no ticket id.

- **Subject: imperative mood, sentence case, no trailing period.** "Scan
  `${...}` as code in mask_source, tracking brace depth". "Give the audit
  deliverable one name, defined once". "Parse every skill's Python, not just the
  two named ones". Squash-merging appends ` (#N)`.
- **Body: long, and it explains the failure, not the change.** These read as
  incident notes — what broke, how it surfaced, why the obvious fix was wrong,
  what was checked. The `#8` body is ~40 lines for a ~20-line diff. This is
  house style, not an accident: the same reasoning is what makes the code
  comments and `references/` prose worth reading.
- **Trailers**, both used:
  ```
  Co-authored-by: johnny-bm <johnny-bm@users.noreply.github.com>
  Co-authored-by: Claude Opus 5 <noreply@anthropic.com>
  ```

### Branching and PRs

- `main` is the default branch. Feature branches, one per change, squash-merged.
- Branch names seen: `fix/mask-source-interpolations`, `fix-footer-label-drift`,
  `add-atomic-design-skill`, `multi-agency-branding`, and Claude-generated
  `claude/<slug>` names. No enforced scheme.
- One direct-to-main push exists (`e958fc2`) and it is the one that turned CI red
  for a day. Do not repeat it.
- **Check the rollup before every merge** (§7).

### Code style

- **Python 3, stdlib-first.** Reach for a third-party package only when there is
  no alternative — currently only PPTX generation, image framing, and browser
  automation qualify.
- **Module docstrings carry the reasoning.** Every non-trivial script opens with
  a docstring explaining what problem it solves and what was rejected —
  `brandkit.py` and `build_standalone.py` are the models.
- **`SKILL.md` under ~500 lines.** Detail goes in `references/` and is loaded on
  demand. Runnable code in `scripts/`, templates and fonts in `assets/`.
- **Frontmatter `description` is written for triggering, not summarising.** It is
  the only thing Claude sees when deciding whether to load the skill. Say what
  it does *and* when to use it, including the phrases a user would actually type.
- **One skill, one job.** If a description needs "and also", it is two skills.
- **Anything brand-specific lives in `assets/brand.json`** so a skill can be
  re-pointed without editing `SKILL.md`.
- **Prose is British-inflected and plain** ("colour", "behaviour", "analyse").
  The AI-writing checker exists because a deck full of "robust", "comprehensive",
  "seamless" and "leverage" undoes the one thing the audit is selling — that
  somebody actually looked.

### Front-end code (when these skills build UI)

Two laws from `skills/atomic-design/SKILL.md`, and they are the operator's own
standing preference:

1. **Nothing is hardcoded** — not a colour, spacing value, string, URL, or
   threshold. Every value has one home.
2. **Nothing is built top-down and nothing repeats** — button before form, form
   before page. The *second* time markup appears it becomes a component. Not the
   third. The second.

Detect the project's stack; never assume it. `scripts/check_atomic.py` is
read-only and never edits code.

### How the operator works with Claude here

Inferred from the repo's own artifacts — the commit bodies, the "Things that go
wrong" sections, the contract's tone. Treat as strong signal, not as
instructions the user has restated on the new machine:

- **Orient before coding.** Read `project-contract.md` and the relevant
  `SKILL.md` first. The contract wins over any skill file that disagrees.
- **Ask when a check is red and you think the merge is right.** Do not merge and
  explain afterwards. This is written explicitly in `CLAUDE.md`.
- **Explain the failure, not the diff.** A change that fixes something is
  expected to come with the account of what broke and why the obvious fix was
  wrong. Terse commits are the anomaly here.
- **Prefer failing loudly over degrading silently** — except where degradation is
  explicitly designed (a missing logo, a missing `ia.json`), and those cases are
  enumerated in contract §8.
- **A rule kept in two files is drift.** Point at the canonical location rather
  than restating it. `CLAUDE.md` does this deliberately for §2b.

---

## 9 · Local-only things to recreate on the new machine

Nothing here is in the repo. All of it was on the old machine.

### Required before the first push

```bash
gh auth login                                    # private repo, and `gh pr view` is the merge gate
git config user.name  "Johnny Bou Malhab"        # commits used both this and `johnny-bm`
git config user.email "johnny@monochrome.digital"
make hooks                                       # per clone — git does not clone hooks
```

### Git ignore rules that live outside the repo

Two rules kept the working tree clean on the old machine, and **neither is in
`.gitignore`**:

1. `~/.config/git/ignore` line 1 contained `**/.claude/settings.local.json`.
   Without it, that file shows as untracked in every repo.
2. `.git/info/exclude` contained `.claude/worktrees/`. Claude Code generally adds
   this itself when it first creates a worktree; if `git status` shows a
   `.claude/worktrees/` directory, add the line.

### `.claude/settings.local.json` (ignored, so it does not travel)

Its entire content was two WebFetch permissions, used while writing the
`atomic-design` skill:

```json
{
  "permissions": {
    "allow": [
      "WebFetch(domain:atomicdesign.bradfrost.com)",
      "WebFetch(domain:medium.com)"
    ]
  }
}
```

Recreate only if you are editing `atomic-design` and need its source material.

### Tools

`python3` (3.11+; CI pins 3.11), `make`, `git`, `gh` (2.96 on the old machine),
`zip`. `node` 22 only if you touch the Figma plugin or the `morning` skill's
screenshot step. For the three non-stdlib scripts, a venv with `python-pptx`,
`Pillow`, `lxml`, `playwright` — see §2 and open item P5.

### Fonts

**Urbanist** (Google Fonts) must be installed system-wide to view the PPTX and
to run the Figma plugin without its Inter fallback. The TTFs are committed at
`skills/*/assets/fonts/` — install from there.

### Skills installed on the old machine (`~/.claude/skills/`)

Plain directory copies, not symlinks — so edits in the repo did **not**
propagate, and the installed copies could drift:

- `atomic-design` (copied 2026-08-11)
- `linear-ticket-writing-mono` — a **renamed** copy of this repo's
  `linear-ticket-writing`, presumably to avoid colliding with the
  Anthropic-provided skill of the same name

`website-assessment`, `sitemap-ia-board`, `psychology-of-design` and `morning`
appeared in the old session under an `anthropic-skills:` namespace rather than
as folders in `~/.claude/skills/`. **Unverified** where that namespace resolves
from — check it on the new machine before assuming the repo versions are what is
running. Re-install from this repo either way:

```bash
cp -r skills/<name> ~/.claude/skills/          # or symlink, which avoids the drift above
```

### MCP servers to re-authorise

Connected in the old session. Only the first two are relevant to this repo:

- **Linear** (`linear-monochrome`) — workspace *Monochrome Digital*, `MC-` prefix.
  Used by `linear-ticket-writing`.
- **Figma** — note it is **read-only** and cannot create frames; the deck is
  built by the local plugin, not through MCP. Required OAuth on the old machine.
- Present but not used by this repo: Supabase, Vercel (OAuth required),
  Shadcn UI, Pencil, claude-mem, Claude in Chrome, scheduled-tasks.

Authorise via claude.ai connector settings, or `claude mcp` / `/mcp` in an
interactive terminal session.

### Claude Code memory

The old account's memory held one relevant note — *"nothing hardcoded; build
smallest-component-first and never repeat markup"*. That is already the two laws
of `skills/atomic-design/SKILL.md`, so nothing is lost by not migrating it.
Nothing else in memory was specific to this repo.

---

## 10 · First-session checklist

Run these in order before touching any feature code. Each line has an expected
result; if one does not match, stop and read the relevant section above.

```bash
# 1 — where are we
git status                    # expect: clean
git log --oneline -5          # expect: f787b6e at top (or later)
git branch -a                 # note: multi-agency-branding is stale, see §4
git stash list                # expect: empty
```

```bash
# 2 — install the guardrail (per clone; git does not clone hooks)
make hooks
# expect: "core.hooksPath -> .githooks (pre-push)"
```

```bash
# 3 — does the environment work
make check
```
Expect exactly this, exit 0:
```
== shared files ==
scripts/check_prose_standalone.py is current
  All shared files identical.
== python syntax ==
  all parse
== agencies installed ==
installed: all-in, crackwits, daydream, monochrome
```
If **shared files** fails: read contract §2b **before** copying anything (§7).
If **agencies** fails: the brand assets did not clone cleanly.

```bash
# 4 — confirm the branding state you were handed
cd skills/website-assessment && python3 scripts/brandkit.py && cd ../..
# expect all four agencies listed, every one showing logo=-   (open items P1, P2)
```

```bash
# 5 — confirm CI is green and nothing is open
gh auth status
gh pr list --state open        # expect: none
gh run list --limit 3          # expect: success on main
```

```bash
# 6 — confirm the packaging path works end to end
make zip                       # runs `make check` first
ls dist/                       # expect six .skill bundles
make clean
```

```bash
# 7 — orient
cat CLAUDE.md                                                          # the merge gate
cat skills/website-assessment/references/project-contract.md           # the governing document
cat docs/walkthrough.md                                                # both skills on one client
```

Only after all seven pass, start on §6 — P1 (agency palettes) is the item that
blocks real client work.
