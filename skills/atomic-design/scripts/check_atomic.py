#!/usr/bin/env python3
"""
check_atomic.py - Checks a front-end codebase against the two laws in SKILL.md:
nothing is hardcoded, and nothing repeats.

The rules an atomic codebase runs on are mostly mechanical - a hex value in a
component, a card block pasted into three routes, an atom importing a feature -
and mechanical rules should be checked mechanically rather than by whoever is
reading the diff that day. This script is the half that can be automated. The
judgement half lives in `references/audit.md`.

It is read-only. It reports; it never edits. Fixes are proposed to the user and
applied after they approve, because a layer move rewrites import paths across a
repo and that is not a change to make quietly.

Layer patterns come from `atomic.config.json` at the project root when present,
and from built-in defaults otherwise. Files matching no pattern are `unknown`:
still checked for hardcoded values and duplication, exempt from layer rules, so
a partial mapping is useful immediately.

Checks (error):
  hardcoded-color       #hex, rgb(), hsl() outside the token layer
  hardcoded-dimension   raw px/rem in inline styles and style objects
  arbitrary-utility     Tailwind escape hatches - w-[327px], text-[#fff]
  duplicate-markup      the same block of markup twice - the Rule of Two
  layer-violation       an import pointing upward, or across features
  vendor-import         a vendor UI package imported outside components/ui
  logic-in-component    fetch/store/router hooks below the page layer
  hardcoded-url         literal http(s):// outside config
  hardcoded-copy        user-facing text baked into a ui/ or feature component

Checks (warning - these need judgement, and the script says so):
  oversized-component   a file past maxComponentLines
  magic-number          unexplained numeric literals outside a constants file

Usage:
  python3 check_atomic.py <path>
  python3 check_atomic.py <path> --json
  python3 check_atomic.py <path> --strict
  python3 check_atomic.py <path> --only hardcoded-color,duplicate-markup
  python3 check_atomic.py --detect <path>
"""

import argparse
import bisect
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

DEFAULT_CONFIG = {
    "root": "src",
    "layers": {
        "tokens": [
            "**/tokens/**", "**/theme/**", "**/design-tokens/**",
            "tailwind.config.*", "**/tailwind.config.*",
            "**/tokens.css", "**/theme.css", "**/variables.css",
            "**/*.css.ts",
        ],
        "ui": ["**/components/ui/**", "**/components/common/**", "**/ui/**"],
        "layout": ["**/components/layout/**", "**/components/shared/**", "**/layout/**"],
        "feature": ["**/features/*/**", "**/modules/*/**", "**/domains/*/**"],
        "page": [
            "app/**", "src/app/**", "pages/**", "src/pages/**",
            "**/views/**", "**/screens/**", "**/routes/**",
        ],
    },
    "maxComponentLines": 150,
    "duplicateMinLines": 4,
    "allowLiterals": [0, 1, -1, 2, 100, 1000, 12, 24, 60],
    "disable": [],
    "ignore": [
        "**/node_modules/**", "**/.git/**", "**/dist/**", "**/build/**",
        "**/.next/**", "**/out/**", "**/coverage/**", "**/.turbo/**",
        "**/*.test.*", "**/*.spec.*", "**/*.stories.*", "**/*.d.ts",
        "**/*.min.*", "**/__snapshots__/**", "**/__mocks__/**",
    ],
}

LAYER_RANK = {"tokens": 0, "ui": 1, "layout": 2, "feature": 3, "page": 4}

SOURCE_EXT = {
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".vue", ".svelte", ".astro",
    ".css", ".scss", ".sass", ".less",
}
SCRIPT_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte", ".astro"}
STYLE_EXT = {".css", ".scss", ".sass", ".less"}

SKIP_DIRS = {
    "node_modules", ".git", "dist", "build", ".next", "out", "coverage",
    ".turbo", ".cache", "__pycache__", "vendor", ".venv", "public",
}

VENDOR_UI_PACKAGES = (
    "@mui/", "@material-ui/", "@chakra-ui/", "@mantine/", "@radix-ui/",
    "antd", "@ant-design/", "react-bootstrap", "@nextui-org/", "@heroui/",
    "@headlessui/", "primereact", "@fluentui/", "semantic-ui-react",
    "@blueprintjs/", "rsuite", "@arco-design/",
)

