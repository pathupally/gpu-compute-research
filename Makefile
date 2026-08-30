PYTHON ?= python3
PDFLATEX ?= pdflatex
PAPER_NAME := the-benchmark-is-part-of-the-option

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
	mkdir -p output/pdf
	$(PDFLATEX) -interaction=nonstopmode -halt-on-error -jobname=$(PAPER_NAME) -output-directory=output/pdf paper/manuscript.tex
	$(PDFLATEX) -interaction=nonstopmode -halt-on-error -jobname=$(PAPER_NAME) -output-directory=output/pdf paper/manuscript.tex

refreeze:
	$(PYTHON) src/freeze_inputs.py
