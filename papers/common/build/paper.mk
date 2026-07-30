# paper.mk — shared Makefile include for the Epistemic-Humility paper series.
#
# Usage (from papers/<paper>/build/Makefile):
#     include ../../common/build/paper.mk
#
# The including Makefile lives in <paper>/build/ and may override PAPER_DIR,
# PANDOC_EXTRA_FLAGS, etc. before/after the include. All work runs with the
# paper root as cwd so figures/ and relative links resolve naturally.
#
# Targets:
#   pdf    — manuscript.md -> out/main.tex -> tectonic -> out/main.pdf
#   arxiv  — out/dist/<paper>-arxiv.tar.gz (main.tex + figures/, the layout
#            arXiv ingestion expects: tex at tarball root, figures/ subdir)
#   check  — run paper_build_check.py (figure refs, link rot, prose rules)
#   clean  — remove out/
#
# Tools: pandoc 3.x and tectonic on PATH, or in ~/.local/bin (fallback).
# Pinned versions + sha256s are recorded in papers/common/build/README.md.

COMMON_BUILD := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
PAPER_BUILD  := $(abspath .)
PAPER_DIR    ?= $(abspath ..)
PAPER_NAME   := $(notdir $(PAPER_DIR))
OUT          := $(PAPER_BUILD)/out

PANDOC   ?= $(or $(shell command -v pandoc 2>/dev/null),$(HOME)/.local/bin/pandoc)
TECTONIC ?= $(or $(shell command -v tectonic 2>/dev/null),$(HOME)/.local/bin/tectonic)
PYTHON   ?= python3

MANUSCRIPT := $(PAPER_DIR)/manuscript.md
TEMPLATE   := $(COMMON_BUILD)/template.tex
DEFAULTS   := $(COMMON_BUILD)/defaults.yaml
FILTERS    := $(COMMON_BUILD)/manuscript-filters.lua
CHECKER    := $(COMMON_BUILD)/scripts/paper_build_check.py
METADATA   := $(PAPER_BUILD)/metadata.yaml

PANDOC_EXTRA_FLAGS ?=

.PHONY: all pdf tex arxiv check clean
.DELETE_ON_ERROR:

all: check pdf

tex: $(OUT)/main.tex
pdf: $(OUT)/main.pdf

$(OUT)/main.tex: $(MANUSCRIPT) $(TEMPLATE) $(DEFAULTS) $(FILTERS) $(METADATA)
	@mkdir -p $(OUT)
	cd $(PAPER_DIR) && $(PANDOC) \
	  --defaults $(DEFAULTS) \
	  --template $(TEMPLATE) \
	  --lua-filter $(FILTERS) \
	  --metadata-file $(METADATA) \
	  $(PANDOC_EXTRA_FLAGS) \
	  -o $@ manuscript.md

# tectonic resolves \includegraphics relative to the input file's directory,
# so expose the paper's figures/ inside out/ via symlink.
$(OUT)/main.pdf: $(OUT)/main.tex
	@ln -sfn $(PAPER_DIR)/figures $(OUT)/figures
	cd $(PAPER_DIR) && $(TECTONIC) --outdir $(OUT) $(OUT)/main.tex

# arXiv ingestion layout: main.tex at tarball root, figures/ subdir with only
# the figures the tex actually references.
arxiv: $(OUT)/main.pdf
	rm -rf $(OUT)/dist
	mkdir -p $(OUT)/dist/figures
	cp $(OUT)/main.tex $(OUT)/dist/
	@refs=$$(grep -o '{figures/[^}]*}' $(OUT)/main.tex | sed 's/[{}]//g' | sort -u); \
	if [ -z "$$refs" ]; then echo "WARNING: no figures referenced in main.tex"; fi; \
	for f in $$refs; do cp $(PAPER_DIR)/$$f $(OUT)/dist/figures/ || exit 1; done
	tar czf $(OUT)/$(PAPER_NAME)-arxiv.tar.gz -C $(OUT)/dist .
	@echo "arXiv tarball: $(OUT)/$(PAPER_NAME)-arxiv.tar.gz"
	@tar tzf $(OUT)/$(PAPER_NAME)-arxiv.tar.gz

check:
	$(PYTHON) $(CHECKER) $(PAPER_DIR)

clean:
	rm -rf $(OUT)
