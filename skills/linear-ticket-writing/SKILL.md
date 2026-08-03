---
name: linear-ticket-writing
description: Draft, review, or improve Linear tickets that will be executed by Claude Code (or any agent) through the Linear MCP server. Use whenever the user asks to "write a ticket," "draft an issue," "turn this into a Linear ticket," "make this a backlog item," or "review/clean up this ticket" — especially when Claude Code, an AI agent, or an MCP workflow is mentioned. Also use when the user pastes a vague task, bug report, or idea and wants it shaped into something an agent can execute end-to-end without follow-up questions. Produces tickets that are both agent-friendly (full context, clear goal, explicit constraints, testable acceptance criteria) and Linear-MCP-friendly (clean title, markdown description, named labels, suggested priority/estimate, explicit relationships) so they can be handed directly to the Linear MCP `create_issue` tool without reformatting.
---

# Linear Ticket Writing

Write Linear tickets that an agent — usually Claude Code via the Linear MCP server — can pick up and finish without asking clarifying questions, and that the Linear MCP can create in a single tool call.

A good ticket here does two jobs at once. It carries enough context, intent, and acceptance criteria for an agent with zero memory of the user's prior conversations to execute it end-to-end. And it's shaped so the Linear MCP server can drop it into Linear cleanly — title in the title field, markdown body in the description field, named labels attached, priority and estimate filled in when inferable, relationships expressed as real ticket IDs.

The user almost always wants a single deliverable: a ready-to-create ticket. Produce that, then briefly note the suggested labels, priority, estimate, and any relationships so they can confirm before the MCP call.

## When you're invoked

Common shapes the user's request will take:

- "Write a Linear ticket for X" / "Draft an issue for Y"
- "Turn this into a ticket" (often with a pasted Slack message, bug report, or rough idea)
- "Make this Claude-Code-ready"
- "Review this ticket — is it good enough for an agent?"
- "Clean this up before I send it to Linear"

If the request is genuinely ambiguous about what the work is, ask one focused clarifying question before drafting. Otherwise draft first — it's faster to react to a concrete draft than to interview the user up front.

## The four-section ticket template

Every ticket body uses these four sections, in this order, as H2 headings. Skipping a section is almost always a mistake — if a section feels empty, that's usually a signal the ticket isn't ready, not that the section is unnecessary.

```markdown
## Context
## Goal
## Constraints
## Acceptance criteria
```

### Context

What the agent needs to know that it can't discover from the codebase or a quick search. The agent has no memory of prior conversations, so anything implicit between you and the user must become explicit here.

Cover, when relevant: why this work matters now, what triggered it, what's already been tried, where the relevant code/docs/data live (with paths or links), which conventions or patterns to follow, and any domain knowledge an outsider wouldn't have. Link to related tickets, PRs, design docs, and Slack threads by URL — don't paraphrase them when a link will do.

Keep it to what the agent actually needs. Two tight paragraphs beats a page of backstory.

### Goal

One or two sentences naming the outcome. Outcome, not steps. "Users can reset their password from the login screen" is a goal; "Add a `POST /reset` endpoint and a form component" is an implementation sketch that belongs in Constraints if at all.

If the work is exploratory (research, spike), the goal is the artifact: "A written recommendation on which queue library to adopt, with tradeoffs."

### Constraints

The boundaries on how the work gets done. This is where you head off the wrong solution. Include:

- Tech choices that are fixed (language, framework, library versions)
- Files or modules to touch — and ones to leave alone
- Patterns to follow (link to an existing example in the repo when possible)
- Performance, security, accessibility, or compliance requirements
- What's explicitly out of scope
- Dependencies on other tickets or external work, with IDs

If a constraint is "use the existing pattern in `src/auth/session.ts`", say so by path. Agents follow specific pointers; they invent things when given vague ones.

### Acceptance criteria

A bulleted checklist of testable statements. Each item should be something a reviewer (or the agent itself) can verify is done.

Good acceptance criteria are:

- Concrete: "Submitting an empty email shows the error `Email is required`"
- Independent: each bullet stands on its own
- Complete: together they describe a done ticket, including tests, docs, and any migration steps

If the ticket produces a deliverable (deck, doc, report), the criteria describe the deliverable's properties: format, length, sections, where it lives, who's seen it.

