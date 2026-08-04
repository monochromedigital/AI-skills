#!/usr/bin/env python3
"""
check_prose_standalone.py - Scans the client-facing prose in a project folder for the
words and constructions that make a deliverable read as generated.

An audit or an IA board is sold on the claim that somebody looked. A document
carrying "leverage a robust, holistic ecosystem" undoes that claim in one line,
whoever actually wrote it. This is the portable copy: the word lists are embedded, so it runs in
any session, or on any machine with Python, against any findings.json
or ia.json, and needs nothing else on disk.

It reads `findings.json` and `ia.json` and reports by JSON path, the same way
the other validators in these skills do:

    findings.json: slides[1].findings[0].observation - "seamless" (tier 1)
    ia.json: personas[2].context - "harness", "empower" (tier 2 cluster)

**Quoted text is exempt.** An audit quotes the client's own page copy
constantly, and their headline is evidence, not your writing. Anything inside
double quotes - straight or curly - is skipped.

Severity:
  error    tier 1, chatbot artifacts, filler, hollow judgement, agency cliche,
           and two or more tier-2 words in one field
  warning  three or more tier-3 words in one field. Ordinary English in
           isolation; a fingerprint in bulk. Never fails the run unless --strict

Usage:
  python3 check_prose_standalone.py --project <project>
  python3 check_prose_standalone.py --project <project> --strict
  python3 check_prose_standalone.py --file <project>/findings.json
"""

# ---------------------------------------------------------------------------
# GENERATED FILE - do not edit.
#
# Built from skills/website-assessment/scripts/check_prose.py
#          and skills/website-assessment/assets/ai-writing.json
# Source digest: c5161e32cc230959
#
# To change the word lists, edit assets/ai-writing.json in the skills and run
#     python3 scripts/build_standalone.py
# ---------------------------------------------------------------------------

import argparse
import json
import re
import sys
from pathlib import Path

WORDS = json.loads(r"""
{
  "_comment": "Word and phrase lists for scripts/check_prose.py. Edit here only - the reference doc describes the rules, this file holds the data, so the two cannot drift. Keep this file byte-identical in every skill that carries it.",
  "_source": "Tiers 1-3, template phrases, transitions and artifacts adapted from avoid-ai-writing by Conor Bronsdon (MIT), https://github.com/conorbronsdon/avoid-ai-writing. Trimmed to what applies to client deliverables and extended with the agency-specific entries below. See references/ai-writing.md for the rules that were deliberately left out.",
  "_license": "MIT (upstream). This subset carries the same terms.",

  "tier1": {
    "_rule": "Always an error. These read as generated on sight.",
    "words": [
      "delve", "landscape", "tapestry", "realm", "paradigm", "embark", "beacon",
      "robust", "comprehensive", "cutting-edge", "leverage", "leveraging", "pivotal",
      "underscores", "underscoring", "meticulous", "meticulously", "seamless",
      "seamlessly", "game-changer", "game-changing", "utilize", "utilise", "vibrant",
      "thriving", "bustling", "intricate", "complexities", "ever-evolving", "enduring",
      "daunting", "holistic", "actionable", "impactful", "learnings", "synergy",
      "synergies", "interplay", "solutioning"
    ],
    "phrases": [
      "watershed moment", "deep dive", "thought leader", "thought leadership",
      "best practices", "best practice", "in today's fast-paced", "in the ever-evolving"
    ]
  },

  "tier2": {
    "_rule": "An error when two or more appear in the same field. One is ordinary English; three in a paragraph is a fingerprint.",
    "words": [
      "harness", "navigate", "foster", "elevate", "unleash", "streamline", "empower",
      "bolster", "spearhead", "resonate", "revolutionize", "revolutionise", "facilitate",
      "underpin", "nuanced", "crucial", "multifaceted", "ecosystem", "myriad", "plethora",
      "encompass", "catalyze", "catalyse", "reimagine", "galvanize", "galvanise",
      "augment", "cultivate", "illuminate", "elucidate", "juxtapose", "transformative",
      "cornerstone", "paramount", "poised", "burgeoning", "nascent", "quintessential",
      "overarching"
    ],
    "phrases": []
  },

  "tier3": {
    "_rule": "A warning, never an error. Ordinary words that only signal anything in bulk - reported when a single field carries three or more, so a real sentence is never blocked.",
    "words": [
      "significant", "significantly", "innovative", "effective", "dynamic", "scalable",
      "compelling", "unprecedented", "exceptional", "remarkable", "sophisticated",
      "instrumental", "world-class", "state-of-the-art", "best-in-class"
    ],
    "phrases": []
  },

  "artifacts": {
    "_rule": "Always an error. Every one of these has reached a client at least once somewhere.",
    "words": [],
    "phrases": [
      "i hope this helps", "let's dive in", "lets dive in", "in this article",
      "in this report we will", "great question", "excellent point",
      "let me think step by step", "breaking this down", "it's worth noting",
      "it is worth noting", "interestingly,", "notably,",
      "citeturn", "oai_citation", "utm_source=chatgpt.com", "referrer=grok.com",
      "[your name]", "[insert", "[client name]", "xx-xx"
    ]
  },

  "filler": {
    "_rule": "Always an error. Words spent before the sentence starts.",
    "words": ["moreover", "furthermore"],
    "phrases": [
      "in terms of", "when it comes to", "the reality is that", "at the end of the day",
      "that being said", "in conclusion", "in summary", "it is important to note",
      "it's important to note", "in an era where", "in today's", "needless to say",
      "first and foremost"
    ]
  },

  "hollow": {
    "_rule": "Always an error. Judgement with nothing behind it, hedges that refuse to commit, and conclusions that say nothing.",
    "words": ["clearly", "obviously", "simply", "truly", "genuinely"],
    "phrases": [
      "could potentially", "might eventually", "may potentially", "worth noting that",
      "experts believe", "studies show", "research suggests", "it is widely believed",
      "the future looks bright", "only time will tell", "a step towards",
      "a step toward", "whether you're", "whether you are",
      "i recently had the pleasure", "let's be clear", "here's the thing",
      "the catch?", "the kicker?"
    ]
  },

  "agency": {
    "_rule": "Always an error. Specific to audit and IA writing - each one was already banned in voice.md, and each is a finding that has stopped being a finding.",
    "words": ["bad", "ugly", "terrible", "modern", "clean", "sleek", "beautiful", "stunning"],
    "phrases": [
      "consider adding", "you might want to", "we noticed that", "users may find",
      "user-friendly", "look and feel", "take it to the next level",
      "in order to improve", "best-in-breed"
    ]
  }
}
""")

