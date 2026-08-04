#!/usr/bin/env python3
"""
brandkit.py - Resolves which agency's branding a run wears.

Carried byte-identically by every skill that renders a document, for the same
reason `render_report.py` is: the moment two skills resolve branding
differently, the audit and the board start looking like two agencies.

The problem this solves: one operator, several agencies. A project belongs to
Crackwits or Monochrome or Daydream or ALL IN, and that choice has to survive
from the first skill that runs to the last, without being asked twice and
without being copied into every project folder.

Resolution order, first hit wins:

  1. an explicit --agency slug on the command line      (one-off override)
  2. project.json["brand"]  - a path to a brand file    (contract §2, retained)
  3. project.json["agency"] - an agency slug            (the normal path)
  4. nothing. It fails.

**There is no default agency.** Four agencies, none of them the house one, so
picking one when the project does not say would be a guess wearing the costume
of a decision - and the output would look completely finished while being
branded by the wrong company. The same reasoning already applies to a typo'd
slug; an absent field is not a weaker case, it is the same case.

Per-agency files are **overlays**, not replacements. `assets/brand.json` is the
base and belongs to nobody: categories, severity, layout and type live there
and are not duplicated four times. Its palette is a deliberate neutral grey, so
an incomplete agency file renders as visibly unbranded rather than as some
other agency's work. An agency file carries its name, its footers and its
palette. Deep-merged, so an agency that overrides one colour keeps the rest.

Category colours are deliberately awkward to override. The seven discipline
colours are functional encoding - a reader learns that orange means UX across
every report they are sent - and an agency that recolours them is making its
own documents harder to read. Nothing forbids it; it just has to be explicit
in the agency file rather than inherited by accident.

Logos live beside the agency file:

  assets/brands/<slug>/brand.json
  assets/brands/<slug>/logo.svg        on light backgrounds
  assets/brands/<slug>/logo-dark.svg   on dark backgrounds (the report header
                                       and every deck slide are dark)

Both are optional. A missing logo renders the wordmark as text, exactly as it
did before this module existed - it is a degradation, not a failure.
"""

import base64
import copy
import json
import mimetypes
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_BRAND = ROOT / "assets" / "brand.json"
BRANDS_DIR = ROOT / "assets" / "brands"

# Every agency the work goes out under. Alphabetical, because any other
# ordering starts to read as a ranking. The list is here, not in a prompt, so
# the CLI, the validator and the skill's own question cannot disagree about
# what the valid answers are.
AGENCIES = ("all-in", "crackwits", "daydream", "monochrome")

# Colour keys the base supplies as structure rather than brand. An agency that
# leaves these alone is not incomplete, so inheriting them is not worth a
# warning.
STRUCTURAL_COLORS = {"panel", "title", "marker_text", "tag_text", "rule", "card"}

LOGO_NAMES = {
    "light": ("logo.svg", "logo.png"),
    "dark": ("logo-dark.svg", "logo-dark.png"),
}


class BrandError(Exception):
    """Raised when a run names no agency, or one that does not exist. Loud on
    purpose, and for the same reason in both cases: a deck that goes out in the
    wrong company's colours looks entirely finished, so nothing downstream
    catches it. The build is the only place that can."""


