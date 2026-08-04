# Writing that does not read as generated

An audit is sold on the claim that somebody looked at the site. An IA board is
sold on the claim that somebody thought about the business. One paragraph of
"leverage a robust, holistic ecosystem" and both claims are gone — regardless
of who actually wrote it, and regardless of how good the findings underneath
are. The reader stops reading the argument and starts reading the prose.

That is why this is a build step and not a style preference.

The word lists come from
[avoid-ai-writing](https://github.com/conorbronsdon/avoid-ai-writing) by Conor
Bronsdon, MIT licensed, trimmed to what applies to a client deliverable and
extended with the entries these skills already banned. The data lives in
`assets/ai-writing.json`; this file describes the rules. Edit the JSON, never a
copy of the list pasted somewhere else.

## Running it

```bash
python3 scripts/check_prose.py --project <project>
python3 scripts/check_prose.py --project <project> --strict
python3 scripts/check_prose.py --file <project>/findings.json
```

It reads `findings.json` and `ia.json` and reports by JSON path:

```
findings.json: slides[1].findings[0].observation - "seamless" (tier 1)
ia.json: personas[2].context - "harness", "empower" (tier 2 cluster)
```

Run it in the verification step, before anything is rendered or sent.

## What it flags

**Tier 1 — always an error.** Words that read as generated on sight: delve,
robust, comprehensive, seamless, leverage, holistic, actionable, impactful,
cutting-edge, vibrant, thriving, intricate, ever-evolving, synergy, learnings,
best practices, deep dive, thought leader.

**Tier 2 — an error when two land in the same field.** Harness, foster,
elevate, streamline, empower, facilitate, crucial, ecosystem, myriad,
transformative, cornerstone, paramount, nascent, burgeoning. One is ordinary
English. Three in a paragraph is a fingerprint.

**Tier 3 — a warning, never an error.** Significant, innovative, effective,
dynamic, compelling, exceptional, remarkable, sophisticated. These are real
words doing real work most of the time; they only mean something in bulk, so
the check reports three or more in one field and never blocks the build.

**Chatbot artifacts, filler, hollow judgement, agency cliché — always errors.**
"It's worth noting", "In terms of", "at the end of the day", "clearly",
"obviously", "could potentially", "experts believe", "the future looks bright",
"consider adding", "user-friendly", "look and feel", leftover `[Your Name]`
placeholders and `utm_source=chatgpt.com` parameters.

## Quoted text is exempt

An audit quotes the client's own page copy constantly. Their headline saying
"leverage our comprehensive platform" is *evidence* — it is very often the
finding itself — and flagging it would teach people to stop quoting, which
would make the audit worse.

Anything inside double quotes, straight or curly, is skipped. So this passes:

> The hero reads "Leveraging comprehensive solutions for the modern
> enterprise", which names no service and no market.

and this does not:

> The hero leverages a comprehensive value proposition.

If the checker flags something that is genuinely the client's words, the fix is
to quote it properly, not to argue with the check.

## What does **not** apply here

The upstream skill is tuned for blog posts, LinkedIn and investor email. Some
of its rules contradict how these deliverables are built, and following them
would damage the documents. They are deliberately absent from the JSON and must
stay absent:

**The em-dash cap (1 per 1,000 words).** House style uses them. `voice.md`,
the reference deck and every card in the board lean on them for the
observation → consequence turn. This is a stylistic signal at worst.

**Curly quotes as a signal.** The audit skill's `voice.md` *mandates* curly
quotes in copy shown to a client. The two rules cannot both hold; the house
rule wins.

**"Convert bullet-heavy sections to prose."** The audit is finding cards. The
board is section cards. The format is the deliverable.

**"Bullet lists of bare noun phrases (5+ symmetric adj+noun)."** A page column
of section cards is exactly this shape, by design.

**"Compulsive triads."** The summary narrative is specified as three
paragraphs, and every finding is observation → consequence → fix. The rule of
three here is structure, not a tic.

**Uniform paragraph length.** Summary paragraphs are capped at 60 words on
purpose, so they stay scannable next to the counts grid.

**Everything social.** Hashtag stuffing, emoji in headers, endorsement closers,
"I recently had the pleasure of". Wrong medium.

## The part no script can check

The checker catches vocabulary. It cannot tell you whether the sentence says
anything. The rules that matter more live next to it — `voice.md` in the audit
skill (quantify where a number exists, describe the page rather than the people
who built it, one finding per card, be specific enough to act on) and the
In-plain-words formula in `methodology.md` in the sitemap skill (a metaphor,
then one named actor doing one specific thing).

A finding with none of the banned words that still says "the navigation could
be improved" passes this check and should not have been written.

Passing `check_prose.py` is the floor, not the standard.
