# Skills repo. `make` runs the checks; `make zip` produces upload artifacts.
#
# The shared-file invariant is enforced by scripts/build_standalone.py, which
# already had to know that list in order to generate the portable checker. It
# scans every skill under skills/, so a third skill that picks up a shared file
# is covered without editing anything here. Keeping a second list in a shell
# script would be the same drift this repo exists to prevent.
#
# The syntax check globs skills/*/ for the same reason. It used to name A and B,
# which read as harmless while those were the only two skills with code in them.
# atomic-design arrived with a validator that `make zip` packages and uploads
# and nothing ever parsed. A check that silently covers a subset is worse than
# one that covers nothing, because the green tick is read as coverage.

A := skills/website-assessment
B := skills/sitemap-ia-board
SHARED := scripts/render_report.py scripts/brandkit.py scripts/check_prose.py \
          references/project-contract.md references/ai-writing.md \
          assets/brand.json assets/ai-writing.json

.PHONY: all check sync zip brands clean

all: check

check:
	@echo "== shared files =="
	@python3 scripts/build_standalone.py --check
	@echo "  All shared files identical."
	@echo "== python syntax =="
	@for f in skills/*/scripts/*.py scripts/*.py; do \
	  python3 -c "import ast,sys;ast.parse(open('$$f').read())" || exit 1; done
	@echo "  all parse"
	@echo "== agencies installed =="
	@cd $(A) && python3 scripts/brandkit.py

# website-assessment is the source of truth for shared files; the board copies.
sync:
	@for f in $(SHARED); do cp "$(A)/$$f" "$(B)/$$f"; done
	@rm -rf "$(B)/assets/brands" && cp -r "$(A)/assets/brands" "$(B)/assets/brands"
	@python3 scripts/build_standalone.py
	@echo "synced $(A) -> $(B)"

brands:
	@cd $(A) && python3 scripts/brandkit.py

# package.sh regenerates the standalone checker and enforces the shared-file
# invariant before it writes anything, so a drifted copy fails here rather than
# in a client's report.
zip: check
	@./package.sh

clean:
	@rm -f dist/*.skill
	@find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