## Title rules

The title is a single line that an engineer scanning a backlog can understand without opening the ticket.

- Action-oriented: start with a verb (`Add`, `Fix`, `Refactor`, `Investigate`, `Draft`, `Migrate`, `Document`).
- Hints at the deliverable: the reader should be able to guess roughly what "done" looks like.
- ~50–80 characters. Hard cap around 100.
- No trailing punctuation, no ticket IDs, no `[WIP]` or `[DRAFT]` prefixes.
- Avoid vague verbs alone (`Update X`, `Improve Y`) — say what about it.

**Examples:**

- Good: `Add rate limiting to public /search endpoint (100 req/min/IP)`
- Good: `Investigate why nightly ETL job started failing on 2026-05-18`
- Good: `Draft Q3 board update deck (12 slides, finance-reviewed numbers)`
- Bad: `Rate limiting` (noun pile, no verb, no scope)
- Bad: `Fix the thing in search` (vague, no deliverable)
- Bad: `Update search` (vague verb, no specifics)

## Label rules

Apply labels by name so the Linear MCP can attach them in the create call. Use the four canonical labels below; add team-specific labels only if the user has mentioned them.

- **`code`** — the ticket's deliverable is a code change (feature, fix, refactor, migration).
- **`research`** — the deliverable is understanding: an investigation, spike, comparison, or written recommendation. No production code expected.
- **`deliverable`** — the deliverable is a non-code artifact: a deck, doc, report, spec, diagram, dataset.
- **`claude-ready`** — apply only when the ticket meets the pre-flight checklist below. This label is a signal to the human reviewer (and to any agent routing layer) that the ticket can be handed to Claude Code without further editing. If anything's still fuzzy, leave it off and flag what's missing.

A ticket usually gets exactly one of `code` / `research` / `deliverable` plus, when ready, `claude-ready`. Hybrid tickets (research that produces a small code spike) usually mean the work should be split — see Anti-patterns.

## Priority and estimate

Suggest these when they're inferable from context; otherwise omit and let the human set them.

