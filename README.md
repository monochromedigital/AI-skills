# Skills

Custom [Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) authored for use with Claude (Cowork), Claude Code, and the Claude API.

Each folder under `skills/` is a self-contained skill: a `SKILL.md` with YAML frontmatter (`name`, `description`) plus any supporting assets, reference docs, or scripts it needs.

## What's in here

| Skill | What it does |
| --- | --- |
| [`website-assessment`](skills/website-assessment) | Section-by-section UX/UI/SEO/accessibility audit of a live site — typed to the kind of site it is (ecommerce, SaaS, service, corporate, publisher, marketplace, nonprofit/education) and backed by researched benchmarks — delivered as a branded PPTX deck and/or Figma slides with numbered markers pinned to the exact elements. |
| [`sitemap-ia-board`](skills/sitemap-ia-board) | Full visual sitemap + information architecture board as a single HTML artifact — page columns, section cards tagged for UX/CRO/SEO, conversion-flow logic, and a CMS spec for developers. |
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
- Skills bundled by Anthropic (`docx`, `pdf`, `pptx`, `xlsx`, `skill-creator`) are deliberately **not** vendored here — they ship with the product and carry their own license.
