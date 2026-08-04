# Voice: how findings are written

## The shape of a finding

Every finding follows the same three-beat move, in this order:

1. **Observation** — what is on the page, stated neutrally
2. **Consequence** — what that does to the user
3. **Fix** — the concrete change (in the `fix` field, not buried in prose)

The observation and consequence live together in one flowing sentence or two.
Do not label them. From the reference deck:

> The green header feels visually heavy and creates a low-contrast navigation
> area, making the menu harder to read and scan.

Observation ("visually heavy... low-contrast"), consequence ("harder to read
and scan"). One sentence. No preamble, no "we noticed that".

> The Home button is redundant because the logo already acts as the expected
> route back to the homepage. Removing it simplifies the navigation and gives
> more space to higher-value sections.

Observation, reason, consequence, and the fix folded into the second sentence.

## Rules

**Describe the page, not the people who built it.** "The header feels visually
heavy" — not "the designer chose a heavy header". Never "you failed to", never
"whoever built this".

**Lead with the thing, not with the category.** Start with what is on screen.
The tag already says which discipline it belongs to; repeating it in the
sentence wastes the first four words.

**One finding per card.** If a sentence contains "and also", it is two findings.

**Be specific enough to act on.** "Improve the navigation" is not a finding.
"The Home button is redundant because the logo already routes home" is.

**Quantify where a number exists.** Contrast ratios, field counts, page weight,
click depth, load time. A number ends the argument. `Red on dark green fails
contrast minimum` becomes undeniable when it reads `2.1:1 against a 4.5:1
minimum`.

**Note scope when a finding repeats.** If it applies site-wide, say so in the
`scope` field — it renders in bold at the bottom of the card:
`Applicable on all the website and also on footer`

**British spelling** — colour, behaviour, organisation, recognise.

**Curly quotes** in copy that will be shown to a client — `“Contact”` not
`"Contact"`.

**Sentence case** for everything except the eyebrow and title.

## Words to avoid

| Avoid | Use |
|---|---|
| "clearly", "obviously", "simply" | delete — if it were obvious it would not be a finding |
| "bad", "ugly", "wrong", "terrible" | describe the effect instead |
| "best practice" alone | name the practice and why it exists |
| "modern", "clean", "sleek" | say what specifically changes |
| "users may find it confusing" | say what they cannot do |
| "consider adding", "you might want to" | state the fix directly |
| "leverage", "utilise", "solutioning" | use, use, work |
| "robust", "comprehensive", "seamless", "holistic" | name the property you mean |
| "it's worth noting", "in terms of" | delete and start the sentence at the point |

That table is the short version. The full list is machine-checked — see
`references/ai-writing.md` and run:

```bash
python3 scripts/check_prose.py --project <project>
```

Text inside double quotes is exempt, so quoting the client's own copy back at
them never trips it. Quoting is usually the strongest form the observation can
take, and the check is built to encourage it rather than punish it.

Passing that check is the floor. Everything above this line is the standard.

## Audience variants

The findings do not change. The framing around them does.

### Prospect (sales tool)

The audit is proving you see things they do not. Be generous but not soft.

- Open the summary with what the site is *trying* to do, then the gap
- Emphasise business consequence — enquiries lost, trust not established
- Keep the fix general enough that implementing it is a project, not a checkbox
- Never mock. A prospect who feels embarrassed does not hire you
- Include 2–3 things that genuinely work — it makes the criticism credible
- Aim for 25–45 findings. Enough to show depth, not so many it reads as a pile-on

### Existing client (progress report)

Continuity matters more than impact.

- Open by acknowledging what has improved since last time
- Group by what is newly found vs still outstanding
- Fixes should be specific and scoped — they have the context
- Reference previous audit numbers where you have them
- Aim for 15–30 findings

### Internal (project scoping)

This is a working document. Optimise for the person who has to build from it.

- Blunt is fine. Skip the diplomacy
- Every finding needs a fix specific enough to estimate
- Flag unknowns explicitly ("needs a CMS audit to confirm")
- Severity drives sequencing, so be strict about it
- Aim for exhaustive — 40+ is fine

## The summary narrative

Three paragraphs, in this order:

1. **The one-line diagnosis.** What the site needs, stated as a need not a
   complaint. *"What the site needs is a clearer service experience, stronger
   content governance, and a more scalable technical foundation."*
2. **The pattern.** Name what recurs across pages, and ground it in what users
   actually arrive to do. *"Across every page, the same pattern appears: the
   core structure is there, but the experience does not yet fully support the
   way people use websites. Users arrive with practical needs..."*
3. **The gaps.** The specific themes, listed plainly. *"The main gaps are around
   clarity, consistency, and trust. CTAs promise actions that are not actually
   available, key information is repeated or inconsistent..."*

Note the second paragraph's move: it describes the *user's* job before it
describes the site's failure. That is what separates this from a checklist.

Keep each paragraph under 60 words. The counts grid does the quantifying.