ERROR_GROUPS = ("tier1", "artifacts", "filler", "hollow", "agency")
TIER2 = "tier2"
TIER3 = "tier3"
TIER2_CLUSTER = 2   # distinct tier-2 hits in one field before it is an error
TIER3_CLUSTER = 3   # distinct tier-3 hits in one field before it is a warning

LABELS = {
    "tier1": "tier 1",
    "tier2": "tier 2 cluster",
    "tier3": "tier 3 cluster",
    "artifacts": "chatbot artifact",
    "filler": "filler",
    "hollow": "hollow",
    "agency": "agency cliche",
}


# ---------------------------------------------------------------- text
def normalise(text):
    """Curly punctuation to straight, so one pattern matches both. voice.md
    mandates curly quotes in client copy, so this is not optional."""
    return (str(text)
            .replace("’", "'").replace("‘", "'")
            .replace("“", '"').replace("”", '"')
            .replace("–", "-").replace("—", "-"))


QUOTED = re.compile(r'"[^"]*"')


def strip_quoted(text):
    """Drop anything in double quotes. The client's own headline is evidence,
    not prose you wrote, and flagging it would train people to stop quoting."""
    return QUOTED.sub(" ", text)


def variants(word):
    """'empower' has to catch 'empowers' and 'empowering', or a paragraph
    three tier-2 words deep slips through on grammar alone. Explicit variants
    rather than a stemmer: the list is small and this stays debuggable."""
    v = {word}
    if word.endswith("y") and len(word) > 3:
        v.add(word[:-1] + "ies")
    if word.endswith(("s", "x", "z", "ch", "sh")):
        v.add(word + "es")
    else:
        v.add(word + "s")
    if word.endswith("e"):
        v.update({word + "s", word + "d", word[:-1] + "ing"})
    else:
        v.update({word + "ed", word + "ing"})
    return sorted(v, key=len, reverse=True)


def compile_terms(spec):
    """Build (pattern, term) pairs. \\b fails on terms ending in punctuation
    ('the catch?'), so bound on non-word characters instead. Words get their
    inflections; phrases are matched as written."""
    out = []
    for word in spec.get("words", []):
        alts = "|".join(re.escape(v) for v in variants(word))
        out.append((re.compile(r"(?<!\w)(?:%s)(?!\w)" % alts, re.IGNORECASE), word))
    for phrase in spec.get("phrases", []):
        out.append((re.compile(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)",
                               re.IGNORECASE), phrase))
    return out


def load_terms():
    return {g: compile_terms(WORDS[g]) for g in WORDS if not g.startswith("_")}


# ---------------------------------------------------------------- field collection
def findings_fields(data):
    """(json path, text) for every field a client actually reads."""
    for i, slide in enumerate(data.get("slides", []) or []):
        for j, f in enumerate(slide.get("findings", []) or []):
            base = "slides[%d].findings[%d]" % (i, j)
            for key in ("observation", "detail", "fix", "benchmark", "scope"):
                if f.get(key):
                    yield "%s.%s" % (base, key), f[key]
    for k, para in enumerate((data.get("summary") or {}).get("narrative", []) or []):
        if para:
            yield "summary.narrative[%d]" % k, para


