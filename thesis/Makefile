.PHONY: all results paper paper-only clean

SCRIPT_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
BUILD_DIR = build

results:
	python3 $(SCRIPT_DIR)scripts/gen_paper_data.py

paper: results
	@mkdir -p $(BUILD_DIR)
	export PATH=/Library/TeX/texbin:$$PATH && \
		xelatex -output-directory=$(BUILD_DIR) -interaction=nonstopmode main.tex && \
		bibtex $(BUILD_DIR)/main && \
		xelatex -output-directory=$(BUILD_DIR) -interaction=nonstopmode main.tex && \
		xelatex -output-directory=$(BUILD_DIR) -interaction=nonstopmode main.tex

paper-only:
	@mkdir -p $(BUILD_DIR)
	python3 $(SCRIPT_DIR)scripts/gen_paper_data.py
	export PATH=/Library/TeX/texbin:$$PATH && \
		xelatex -output-directory=$(BUILD_DIR) -interaction=nonstopmode main.tex && \
		bibtex $(BUILD_DIR)/main && \
		xelatex -output-directory=$(BUILD_DIR) -interaction=nonstopmode main.tex && \
		xelatex -output-directory=$(BUILD_DIR) -interaction=nonstopmode main.tex

all: results paper

clean:
	rm -rf $(BUILD_DIR)/
	rm -f generated/*.tex