def deep_merge(base, overlay):
    """Overlay wins on scalars and lists; dicts merge key by key. Lists are
    replaced rather than concatenated - a partial list of category colours
    would be meaningless, and an agency that redefines one means to redefine
    the set."""
    out = copy.deepcopy(base)
    for k, v in (overlay or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def available_agencies():
    """What is actually on disk, which may be fewer than AGENCIES while the
    set is being filled in."""
    if not BRANDS_DIR.exists():
        return []
    return sorted(p.name for p in BRANDS_DIR.iterdir()
                  if p.is_dir() and (p / "brand.json").exists())


def _logo_path(agency_dir, theme):
    if not agency_dir:
        return None
    for name in LOGO_NAMES[theme]:
        p = agency_dir / name
        if p.exists():
            return p
    return None


def logo_data_uri(path):
    """SVG stays SVG - it is a few hundred bytes and scales to any header
    height. PNG is accepted so an agency without a vector wordmark is not
    blocked, but it is the worse answer on a retina screen."""
    if not path:
        return ""
    mime = mimetypes.guess_type(path.name)[0] or "image/svg+xml"
    b64 = base64.b64encode(Path(path).read_bytes()).decode("ascii")
    return "data:%s;base64,%s" % (mime, b64)


def resolve(project_dir=None, project=None, agency=None, quiet=False):
    """Returns (brand, info).

    brand - the merged brand dict, the same shape every script already expects
    info  - {"slug", "source", "logo_light", "logo_dark", "logo_uri"} where
            logo_uri is the dark-background logo, because every surface that
            currently shows the agency name is dark

    project_dir/project are optional so a script with neither (a bare
    build_deck run against a loose findings.json) still gets a valid brand.
    """
    project = project or {}
    base = json.loads(BASE_BRAND.read_text(encoding="utf-8"))

    # 2 · explicit file path in project.json. Kept because a white-label run -
    # a report delivered under the client's own branding - is a real request
    # and does not belong in assets/brands/.
    override = project.get("brand")
    if not agency and override:
        p = Path(override)
        if not p.is_absolute() and project_dir:
            p = Path(project_dir) / override
        if p.exists():
            merged = deep_merge(base, json.loads(p.read_text(encoding="utf-8")))
            return merged, {"slug": None, "source": str(p), "logo_light": None,
                            "logo_dark": None, "logo_uri": ""}
        if not quiet:
            print("WARNING: project.json brand = %r not found; falling back to the agency slug"
                  % override, file=sys.stderr)

    slug = str(agency or project.get("agency") or "").strip().lower()
    if not slug:
        raise BrandError(
            "no agency set. Add \"agency\": \"<slug>\" to project.json, or pass "
            "--agency. Installed: %s\n"
            "There is no default - all four are peers, and guessing would "
            "produce a finished-looking document branded by the wrong company."
            % (", ".join(available_agencies()) or "(none installed)"))

    agency_dir = BRANDS_DIR / slug
    agency_file = agency_dir / "brand.json"
    if not agency_file.exists():
        have = available_agencies()
        raise BrandError(
            "unknown agency %r. Available: %s\n"
            "Add assets/brands/%s/brand.json, or pass one of the above."
            % (slug, ", ".join(have) or "(none installed)", slug))

    overlay = json.loads(agency_file.read_text(encoding="utf-8"))
    merged = deep_merge(base, overlay)

    # An agency file that forgot half its palette still renders - in neutral
    # grey, which reads as unfinished rather than as another agency. Say which
    # keys fell through, so it gets finished rather than shipped.
    inherited = sorted(k for k in base.get("colors", {})
                       if k not in (overlay.get("colors") or {})
                       and k not in STRUCTURAL_COLORS)
    if inherited and not quiet:
        print("NOTE: %s inherits %d neutral colour(s) from the shared base: %s. "
              "They are placeholders, not brand values."
              % (slug, len(inherited), ", ".join(inherited)), file=sys.stderr)

    light = _logo_path(agency_dir, "light")
    dark = _logo_path(agency_dir, "dark") or light

    if not dark and not quiet:
        print("NOTE: no logo for %r; the header falls back to the agency name as text. "
              "Drop logo-dark.svg into assets/brands/%s/ to fix." % (slug, slug),
              file=sys.stderr)

    return merged, {
        "slug": slug,
        "source": str(agency_file),
        "logo_light": str(light) if light else None,
        "logo_dark": str(dark) if dark else None,
        "logo_uri": logo_data_uri(dark),
    }


def load_project(project_dir):
    p = Path(project_dir) / "project.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def add_agency_arg(ap):
    """Every script that renders anything takes the same flag, spelled the
    same way."""
    ap.add_argument("--agency", default="",
                    help="agency slug (%s). Default: project.json[\"agency\"]. "
                         "There is no fallback - one of the two must be set."
                         % "|".join(AGENCIES))


if __name__ == "__main__":
    # `python3 brandkit.py` prints what is installed - the fastest way to check
    # a new agency folder is wired up before a client run depends on it.
    print("base:      %s" % BASE_BRAND)
    print("brands:    %s" % BRANDS_DIR)
    print("installed: %s" % (", ".join(available_agencies()) or "(none)"))
    for s in available_agencies():
        b, i = resolve(agency=s, quiet=True)
        print("  %-12s %-22s logo=%s" % (
            s, b.get("agency", {}).get("name", "?"),
            Path(i["logo_dark"]).name if i["logo_dark"] else "-"))
