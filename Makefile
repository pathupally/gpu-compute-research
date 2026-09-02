PYTHON ?= python3
PDFLATEX ?= pdflatex
PAPER_NAME := the-benchmark-is-part-of-the-option
export SOURCE_DATE_EPOCH := 1788134400
export FORCE_SOURCE_DATE := 1
export TZ := UTC

.PHONY: all verify analysis figures paper refreeze

all: verify analysis figures paper

verify:
	$(PYTHON) -m unittest discover -s tests -v

analysis:
	$(PYTHON) src/study.py

figures: analysis
	@test -s paper/generated/surface_bounds_picture.tex
	@test -s paper/generated/fragility_frontier_picture.tex

paper: figures
	mkdir -p outputs/pdf
	$(PDFLATEX) -interaction=nonstopmode -halt-on-error -jobname=$(PAPER_NAME) -output-directory=outputs/pdf paper/manuscript.tex
	$(PDFLATEX) -interaction=nonstopmode -halt-on-error -jobname=$(PAPER_NAME) -output-directory=outputs/pdf paper/manuscript.tex

refreeze:
	@test -n "$(SOURCE_ROOT)" || (echo "SOURCE_ROOT is required" >&2; exit 2)
	$(PYTHON) src/freeze_inputs.py --source-root "$(SOURCE_ROOT)"