def ia_fields(data):
    ev = data.get("evidence") or {}
    if ev.get("note"):
        yield "evidence.note", ev["note"]
    for i, p in enumerate(data.get("personas", []) or []):
        for key in ("quote", "context"):
            if p.get(key):
                yield "personas[%d].%s" % (i, key), p[key]
        for j, w in enumerate(p.get("wants", []) or []):
            yield "personas[%d].wants[%d]" % (i, j), w
        for j, b in enumerate(p.get("blocked_by", []) or []):
            if b.get("text"):
                yield "personas[%d].blocked_by[%d].text" % (i, j), b["text"]
    for i, f in enumerate(data.get("funnels", []) or []):
        if f.get("note"):
            yield "funnels[%d].note" % i, f["note"]
    for i, p in enumerate(data.get("pages", []) or []):
        if p.get("plain"):
            yield "pages[%d].plain" % i, p["plain"]
        for j, s in enumerate(p.get("sections", []) or []):
            for key in ("t", "d"):
                if s.get(key):
                    yield "pages[%d].sections[%d].%s" % (i, j, key), s[key]


COLLECTORS = {"findings.json": findings_fields, "ia.json": ia_fields}


def collector_for(data, name):
    """Pick by content, not filename - a file called findings-draft.json is
    still a findings file, and silently scanning nothing is the worst outcome
    for a check like this."""
    if "slides" in data:
        return findings_fields
    if "personas" in data or "pages" in data:
        return ia_fields
    return COLLECTORS.get(name)


# ---------------------------------------------------------------- scan
def scan_field(text, terms):
    """Returns {group: [term, ...]} of distinct hits, quoted text excluded."""
    clean = strip_quoted(normalise(text))
    hits = {}
    for group, pairs in terms.items():
        found = []
        for pat, term in pairs:
            if pat.search(clean) and term not in found:
                found.append(term)
        if found:
            hits[group] = found
    return hits


def scan_file(path, collector, terms):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    name = Path(path).name
    collector = collector or collector_for(data, name)
    if collector is None:
        print("check_prose_standalone.py: %s is neither a findings file nor an ia file." % name,
              file=sys.stderr)
        sys.exit(2)
    errors, warnings, scanned, words = [], [], 0, 0

    for where, text in collector(data):
        scanned += 1
        words += len(str(text).split())
        hits = scan_field(text, terms)
        for group, found in hits.items():
            listed = ", ".join('"%s"' % t for t in found)
            line = "%s: %s - %s (%s)" % (name, where, listed, LABELS[group])
            if group in ERROR_GROUPS:
                errors.append(line)
            elif group == TIER2 and len(found) >= TIER2_CLUSTER:
                errors.append(line)
            elif group == TIER3 and len(found) >= TIER3_CLUSTER:
                warnings.append(line)

    return errors, warnings, scanned, words


def main():
    ap = argparse.ArgumentParser(
        description="flag AI-writing patterns in a project's client-facing prose")
    ap.add_argument("--project", default="", help="project folder (contract §1)")
    ap.add_argument("--file", default="", help="a single findings.json or ia.json")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    a = ap.parse_args()

    terms = load_terms()
    targets = []
    if a.file:
        targets.append((Path(a.file), None))   # sniffed from content
    elif a.project:
        for name, collector in COLLECTORS.items():
            p = Path(a.project) / name
            if p.exists():
                targets.append((p, collector))
    else:
        ap.error("give either --project or --file")

    if not targets:
        print("check_prose_standalone.py: nothing to check - no findings.json or ia.json in %s"
              % a.project, file=sys.stderr)
        sys.exit(1)

    errors, warnings, scanned, words = [], [], 0, 0
    for path, collector in targets:
        e, w, s, n = scan_file(path, collector, terms)
        errors += e
        warnings += w
        scanned += s
        words += n

    for w in warnings:
        print("  warning: " + w, file=sys.stderr)
    if errors:
        print("check_prose_standalone.py: %d problem%s in %d field%s of client-facing prose."
              % (len(errors), "" if len(errors) == 1 else "s",
                 scanned, "" if scanned == 1 else "s"), file=sys.stderr)
        for e in errors:
            print("  " + e, file=sys.stderr)
        print("\nRewrite these. Text "
              "inside double quotes is already exempt, so if one of these is the "
              "client's own copy, quote it.", file=sys.stderr)
        sys.exit(1)
    if warnings and a.strict:
        print("check_prose_standalone.py: %d warning%s, and --strict was set."
              % (len(warnings), "" if len(warnings) == 1 else "s"), file=sys.stderr)
        sys.exit(1)

    print(json.dumps({
        "checked": [str(p) for p, _ in targets],
        "fields": scanned,
        "words": words,
        "errors": 0,
        "warnings": len(warnings),
    }, indent=2))


if __name__ == "__main__":
    main()