- **Priority** (Linear's scale: 1 Urgent, 2 High, 3 Medium, 4 Low). Infer from explicit user signals ("this is blocking the launch" → High/Urgent) or from the nature of the work (production outage → Urgent; nice-to-have polish → Low).
- **Estimate** (story points, usually 1/2/3/5/8). Suggest only when scope is clear. A bounded code change touching 1–2 files is typically 1–2; a multi-file feature with tests is 3–5; anything you'd estimate above 5 should probably be split.

When you suggest either, say so briefly under the ticket: "Suggested priority: 2 (High) — user said this blocks the partner integration."

## Relationships

If the user mentions another ticket, a blocker, or a parent epic, capture it explicitly with the Linear ticket ID (e.g., `ENG-1423`). State the relationship type so the MCP can set it correctly:

- `Parent: ENG-1400`
- `Blocks: ENG-1450`
- `Blocked by: ENG-1399, ENG-1402`
- `Related: ENG-1380`

Put these as a short list at the bottom of the description, under an `## Links` heading, alongside any reference URLs. The MCP create call handles parent/child and blocking via separate fields — see the handoff section.

## Pre-flight checklist

Run through this before declaring a ticket ready and applying `claude-ready`. If any answer is no, fix it or leave `claude-ready` off and call out the gap.

1. Could a new engineer with no prior context start this ticket today and know what "done" looks like?
2. Is the goal one outcome, not several bundled together?
3. Does Context link to (not paraphrase) the relevant code, docs, and prior discussion?
4. Are constraints specific — named files, named patterns, named libraries — not vague preferences?
5. Is every acceptance criterion something a reviewer can objectively check?
6. Does the title start with a verb and hint at the deliverable?
7. Are labels, priority, estimate, and relationships either filled in or deliberately omitted?
8. Could the Linear MCP take this description string and create the issue without you reformatting anything?

## Worked examples

### Example 1: Code task

**Title:** `Add rate limiting to public /search endpoint (100 req/min/IP)`

**Description:**

```markdown
## Context
The public `/search` endpoint has been hit by scraping traffic three times in the past two weeks (see incident notes in `docs/incidents/2026-05-09-search-scraping.md`). We have an internal rate limiter used on `/api/v2/*` routes — see `src/middleware/rate_limit.ts` — but it isn't applied to the public search path. The product team is OK with 100 requests/minute/IP for unauthenticated traffic; authenticated users should be unaffected.

## Goal
Anonymous traffic to `/search` is capped at 100 requests/minute per IP, returning HTTP 429 with a clear error body when exceeded. Authenticated requests bypass the limit.

## Constraints
- Reuse `src/middleware/rate_limit.ts` — do not introduce a new library.
- Configuration lives in `config/rate_limits.json`; add a `search_public` entry.
- The 429 response body matches the existing shape used by `/api/v2/*` (`{ error, retry_after_seconds }`).
- Log throttled requests via the existing `logger.warn` path with `event: "rate_limit_hit"`.
- Do not change behavior for authenticated requests (token in `Authorization` header).
- Out of scope: per-user limits, distributed rate limiting across regions.

## Acceptance criteria
- 101st anonymous request from a single IP within a 60-second window returns HTTP 429.
- 429 response body matches `{ error: string, retry_after_seconds: number }`.
- Authenticated requests are not throttled regardless of volume.
- Integration test added under `tests/integration/search_rate_limit.test.ts` covering: under-limit, over-limit, authenticated bypass.
- `config/rate_limits.json` documents the new entry in the same style as existing entries.
- Throttled requests appear in logs with `event: "rate_limit_hit"`.

## Links
- Incident notes: `docs/incidents/2026-05-09-search-scraping.md`
- Existing middleware: `src/middleware/rate_limit.ts`
- Related: ENG-1380 (auth-bypass discussion)
```

**Suggested metadata:** labels `code`, `claude-ready`; priority 2 (High) — recurring incident; estimate 3.

### Example 2: Research task

**Title:** `Investigate options for replacing the in-memory job queue (write recommendation)`

**Description:**

```markdown
## Context
Our background jobs currently run through an in-process queue in `src/jobs/queue.ts`. As of last week's load test (results in `docs/loadtest/2026-05-15.md`), it drops jobs under sustained 500 req/s and has no retry semantics. Leadership wants a recommendation before the Q3 planning meeting on June 10. We've informally discussed BullMQ, Sidekiq-style approaches, and SQS, but no one has compared them in writing.

## Goal
A written recommendation on which job queue technology to adopt, with tradeoffs, that the team can act on in Q3 planning.

## Constraints
- Output is a markdown doc at `docs/proposals/job-queue-2026.md`.
- Cover at minimum: BullMQ, AWS SQS, and at least one self-hosted alternative.
- Evaluate against: throughput at 500 req/s sustained, at-least-once delivery, retry/backoff, ops burden, cost at our current scale (see `docs/infra/scale.md`), and migration cost from the current implementation.
- No code changes in this ticket. A follow-up ticket will own the actual migration.
- Length target: 1,500–2,500 words.

## Acceptance criteria
- `docs/proposals/job-queue-2026.md` exists with sections: Background, Options, Comparison table, Recommendation, Migration sketch, Open questions.
- Comparison table covers all six evaluation dimensions named in Constraints.
- Recommendation names one option and gives at least three concrete reasons.
- Doc is linked in the Q3 planning agenda (`docs/planning/q3-2026.md`).

## Links
- Load test: `docs/loadtest/2026-05-15.md`
- Current implementation: `src/jobs/queue.ts`
- Scale assumptions: `docs/infra/scale.md`
```

**Suggested metadata:** labels `research`, `claude-ready`; priority 3 (Medium) — needed by June 10 but not blocking; estimate 3.

### Example 3: Non-code deliverable

**Title:** `Draft Q2 customer retention readout deck (10–12 slides, exec audience)`

**Description:**

```markdown
## Context
The exec team wants a Q2 retention readout at the all-hands on June 20. Data is already pulled — see `data/retention/q2_2026.csv` and the dashboard at https://internal.example.com/dashboards/retention. Last quarter's deck (`decks/q1_2026_retention.pptx`) is the format reference; reuse its section structure and visual style. Audience is execs, not analysts — assume they want the story, not the methodology.

## Goal
A 10–12 slide deck telling the Q2 retention story to the exec team, ready for review by the data lead before the June 20 all-hands.

## Constraints
- Output: `.pptx` saved to `decks/q2_2026_retention.pptx`.
- Match the section structure of `decks/q1_2026_retention.pptx`: TL;DR → Cohort trends → Churn drivers → What we shipped → Asks.
- Use only numbers from `data/retention/q2_2026.csv` or the linked dashboard. No invented figures.
- Each slide has a one-sentence takeaway as the title (not a topic label).
- Charts use the company template colors already present in the Q1 deck.

## Acceptance criteria
- Deck is 10–12 slides, in the order above.
- Every chart's source is cited in the speaker notes.
- TL;DR slide states the headline number and the single most important change vs Q1.
- "Asks" slide names at least one concrete decision the execs are being asked to make.
- File saved to `decks/q2_2026_retention.pptx` and the path shared in #data-readouts.

## Links
- Q2 data: `data/retention/q2_2026.csv`
- Q1 deck for format: `decks/q1_2026_retention.pptx`
- Dashboard: https://internal.example.com/dashboards/retention
```

**Suggested metadata:** labels `deliverable`, `claude-ready`; priority 2 (High) — fixed date; estimate 2.

## Anti-patterns to avoid

**Verb-only or noun-only titles.** `Update search` and `Rate limiting` both fail. The title needs verb + object + enough specifics to hint at done.

**Bundled tickets.** "Add rate limiting and also clean up the auth middleware and write a retention deck" is three tickets. If you can't write a single Goal sentence without using "and" between unrelated outcomes, split. Bundled tickets break agent execution because there's no single completion state.

**Missing or untestable acceptance criteria.** "It works well" and "users are happy" are not acceptance criteria. If a reviewer can't check it, the agent can't aim at it.

**Implicit context.** "You know, the thing we discussed" — the agent doesn't. Anything that lives only in chat history must be written into Context, or the agent will guess and guess wrong.

**Solution dressed up as a goal.** "Add a Redis-backed cache to the user service" presupposes the solution. The goal is the outcome (e.g., "User profile reads return in under 50ms p95"); Redis is a constraint or an implementation detail.

**Vague constraints.** "Follow our patterns" tells the agent nothing. Name the file, the function, or the existing example to follow.

**`claude-ready` applied to a fuzzy ticket.** The label is a promise. If the pre-flight checklist has any "no", leave the label off and call out the gap — that's more useful than a false green light.

## Handoff to the Linear MCP

The output should be structured so the user (or another agent) can pass it to the Linear MCP `create_issue` tool in one call. Exact field names vary by MCP version, but the shape is consistent.

**Fields to populate:**

- `title` — the single-line title, no markdown, no trailing punctuation.
- `description` — the full markdown body (the four H2 sections plus `## Links`) as a single string. Linear renders standard markdown: H1–H3, ordered/unordered lists, bold/italic, inline code, fenced code blocks, links, blockquotes, and task lists (`- [ ]`). Avoid HTML, tables nested inside list items, and any exotic markdown extensions.
- `team` or `team_id` — the team the ticket belongs to. Ask if unknown.
- `labels` — pass label names as an array of strings exactly as named above (`["code", "claude-ready"]`). The MCP will resolve names to IDs.
- `priority` — integer 1–4 if suggested.
- `estimate` — integer if suggested.
- `parent_id` — Linear ID of the parent ticket if there is one.
- `assignee` — leave unset unless the user specified one.

**Relationships beyond parent/child** (blocks, blocked-by, related) are usually set via a separate MCP call after the issue is created, since they need the new issue's ID. List them clearly in the `## Links` section of the description so whoever runs the MCP can issue the follow-up calls.

**Format the description string carefully:**

- Use literal `\n` newlines between lines, not escaped sequences, when handing the string to the MCP.
- Keep code blocks fenced with triple backticks and a language hint when relevant.
- Don't wrap the whole description in quotes or a code fence — pass the markdown directly.

**After drafting, present the result to the user like this:**

1. The title on its own line.
2. The full description body in a fenced markdown block so they can copy it cleanly.
3. A short metadata summary: suggested labels, priority, estimate, and any relationships.
4. A one-line note on what the Linear MCP call would do, so they can confirm before triggering it.

That structure makes the ticket reviewable in chat and trivially transferable to the MCP — which is the whole point.
