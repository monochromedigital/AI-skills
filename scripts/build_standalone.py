#!/usr/bin/env python3
"""
build_standalone.py - Generates scripts/check_prose_standalone.py.

The checker inside each skill reads its word lists from
`assets/ai-writing.json`, so there is one place to edit them. That is the right
design inside a skill and useless outside one: you cannot drag a two-file
checker into a chat.

This bakes the lists into a single file that runs anywhere - any Cowork
session, any machine with Python, against any findings.json or ia.json, with
nothing else installed. The output is generated, never hand-edited. Add a word
to `assets/ai-writing.json` and re-run this; editing the standalone directly
puts the two out of step, which is the exact failure the JSON was meant to
prevent.

It also enforces the invariant the project contract relies on: the files that
are supposed to be byte-identical across skills actually are.

Usage:
  python3 scripts/build_standalone.py            # regenerate
  python3 scripts/build_standalone.py --check    # fail if the committed file is stale
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
OUT = REPO / "scripts" / "check_prose_standalone.py"

SOURCE_SKILL = "website-assessment"
CHECKER = "scripts/check_prose.py"
WORDS = "assets/ai-writing.json"

# Files the project contract requires to be identical wherever they appear.
SHARED = [
    "assets/ai-writing.json",
    "assets/brand.json",
    "scripts/brandkit.py",
    "scripts/check_prose.py",
    "scripts/render_report.py",
    "references/ai-writing.md",
    "references/project-contract.md",
]

# Directory trees under the same rule. The agency overlays decide what a
# document looks like, so a palette edited in one skill and not the other is
# how an audit and its board end up branded as different agencies.
SHARED_TREES = ["assets/brands"]

# The other half of the rule (contract §2b). Byte-identity catches copies that
# have already drifted; this catches the arrangement that makes drift certain -
# a per-deliverable value living in a file every skill has to carry.
#
# `footer_right` is here because it was the one that broke. It sat in all four
# agency overlays, in both skills, holding the same string in all eight - and
# the day one was edited, the byte-identity check failed while pointing at the
# wrong fix: syncing the copies would have labelled a sitemap as an audit. The
# label belongs to the skill (build_data.py's DELIVERABLE), not to an agency,
# and putting it back in a brand file should fail immediately rather than on
# whichever later commit happens to touch one copy.
BRAND_FILES = ["assets/brand.json", "assets/brands/*/brand.json"]
FORBIDDEN_BRAND_KEYS = {
    "footer_right": "the deliverable's name - one DELIVERABLE constant per "
                    "skill, not four copies per agency",
}

ANCHOR_ROOT = 'ROOT = Path(__file__).resolve().parent.parent\nWORDS_FILE = ROOT / "assets" / "ai-writing.json"'
ANCHOR_LOAD = re.compile(
    r'def load_terms\(\):\n(?:.*\n)*?    return \{g: compile_terms\(data\[g\]\) '
    r'for g in data if not g\.startswith\("_"\)\}')

HEADER = '''# ---------------------------------------------------------------------------
# GENERATED FILE - do not edit.
#
# Built from skills/{skill}/{checker}
#          and skills/{skill}/{words}
# Source digest: {digest}
#
# To change the word lists, edit assets/ai-writing.json in the skills and run
#     python3 scripts/build_standalone.py
# ---------------------------------------------------------------------------
'''


def tree_digest(root):
    """One hash over a directory's relative paths and contents."""
    h = hashlib.sha256()
    for f in sorted(p for p in root.rglob("*") if p.is_file()):
        h.update(str(f.relative_to(root)).encode("utf-8"))
        h.update(b"\0")
        h.update(f.read_bytes())
    return h.hexdigest()


def check_shared():
    """Every skill carrying one of the shared files must carry the same bytes."""
    problems = []
    skill_dirs = sorted(p for p in SKILLS.iterdir() if p.is_dir())

    def compare(rel, digests):
        if len(set(digests.values())) > 1:
            problems.append("%s differs across skills: %s" % (
                rel, ", ".join("%s=%s" % (k, v[:8]) for k, v in sorted(digests.items()))))

    for rel in SHARED:
        copies = {}
        for skill_dir in skill_dirs:
            f = skill_dir / rel
            if f.exists():
                copies[skill_dir.name] = hashlib.sha256(f.read_bytes()).hexdigest()
        compare(rel, copies)

    for rel in SHARED_TREES:
        copies = {}
        for skill_dir in skill_dirs:
            d = skill_dir / rel
            if d.is_dir():
                copies[skill_dir.name] = tree_digest(d)
        compare(rel + "/", copies)

    for skill_dir in skill_dirs:
        for pattern in BRAND_FILES:
            for f in sorted(skill_dir.glob(pattern)):
                try:
                    agency = json.loads(f.read_text(encoding="utf-8")).get("agency") or {}
                except ValueError as e:
                    problems.append("%s is not valid JSON: %s"
                                    % (f.relative_to(SKILLS), e))
                    continue
                for key, why in sorted(FORBIDDEN_BRAND_KEYS.items()):
                    if key in agency:
                        problems.append(
                            "%s carries agency.%s, which is %s (contract §2b)"
                            % (f.relative_to(SKILLS), key, why))

    return problems