# Data / state / routing that must not appear below the page layer.
LOGIC_PATTERN = re.compile(
    r"\b(?:useSelector|useDispatch|useStore|useQuery|useMutation|useInfiniteQuery"
    r"|useSWR|useSWRMutation|useRouter|usePathname|useSearchParams|useNavigate"
    r"|useParams|useSession|useAuth|useLoaderData|getServerSideProps"
    r"|createClient)\b|\bfetch\s*\(|\baxios\s*[.(]|\bsupabase\s*\.|\bprisma\s*\."
)

URL_ALLOW = ("w3.org", "schema.org", "json-schema.org", "purl.org", "xmlns")

COPY_PROPS = re.compile(
    r"""\b(?:label|title|placeholder|alt|aria-label|ariaLabel|heading|subheading
        |description|cta|ctaLabel|buttonText|emptyText|errorText|helperText
        |tooltip|caption)\s*=\s*(["'])(.*?)\1""",
    re.VERBOSE,
)
JSX_TEXT = re.compile(r">\s*([A-Za-z][A-Za-z0-9 ,.'!?&:%()\-]{2,}?)\s*<")

STYLE_PROP = re.compile(
    r"""\b(?:padding|paddingTop|paddingBottom|paddingLeft|paddingRight
        |margin|marginTop|marginBottom|marginLeft|marginRight
        |gap|rowGap|columnGap|width|height|minWidth|maxWidth|minHeight|maxHeight
        |top|left|right|bottom|fontSize|font-size|lineHeight|line-height
        |letterSpacing|letter-spacing|borderRadius|border-radius|borderWidth
        |padding-top|padding-bottom|padding-left|padding-right
        |margin-top|margin-bottom|margin-left|margin-right)
        \s*:\s*['"]?\s*(-?\d+(?:\.\d+)?)(px|rem|em)?""",
    re.VERBOSE,
)
ARBITRARY_UTILITY = re.compile(r"(?<![\w\]])([a-z][a-z0-9]*(?:-[a-z0-9]+)*)-\[([^\]\s]+)\]")
ARBITRARY_VALUE = re.compile(
    r"^(?:-?\d*\.?\d+(?:px|rem|em|%|vh|vw|ch|fr|s|ms|deg|pt)?"
    r"|#[0-9a-fA-F]{3,8}"
    r"|(?:rgb|rgba|hsl|hsla)\(.*\))$"
)
HEX = re.compile(r"#([0-9a-fA-F]{3,8})\b")
COLOR_FN = re.compile(r"\b(rgba?|hsla?)\s*\(([^)]*)\)")
URL = re.compile(r"https?://[^\s'\"`<>)\\]+")
IMPORT = re.compile(
    r"""(?:^|\s)(?:import|export)\s+(?:[^'"]*?\sfrom\s+)?['"]([^'"]+)['"]"""
    r"""|\brequire\s*\(\s*['"]([^'"]+)['"]\s*\)"""
    r"""|\bimport\s*\(\s*['"]([^'"]+)['"]\s*\)""",
    re.MULTILINE,
)
NUMBER = re.compile(r"(?<![\w.#$-])(\d+(?:\.\d+)?)(?![\w.%]|px|rem|em)")

NOISE_LINE = re.compile(r"^[\s{}()\[\];,]*$|^(?:import|export)\b|^</?>$")


# --------------------------------------------------------------------------
# Source scanning
# --------------------------------------------------------------------------

