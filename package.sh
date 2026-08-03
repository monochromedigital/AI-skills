#!/usr/bin/env bash
# Package a skill folder into a .skill bundle (a zip Claude can install).
#   ./package.sh website-assessment     -> dist/website-assessment.skill
#   ./package.sh                        -> packages every skill
set -euo pipefail

cd "$(dirname "$0")"
mkdir -p dist

package() {
  local name="$1"
  [ -f "skills/$name/SKILL.md" ] || { echo "no SKILL.md in skills/$name" >&2; exit 1; }
  rm -f "dist/$name.skill"
  ( cd skills && zip -qr "../dist/$name.skill" "$name" -x '*.DS_Store' '*__pycache__*' )
  echo "dist/$name.skill"
}

if [ $# -gt 0 ]; then
  for s in "$@"; do package "$s"; done
else
  for d in skills/*/; do package "$(basename "$d")"; done
fi