def generate():
    src_dir = SKILLS / SOURCE_SKILL
    checker = (src_dir / CHECKER).read_text(encoding="utf-8")
    words = (src_dir / WORDS).read_text(encoding="utf-8").strip()

    if ANCHOR_ROOT not in checker:
        sys.exit("build_standalone.py: could not find the word-file lookup in %s.\n"
                 "The checker changed shape - update ANCHOR_ROOT rather than letting "
                 "this emit a file that silently reads nothing." % CHECKER)
    if not ANCHOR_LOAD.search(checker):
        sys.exit("build_standalone.py: could not find load_terms() in %s. "
                 "Update ANCHOR_LOAD." % CHECKER)

    if '"""' in words:
        sys.exit("build_standalone.py: the word list contains a triple quote, which "
                 "would break the embedded literal. Remove it from ai-writing.json.")

    body = checker.replace(ANCHOR_ROOT, 'WORDS = json.loads(r"""\n%s\n""")' % words)
    body = ANCHOR_LOAD.sub(
        "def load_terms():\n    return {g: compile_terms(WORDS[g]) "
        "for g in WORDS if not g.startswith(\"_\")}", body)

    # Docstring rewrites. Matched on wrapped whitespace so reflowing a paragraph
    # in the source does not silently skip one - a standalone that still tells
    # the reader to go find assets/ai-writing.json is worse than no docstring.
    for pattern, replacement, what in (
        (r"check_prose\.py - Scans", "check_prose_standalone.py - Scans", "title"),
        (r"This is the mechanical half of the rule:.*?before it reaches anyone\.",
         "This is the portable copy: the word lists are embedded, so it runs in\n"
         "any session, or on any machine with Python, against any findings.json\n"
         "or ia.json, and needs nothing else on disk.", "provenance paragraph"),
        (r"See references/ai-writing\.md - and note that text ", "Text ", "error footer"),
        (r"python3 check_prose\.py ", "python3 check_prose_standalone.py ", "usage lines"),
        # Runtime messages name the program. A standalone that reports itself as
        # check_prose.py sends people looking for a file they do not have.
        (r'"check_prose\.py: ', '"check_prose_standalone.py: ', "runtime messages"),
    ):
        body, n = re.subn(pattern, replacement, body, flags=re.DOTALL)
        if not n:
            sys.exit("build_standalone.py: the %s no longer matches. Fix the pattern "
                     "rather than shipping a standalone that documents itself wrongly."
                     % what)

    digest = hashlib.sha256((checker + words).encode("utf-8")).hexdigest()[:16]
    header = HEADER.format(skill=SOURCE_SKILL, checker=CHECKER, words=WORDS, digest=digest)

    # header goes after the shebang and module docstring, before the imports
    marker = '"""\n\nimport argparse'
    if marker not in body:
        sys.exit("build_standalone.py: could not place the generated-file header.")
    return body.replace(marker, '"""\n\n' + header + '\nimport argparse')


def main():
    ap = argparse.ArgumentParser(description="generate the portable prose checker")
    ap.add_argument("--check", action="store_true",
                    help="verify the committed file is current; write nothing")
    a = ap.parse_args()

    problems = check_shared()
    if problems:
        print("build_standalone.py: the shared-file rules do not hold "
              "(project contract §2b).", file=sys.stderr)
        for p in problems:
            print("  " + p, file=sys.stderr)
        print("\nA shared file must be byte-identical in every skill that carries "
              "it, and must hold nothing that varies per skill.\n"
              "Before syncing one copy over the other, check that both skills "
              "really do want the same bytes. A value that differs per "
              "deliverable belongs in that skill's own code, not in a shared "
              "file - syncing it is how a sitemap ends up labelled as an audit.",
              file=sys.stderr)
        sys.exit(1)

    built = generate()

    if a.check:
        if not OUT.exists():
            sys.exit("build_standalone.py: %s does not exist. Run without --check."
                     % OUT.relative_to(REPO))
        if OUT.read_text(encoding="utf-8") != built:
            sys.exit("build_standalone.py: %s is stale. Run "
                     "`python3 scripts/build_standalone.py`." % OUT.relative_to(REPO))
        print("%s is current" % OUT.relative_to(REPO))
        return

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(built, encoding="utf-8")
    OUT.chmod(0o755)
    print("%s (%d bytes)" % (OUT.relative_to(REPO), len(built)))


if __name__ == "__main__":
    main()
