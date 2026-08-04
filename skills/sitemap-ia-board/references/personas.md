# Personas

Personas come **before** the IA in this skill, because they are the argument
for it. A sitemap without them is a list of pages someone liked. A sitemap with
them is a set of answers to "who is this page for, and what were they unable to
do before it existed?"

That is also the test for whether a persona belongs in the document at all:

> **A persona that does not change the IA does not belong in the document.**

If cutting a persona would not remove a page, a section, a form field or a
funnel, it is decoration. Cut it. Two or three that move the structure beat
five that describe the market.

## Ask how they should be grounded

One question, in the same `AskUserQuestion` call as the project folder and the
rest of the brief:

- **Research the client has** — interviews, sales-call notes, CRM exports,
  support tickets, analytics segments
- **Evidence the client has already published** — a projects archive, a client
  list, case studies, testimonials, a portfolio
- **The client's own account** — what the founder or sales lead says the buyers
  are, without data behind it
- **None of the above** — nothing to work from

Whatever comes back, **the basis goes in the deliverable.** In the `evidence`
block of `ia.json` and in the board's basis paragraph, in plain language:

> Derived from the 50 installations listed in Northgate's own project archive
> (2019–2026), clustered by service. **No primary research has been
> commissioned**, so treat the weightings as what the company has actually
> sold, not as what the market wants.

"No primary research" is an acceptable answer. Silence is not. A persona
presented without its basis reads as fact, gets quoted in a proposal, and
becomes the reason a page exists — and nobody remembers it was invented on a
Tuesday.

## Where a site already exists, count what they sold

Prefer evidence the client has already published over invention. It is on the
site, it is free to gather, and it is defensible in the room.

A projects archive, client list, case-study index or portfolio is a record of
who actually bought. Read it, cluster it by what was sold, and derive the
persona set from the clusters — not from the industry's stock personas.

Then **state the count behind each one**: "22 of 50 installations", "15 of 50",
"13 of 50". A number does two things a paragraph cannot: it survives a
sceptical stakeholder, and it makes the weighting arguable in a useful way. If
the client says "actually the small accounts are the future", that is now a
conversation about strategy rather than about whether the persona is real.

Where there is genuinely nothing to count — a new brand, a first site — say the
persona is derived from the brief, and weight it by the client's own stated
priority rather than inventing a percentage.

## What each persona carries

| Field | What it is |
|---|---|
| `name` | A first name. Not "Persona A" — the point is that people say it out loud |
| `role` | Job title plus the kind of company. "Operations manager, food importer" |
| `weight` | The evidence badge: the count, or the stated basis |
| `quote` | One sentence in their voice, about the decision, not about the brand |
| `context` | Two or three sentences: what they are judged on, how they buy, from what device |
| `wants` | What they need from the site. Three or four, concrete |
| `blocked_by` | What stops them **today**, each with a `fid` when an audit explains it |
| `journey` | Their route through the *proposed* sitemap, as `pages[].id` values |
| `needs_pages` | The pages that exist because of them — the persona's receipt |

`needs_pages` is the enforcement of the rule at the top. If it is empty, the
persona changed nothing.

## Blockers and the audit

When `findings.json` is in the project folder, "what stops them today" is not
speculation — it is diagnosed, and the diagnosis has an id.

Write the blocker in the persona's terms and attach the finding's id:

```jsonc
{ "text": "The nav is unreadable on her low-brightness work display",
  "fid": "f-2b7c7a60d1" }
```

**The id, and nothing else from the finding.** Never copy the audit's wording
into the persona — the renderer resolves the id and shows the finding's current
text, so the two documents cannot drift apart when someone rewords it. See the
project contract §7.

With no audit in the folder, blockers are still worth writing, but they are
inference and carry no `fid`. Never invent one: a `fid` in a greenfield project
fails validation, which is the point.

## Colour

Each persona gets a `colour` used as the card's top bar in both the standalone
board and the shared renderer. Pick from the discipline palette so the two
documents look like one system — `#DF6630` (UX orange), `#2E8F86` (CRO teal),
`#866FBC` (purple), `#1E8FD9` (blue).