def mask_source(src):
    """Blank out comment bodies, preserving offsets, and record string spans.

    Character offsets are preserved so line numbers taken from the masked text
    are correct against the original. String *contents* are kept - a hex value
    inside a string is still a hardcoded hex - but their spans are returned so
    checks that should not fire inside a string (magic numbers, mostly) can
    skip them.

    A single quote only opens a string when the previous significant character
    can start an expression. Without that, the apostrophe in `<p>it's fine</p>`
    swallows the rest of the file.

    A `${...}` interpolation is code rather than string, and is scanned as code,
    tracking brace depth so the interpolation's own braces do not end it early.
    Without that, the template literal an interpolation so often contains has its
    opening backtick read as the closing one, and every span from there is
    inverted - markup scanned as code, code scanned as string - until the
    backticks happen to rebalance.
    """
    out = list(src)
    spans = []
    i, n = 0, len(src)
    state = None
    start = 0
    prev = ""
    tmpl = []

    while i < n:
        c = src[i]
        if state is None:
            if c == "/" and i + 1 < n and src[i + 1] == "/":
                out[i] = out[i + 1] = " "
                state = "line"
                i += 2
                continue
            if c == "/" and i + 1 < n and src[i + 1] == "*":
                out[i] = out[i + 1] = " "
                state = "block"
                i += 2
                continue
            if tmpl:
                if c == "{":
                    tmpl[-1] += 1
                elif c == "}":
                    if tmpl[-1]:
                        tmpl[-1] -= 1
                    else:
                        tmpl.pop()
                        state, start = "`", i + 1
                        prev = c
                        i += 1
                        continue
            if c == "'" and (prev == "" or not (prev.isalnum() or prev in "._)]")):
                state, start = c, i + 1
            elif c in '"`':
                state, start = c, i + 1
            if not c.isspace():
                prev = c
            i += 1
            continue

        if state == "line":
            if c == "\n":
                state = None
            else:
                out[i] = " "
            i += 1
            continue

        if state == "block":
            if c == "*" and i + 1 < n and src[i + 1] == "/":
                out[i] = out[i + 1] = " "
                state = None
                i += 2
                continue
            if c != "\n":
                out[i] = " "
            i += 1
            continue

        # inside a string literal
        if c == "\\":
            i += 2
            continue
        if state == "`" and c == "$" and src[i + 1 : i + 2] == "{":
            spans.append((start, i))
            tmpl.append(0)
            state = None
            i += 2
            continue
        if c == state or (c == "\n" and state in "'\""):
            spans.append((start, i))
            state = None
            prev = c
            i += 1
            continue
        i += 1

    if state in ("'", '"', "`"):
        spans.append((start, n))
    return "".join(out), spans


class SourceFile:
    def __init__(self, path, rel, layer, group, text):
        self.path = path
        self.rel = rel
        self.layer = layer
        self.group = group          # feature name, for cross-feature checks
        self.text = text
        self.masked, self.spans = mask_source(text)
        self.line_starts = [0]
        for m in re.finditer(r"\n", text):
            self.line_starts.append(m.end())
        self.lines = text.splitlines()
        self.ext = Path(path).suffix

    def line_of(self, pos):
        return bisect.bisect_right(self.line_starts, pos)

    def snippet(self, pos, width=90):
        line = self.lines[self.line_of(pos) - 1] if self.lines else ""
        return line.strip()[:width]

    def in_string(self, pos):
        for a, b in self.spans:
            if a <= pos < b:
                return True
            if a > pos:
                break
        return False


# --------------------------------------------------------------------------
# Globs and layers
# --------------------------------------------------------------------------

