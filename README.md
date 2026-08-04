# Skills

Custom [Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) authored for use with Claude (Cowork), Claude Code, and the Claude API.

Each folder under `skills/` is a self-contained skill: a `SKILL.md` with YAML frontmatter (`name`, `description`) plus any supporting assets, reference docs, or scripts it needs.

## What's in here

| Skill | What it does |
| --- | --- |
| [`website-assessment`](skills/website-assessment) | Section-by-section UX/UI/SEO/accessibility audit of a live site — typed to the kind of site it is (ecommerce, SaaS, service, corporate, publisher, marketplace, nonprofit/education) and backed by researched benchmarks — delivered as an interactive web report, a branded PPTX deck, and/or Figma slides — all with numbered markers pinned to the exact elements. |
| [`sitemap-ia-board`](skills/sitemap-ia-board) | Full visual sitemap + information architecture board — evidence-grounded personas, page columns, section cards tagged for UX/CRO/SEO, conversion-flow logic, and a CMS spec for developers. Emits a structured `ia.json` plus either a standalone HTML board or a combined report rendered alongside an existing audit. |
| [`psychology-of-design`](skills/psychology-of-design) | Catalog of 50 behavioral-psychology and cognitive-bias principles for designing, reviewing, and improving interfaces and conversion flows. |
| [`linear-ticket-writing`](skills/linear-ticket-writing) | Turns vague tasks into Linear tickets that an agent can execute end-to-end — full context, explicit constraints, testable acceptance criteria, MCP-ready formatting. |
| [`morning`](skills/morning) | Renders a styled morning brief as an HTML artifact, or sets it up as a recurring weekday task. |

## Installing a skill

**Claude Code / Cowork (personal)** — clone and symlink or copy into your skills directory:

```bash
git clone https://github.com/monochromedigital/AI-skills.git
cp -r AI-skills/skills/website-assessment ~/.claude/skills/
```

**Per-project** — put it under `.claude/skills/` in the repo you're working in, and it becomes available to anyone working on that project.

**Claude apps (packaged)** — zip a skill folder and rename it to `.skill`:

```bash
./package.sh website-assessment
```

This produces `dist/website-assessment.skill`, which can be uploaded in Claude's skill settings.

## How the project skills fit together

`website-assessment` and `sitemap-ia-board` work on the same client project,
in one folder, through the contract in `references/project-contract.md` (carried
identically by both). [`docs/walkthrough.md`](docs/walkthrough.md) follows one
client through both skills end to end — what each asks, what lands in the
folder, what the checks catch, and why the report grows from four views to six
without anyone passing a flag.

## Repo-level scripts

`scripts/check_prose_standalone.py` is a portable copy of the AI-writing checker
that `website-assessment` and `sitemap-ia-board` both carry. The in-skill
version reads its word lists from `assets/ai-writing.json` next to it; this one
has them embedded, so it runs anywhere:

```bash
python3 scripts/check_prose_standalone.py --project <project-folder>
python3 scripts/check_prose_standalone.py --file <anywhere>/findings.json
```

Use it against a session that predates the skill update, or any `findings.json`
or `ia.json` sitting on disk. Drag it into a chat and it works there too.

**It is generated — do not edit it.** Change the word lists in
`skills/*/assets/ai-writing.json` and rebuild:

```bash
python3 scripts/build_standalone.py           # regenerate
python3 scripts/build_standalone.py --check   # fail if the committed copy is stale
```

`package.sh` runs the regeneration first, so building the bundles cannot ship a
stale checker. That step also verifies the files the project contract requires
to be byte-identical across skills actually are — `ai-writing.json`,
`check_prose.py`, `ai-writing.md` and `project-contract.md`. A drifted copy
fails the build here rather than in a client's report.

## Adding a skill

1. Create `skills/<skill-name>/SKILL.md`.
2. Frontmatter needs `name` (lowercase, hyphens) and `description`. The description is the only thing Claude sees when deciding whether to load the skill — write it as trigger conditions, not a summary. Say what the skill does *and* when to use it, including the phrases a user would actually type.
3. Keep `SKILL.md` under ~500 lines. Push detail into `references/` and load it on demand.
4. Put runnable code in `scripts/`, templates and fonts in `assets/`.

```
skills/<skill-name>/
├── SKILL.md          # required — frontmatter + instructions
├── references/       # detail loaded only when needed
├── assets/           # templates, fonts, brand files
└── scripts/          # executable helpers
```

## Conventions

- One skill, one job. If a description needs "and also", it's two skills.
- Descriptions are written for triggering. Include the words a user says, not just the words a designer would.
- Anything brand-specific lives in `assets/brand.json` so a skill can be re-pointed at a different client without editing `SKILL.md`.
- Skills that work on the same client project share `references/project-contract.md` — one project folder, one writer per file, content-derived ids for cross-document references, and defined behaviour when a file is absent. `website-assessment` and `sitemap-ia-board` both carry a copy; keep them identical.
- Skills bundled by Anthropic (`docx`, `pdf`, `pptx`, `xlsx`, `skill-creator`) are deliberately **not** vendored here — they ship with the product and carry their own license.
