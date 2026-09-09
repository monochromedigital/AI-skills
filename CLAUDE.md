# CLAUDE.md

Instructions for agents working in this repo.

## Start here

`HANDOFF.md` is the orientation document: what this project is, how it is set
up, what state it is in, what is decided, what is open, and the checklist to run
before touching feature code. Read it on a first session or on a new machine.
This file carries only the rules that must not be missed.

## Never merge over a red check

Before any `gh pr merge`, confirm every check has finished and passed:

```bash
gh pr view <N> --json statusCheckRollup --jq '[.statusCheckRollup[]|{name,conclusion}]'
```

Every entry must read `SUCCESS`. An empty `conclusion` means the run is still
going — wait for it rather than merging on an incomplete rollup.

**Nothing else enforces this.** `gh pr merge` does not refuse a failing check on
its own, and a required status check — the thing that would refuse it — needs a
paid plan on a private repo. This instruction is the only gate.

It exists because of a specific event. PR #2 merged 48 seconds after its check
concluded red; `main` stayed red for a day and two more commits merged on top of
it before anyone acted. The pre-push hook cannot help here: merges happen on
GitHub's servers, not on a machine a hook runs on. A person might hesitate at a
red X. An automated `gh pr merge` will not.

If a check is red and you believe the merge is still correct, **say so and ask.**
Do not merge and explain afterwards.

## Before pushing

```bash
make check      # shared-file rules, Python syntax, agencies resolve
make hooks      # once per clone: runs make check before every push
```

The hook is a guardrail, not enforcement — `git push --no-verify` skips it, and
it reads the working tree rather than the commits being pushed. CI is the
authority.

## When a shared-file check fails

Do not resolve it by copying one skill's version over the other until you have
checked that both skills genuinely want the same bytes. Syncing a value that
differs per deliverable is how a sitemap ends up labelled as an audit — that is
the failure this rule was written from, not a hypothetical.

The reasoning lives in `references/project-contract.md` §2b, which
`build_standalone.py` names in its error output. Read it there; do not restate
it here, because a rule kept in two files is the same drift the contract exists
to prevent.