def glob_to_regex(pattern):
    """Translate a glob to a regex, capturing each single-`*` path segment.

    The capture is what makes cross-feature detection work: `src/features/*/**`
    against `src/features/checkout/Form.tsx` yields `checkout`, and two feature
    files with different captures are importing across a boundary.
    """
    out, groups, i, n = ["^"], 0, 0, len(pattern)
    while i < n:
        if pattern.startswith("/**/", i):
            out.append("/(?:.*/)?")
            i += 4
        elif pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("/**", i):
            out.append("(?:/.*)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("([^/]*)")
            groups += 1
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    out.append("$")
    return re.compile("".join(out)), groups


class LayerMap:
    def __init__(self, layers):
        self.compiled = {
            name: [glob_to_regex(p) for p in patterns]
            for name, patterns in layers.items()
        }

    def classify(self, rel):
        """Return (layer, group). Most specific rank wins on a tie."""
        best = (None, None, -1)
        for name, regexes in self.compiled.items():
            rank = LAYER_RANK.get(name, -1)
            for rx, ngroups in regexes:
                m = rx.match(rel)
                if m:
                    group = next((g for g in m.groups() if g), None) if ngroups else None
                    # A deeper (higher-rank) match is more specific: a file under
                    # features/x/components/ui/ is still feature-owned.
                    if rank > best[2]:
                        best = (name, group, rank)
        return (best[0], best[1]) if best[0] else ("unknown", None)


def matches_any(rel, regexes):
    return any(rx.match(rel) for rx, _ in regexes)


# --------------------------------------------------------------------------
# Stack detection
# --------------------------------------------------------------------------

FRAMEWORKS = [
    ("next", "Next.js"), ("nuxt", "Nuxt"), ("@sveltejs/kit", "SvelteKit"),
    ("expo", "Expo / React Native"), ("react-native", "React Native"),
    ("@angular/core", "Angular"), ("svelte", "Svelte"), ("vue", "Vue"),
    ("react", "React"),
]
STYLING = [
    ("tailwindcss", "Tailwind"), ("@vanilla-extract/css", "vanilla-extract"),
    ("styled-components", "styled-components"), ("@emotion/react", "Emotion"),
    ("@stitches/react", "Stitches"), ("sass", "Sass"), ("less", "Less"),
]


def detect_stack(root):
    root = Path(root)
    info = {"framework": None, "styling": None, "ui_library": None,
            "vendored_ui": False, "token_files": [], "notes": []}

    pkg_path = root / "package.json"
    deps = {}
    if pkg_path.exists():
        try:
            pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        except (json.JSONDecodeError, OSError):
            info["notes"].append("package.json present but unreadable")
    else:
        info["notes"].append("no package.json at this path")

    info["framework"] = next((label for key, label in FRAMEWORKS if key in deps), None)
    info["styling"] = next((label for key, label in STYLING if key in deps), None)
    info["ui_library"] = next(
        (d for d in deps if any(d.startswith(v) or d == v.rstrip("/")
                                for v in VENDOR_UI_PACKAGES)), None)

    if (root / "components.json").exists():
        info["vendored_ui"] = True
        info["notes"].append("shadcn/ui detected - vendored files ARE the atom layer, retoken them rather than wrapping")
    if info["ui_library"]:
        info["notes"].append(f"{info['ui_library']} ships from node_modules - wrap it in components/ui")

    for name in ("tailwind.config.ts", "tailwind.config.js", "tailwind.config.mjs",
                 "tailwind.config.cjs"):
        if (root / name).exists():
            info["token_files"].append(name)
    for pattern in ("**/tokens.css", "**/theme.ts", "**/tokens.ts",
                    "**/globals.css", "**/variables.css", "**/*.css.ts"):
        for hit in list(root.glob(pattern))[:4]:
            if not any(part in SKIP_DIRS for part in hit.parts):
                info["token_files"].append(str(hit.relative_to(root)))

    info["token_files"] = sorted(set(info["token_files"]))
    if len(info["token_files"]) > 1:
        info["notes"].append("more than one candidate token file - confirm which is the single source before adding tokens")
    if not info["token_files"]:
        info["notes"].append("no token layer found - create one before writing components")
    return info


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------

def finding(check, severity, sf, pos, message, detail=""):
    return {
        "check": check,
        "severity": severity,
        "file": sf.rel,
        "line": sf.line_of(pos),
        "layer": sf.layer,
        "message": message,
        "detail": detail or sf.snippet(pos),
    }


def check_colors(sf, cfg, out):
    if sf.layer == "tokens":
        return
    for m in HEX.finditer(sf.masked):
        if len(m.group(1)) in (3, 4, 6, 8):
            out.append(finding("hardcoded-color", "error", sf, m.start(),
                               f"colour literal `{m.group(0)}` - use a token"))
    for m in COLOR_FN.finditer(sf.masked):
        inner = m.group(2)
        if "var(" in inner or "--" in inner or "$" in inner:
            continue
        out.append(finding("hardcoded-color", "error", sf, m.start(),
                           f"colour literal `{m.group(1)}(...)` - use a token"))


def check_dimensions(sf, cfg, out):
    if sf.layer == "tokens":
        return
    for m in STYLE_PROP.finditer(sf.masked):
        value, unit = m.group(1), m.group(2)
        if float(value) == 0:
            continue
        line = sf.lines[sf.line_of(m.start()) - 1] if sf.lines else ""
        if any(t in line for t in ("var(", "theme.", "tokens.", "vars.", "$", "token(")):
            continue
        if sf.ext in SCRIPT_EXT and unit is None and float(value) < 3:
            continue  # flex: 1, zIndex: 2 and friends
        out.append(finding("hardcoded-dimension", "error", sf, m.start(),
                           f"raw dimension `{m.group(0).strip()}` - use a spacing/size token"))


def check_arbitrary(sf, cfg, out):
    if sf.layer == "tokens" or sf.ext in STYLE_EXT:
        return
    for m in ARBITRARY_UTILITY.finditer(sf.masked):
        value = m.group(2)
        if value.startswith(("var(", "--", "theme(", "calc(")):
            continue
        if not ARBITRARY_VALUE.match(value):
            continue  # an arbitrary *variant* like data-[state=open], not a value
        out.append(finding("arbitrary-utility", "error", sf, m.start(),
                           f"arbitrary value `{m.group(0)}` - add a token and use the named utility"))


def check_urls(sf, cfg, out):
    if sf.layer == "tokens":
        return
    if any(t in sf.rel.lower() for t in ("config", "constant", ".env", "env.", "manifest", "sitemap", "robots")):
        return
    for m in URL.finditer(sf.masked):
        if any(a in m.group(0) for a in URL_ALLOW):
            continue
        out.append(finding("hardcoded-url", "error", sf, m.start(),
                           f"literal URL `{m.group(0)[:60]}` - move to config or env"))


def check_copy(sf, cfg, out):
    if sf.layer not in ("ui", "layout", "feature") or sf.ext not in SCRIPT_EXT:
        return
    seen = set()
    for m in COPY_PROPS.finditer(sf.masked):
        text = m.group(2).strip()
        if not text or "{" in text or len(text) < 3 or not re.search(r"[A-Za-z]{2}", text):
            continue
        key = (sf.line_of(m.start()), text)
        if key in seen:
            continue
        seen.add(key)
        out.append(finding("hardcoded-copy", "error", sf, m.start(),
                           f'copy baked into a {sf.layer} component: "{text[:50]}" - pass it in as a prop'))
    for m in JSX_TEXT.finditer(sf.masked):
        text = m.group(1).strip()
        if len(text) < 3 or not re.search(r"[A-Za-z]{2}", text):
            continue
        if "&&" in text or "||" in text:
            continue  # a comparison in code, not a text node
        if text.isupper() and " " not in text:
            continue  # enum-ish
        key = (sf.line_of(m.start()), text)
        if key in seen:
            continue
        seen.add(key)
        out.append(finding("hardcoded-copy", "error", sf, m.start(),
                           f'copy baked into a {sf.layer} component: "{text[:50]}" - pass it in as a prop'))


def check_logic(sf, cfg, out):
    if sf.layer not in ("ui", "layout") or sf.ext not in SCRIPT_EXT:
        return
    seen = set()
    for m in LOGIC_PATTERN.finditer(sf.masked):
        token = m.group(0).strip("( .")
        if token in seen:
            continue
        seen.add(token)
        out.append(finding("logic-in-component", "error", sf, m.start(),
                           f"`{token}` in a {sf.layer} component - data, state and routing belong to the page layer; take it as a prop"))


def check_oversized(sf, cfg, out):
    if sf.ext not in SCRIPT_EXT or sf.layer == "tokens":
        return
    limit = cfg["maxComponentLines"]
    if len(sf.lines) > limit:
        out.append(finding("oversized-component", "warning", sf, 0,
                           f"{len(sf.lines)} lines (limit {limit}) - likely an organism that never got split",
                           detail=f"{len(sf.lines)} lines"))


def check_magic_numbers(sf, cfg, out):
    if sf.ext not in SCRIPT_EXT or sf.layer == "tokens":
        return
    if any(t in sf.rel.lower() for t in ("config", "constant", "theme", "token")):
        return
    allowed = set(cfg["allowLiterals"])
    flagged_lines = {f["line"] for f in out if f["file"] == sf.rel}
    hits, count = [], 0
    for m in NUMBER.finditer(sf.masked):
        raw = m.group(1)
        if "." in raw:
            continue
        value = int(raw)
        if value < 10 or value in allowed:
            continue
        line_no = sf.line_of(m.start())
        if line_no in flagged_lines:
            continue
        if sf.in_string(m.start()):
            continue
        before = sf.masked[m.start() - 1] if m.start() else ""
        after = sf.masked[m.end():m.end() + 1]
        if before == "[" and after == "]":
            continue  # array subscript, not a rule
        hits.append((m.start(), value))
        count += 1
        if count >= 10:
            break
    for pos, value in hits:
        out.append(finding("magic-number", "warning", sf, pos,
                           f"unexplained literal `{value}` - name it in a constants module if it is a rule"))


def check_imports(sf, cfg, layer_map, root, out):
    if sf.ext not in SCRIPT_EXT:
        return
    rank = LAYER_RANK.get(sf.layer)
    for m in IMPORT.finditer(sf.masked):
        idx = next((i for i in (1, 2, 3) if m.group(i)), None)
        if idx is None:
            continue
        spec, pos = m.group(idx), m.start(idx)

        if not spec.startswith((".", "/", "@/", "~/", "$lib/")):
            if any(spec == v.rstrip("/") or spec.startswith(v) for v in VENDOR_UI_PACKAGES):
                if sf.layer not in ("ui", "tokens"):
                    out.append(finding("vendor-import", "error", sf, pos,
                                       f"`{spec}` imported in a {sf.layer} file - wrap it as an atom in components/ui and import that"))
            continue

        if sf.layer == "unknown":
            continue  # unmapped files are exempt from layer rules, by design
        target = resolve_import(spec, sf, root, cfg)
        if target is None:
            continue
        t_layer, t_group = layer_map.classify(target)
        t_rank = LAYER_RANK.get(t_layer)

        if t_layer == "page" and sf.layer != "page":
            out.append(finding("layer-violation", "error", sf, pos,
                               f"`{spec}` is page-layer - nothing may import a page"))
            continue
        if rank is None or t_rank is None:
            continue
        if t_rank > rank:
            out.append(finding("layer-violation", "error", sf, pos,
                               f"{sf.layer} importing {t_layer} (`{spec}`) - imports point downward only; move the shared piece down or take it as a prop"))
        elif (sf.layer == "feature" and t_layer == "feature"
              and sf.group and t_group and sf.group != t_group):
            out.append(finding("layer-violation", "error", sf, pos,
                               f"feature `{sf.group}` importing feature `{t_group}` (`{spec}`) - move the shared piece down to ui/ or layout/"))


def resolve_import(spec, sf, root, cfg):
    """Map an import specifier to a repo-relative path, or None if unresolvable."""
    if spec.startswith("."):
        base = (Path(sf.path).parent / spec).resolve()
        try:
            return base.relative_to(root).as_posix()
        except ValueError:
            return None
    src_root = cfg.get("root") or ""
    if spec.startswith(("@/", "~/")):
        rest = spec[2:]
    elif spec.startswith("$lib/"):
        rest = "lib/" + spec[5:]
    elif spec.startswith("/"):
        rest = spec[1:]
    else:
        return None
    candidate = f"{src_root}/{rest}" if src_root else rest
    return candidate.lstrip("/")


# --------------------------------------------------------------------------
# Duplicate markup - the Rule of Two
# --------------------------------------------------------------------------

def normalise(line):
    return re.sub(r"\s+", " ", line.strip())


def check_duplicates(files, cfg, out):
    """Hash sliding windows of normalised markup lines and report repeats.

    Normalising means a block that was reindented or reformatted when it was
    pasted still matches. It cannot tell a real duplicate from two blocks that
    merely resemble each other - that call belongs in the audit report.
    """
    window = cfg["duplicateMinLines"]
    buckets = defaultdict(list)

    for sf in files:
        if sf.ext not in SCRIPT_EXT:
            continue
        kept = [(i + 1, normalise(l)) for i, l in enumerate(sf.lines)]
        kept = [(n, l) for n, l in kept if l and not NOISE_LINE.match(l)]
        for i in range(len(kept) - window + 1):
            chunk = kept[i:i + window]
            body = "\n".join(l for _, l in chunk)
            if body.count("<") < 2:
                continue  # markup only; a run of plain statements is not the target
            buckets[hash(body)].append((sf.rel, chunk[0][0], chunk[-1][0], body))

    groups = [g for g in buckets.values() if len({(f, s) for f, s, _, _ in g}) > 1]
    groups.sort(key=lambda g: (g[0][0], g[0][1]))

    # Consecutive windows over the same duplicated region each hash separately.
    # Merge them so a repeated 12-line block is one finding, not nine.
    covered = defaultdict(list)   # file -> list of mutable [start, end]

    def touching(f, s, e):
        return next((iv for iv in covered[f] if s <= iv[1] + 1 and e >= iv[0] - 1), None)

    reports = []
    for group in groups:
        locations = sorted({(f, s, e) for f, s, e, _ in group})
        existing = [touching(f, s, e) for f, s, e in locations]
        if all(iv is not None for iv in existing):
            for (f, s, e), iv in zip(locations, existing):
                iv[0], iv[1] = min(iv[0], s), max(iv[1], e)
            continue
        refs = []
        for (f, s, e), iv in zip(locations, existing):
            if iv is None:
                iv = [s, e]
                covered[f].append(iv)
            else:
                iv[0], iv[1] = min(iv[0], s), max(iv[1], e)
            refs.append((f, iv))
        reports.append(refs)

    for refs in reports:
        (first_file, first_iv) = refs[0]
        span = first_iv[1] - first_iv[0] + 1
        others = ", ".join(f"{f}:{iv[0]}-{iv[1]}" for f, iv in refs[1:])
        out.append({
            "check": "duplicate-markup",
            "severity": "error",
            "file": first_file,
            "line": first_iv[0],
            "layer": "",
            "message": f"{len(refs)} copies of the same {span}-line block - extract one component (Rule of Two)",
            "detail": f"also at {others}",
        })


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------

def load_config(root):
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    for candidate in [root] + list(root.parents)[:3]:
        path = candidate / "atomic.config.json"
        if path.exists():
            try:
                user = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                print(f"warning: {path} is unreadable ({exc}); using defaults", file=sys.stderr)
                break
            cfg.update({k: v for k, v in user.items() if k != "layers"})
            if "layers" in user:
                cfg["layers"] = user["layers"]
            cfg["_config_path"] = str(path)
            break
    return cfg


def collect_files(root, cfg, layer_map):
    ignore = [glob_to_regex(p) for p in cfg["ignore"]]
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            path = Path(dirpath) / name
            if path.suffix not in SOURCE_EXT:
                continue
            rel = path.relative_to(root).as_posix()
            if matches_any(rel, ignore):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            layer, group = layer_map.classify(rel)
            files.append(SourceFile(str(path.resolve()), rel, layer, group, text))
    return files


CHECKS = [
    "hardcoded-color", "hardcoded-dimension", "arbitrary-utility",
    "hardcoded-url", "hardcoded-copy", "logic-in-component",
    "layer-violation", "vendor-import", "duplicate-markup",
    "oversized-component", "magic-number",
]


def run(root, cfg, only=None):
    layer_map = LayerMap(cfg["layers"])
    files = collect_files(root, cfg, layer_map)
    enabled = set(only or CHECKS) - set(cfg.get("disable", []))
    findings = []

    per_file = [
        ("hardcoded-color", check_colors),
        ("hardcoded-dimension", check_dimensions),
        ("arbitrary-utility", check_arbitrary),
        ("hardcoded-url", check_urls),
        ("hardcoded-copy", check_copy),
        ("logic-in-component", check_logic),
        ("oversized-component", check_oversized),
    ]
    for sf in files:
        for name, fn in per_file:
            if name in enabled:
                fn(sf, cfg, findings)
        if "layer-violation" in enabled or "vendor-import" in enabled:
            before = len(findings)
            check_imports(sf, cfg, layer_map, Path(root).resolve(), findings)
            findings[before:] = [f for f in findings[before:] if f["check"] in enabled]
        if "magic-number" in enabled:
            check_magic_numbers(sf, cfg, findings)

    if "duplicate-markup" in enabled:
        check_duplicates(files, cfg, findings)

    findings.sort(key=lambda f: (f["severity"] != "error", f["check"], f["file"], f["line"]))
    return files, findings


def report(files, findings, cfg, root):
    errors = [f for f in findings if f["severity"] == "error"]
    warnings = [f for f in findings if f["severity"] == "warning"]

    print(f"\natomic-design check - {len(files)} files scanned in {root}")
    if cfg.get("_config_path"):
        print(f"config: {cfg['_config_path']}")
    else:
        print("config: built-in defaults (write atomic.config.json to map your folders)")

    unknown = sum(1 for f in files if f.layer == "unknown")
    if unknown:
        print(f"note: {unknown} files matched no layer pattern - exempt from layer rules")

    for label, group in (("ERRORS", errors), ("WARNINGS", warnings)):
        if not group:
            continue
        print(f"\n{label} ({len(group)})")
        by_check = defaultdict(list)
        for f in group:
            by_check[f["check"]].append(f)
        for check in sorted(by_check, key=lambda c: -len(by_check[c])):
            items = by_check[check]
            print(f"\n  {check} ({len(items)})")
            for f in items[:20]:
                print(f"    {f['file']}:{f['line']}  {f['message']}")
                if f["detail"] and f["detail"] != f["message"]:
                    print(f"      {f['detail'][:100]}")
            if len(items) > 20:
                print(f"    ... and {len(items) - 20} more")

    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    if not findings:
        print("clean.")
    elif warnings and not errors:
        print("warnings need judgement - see references/audit.md before acting on them.")


def main():
    ap = argparse.ArgumentParser(description="Check a codebase against atomic-design rules.")
    ap.add_argument("path", nargs="?", default=".", help="project root or subdirectory")
    ap.add_argument("--json", action="store_true", help="machine-readable findings")
    ap.add_argument("--strict", action="store_true", help="warnings fail the run too")
    ap.add_argument("--detect", metavar="PATH", help="report the detected stack and exit")
    ap.add_argument("--only", help="comma-separated check names")
    args = ap.parse_args()

    if args.detect:
        info = detect_stack(args.detect)
        if args.json:
            print(json.dumps(info, indent=2))
        else:
            print(f"\nstack detection - {args.detect}")
            print(f"  framework:   {info['framework'] or 'not identified'}")
            print(f"  styling:     {info['styling'] or 'plain CSS / not identified'}")
            print(f"  ui library:  {info['ui_library'] or 'none'}")
            print(f"  token files: {', '.join(info['token_files']) or 'none found'}")
            for note in info["notes"]:
                print(f"  - {note}")
            print("\nsee references/stacks.md for the matching token strategy")
        return 0

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"error: {root} does not exist", file=sys.stderr)
        return 2

    cfg = load_config(root)
    only = [c.strip() for c in args.only.split(",")] if args.only else None
    if only:
        unknown = [c for c in only if c not in CHECKS]
        if unknown:
            print(f"error: unknown check(s): {', '.join(unknown)}", file=sys.stderr)
            print(f"available: {', '.join(CHECKS)}", file=sys.stderr)
            return 2

    files, findings = run(root, cfg, only)

    if args.json:
        print(json.dumps({
            "root": str(root),
            "scanned": len(files),
            "stack": detect_stack(root),
            "counts": {
                "error": sum(1 for f in findings if f["severity"] == "error"),
                "warning": sum(1 for f in findings if f["severity"] == "warning"),
            },
            "findings": findings,
        }, indent=2))
    else:
        report(files, findings, cfg, root)

    if any(f["severity"] == "error" for f in findings):
        return 1
    if args.strict and findings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
