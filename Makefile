.PHONY: all results paper paper-only clean

BUILD_DIR = build
RESULTS_JSON = bench/results.json

results: $(RESULTS_JSON)
	python3 scripts/gen_paper_data.py

$(RESULTS_JSON):
	bash bench/run_bench.sh

paper: results
	@mkdir -p $(BUILD_DIR)
	export PATH=/Library/TeX/texbin:$$PATH && \
		xelatex -output-directory=$(BUILD_DIR) -interaction=nonstopmode main.tex && \
		bibtex $(BUILD_DIR)/main && \
		xelatex -output-directory=$(BUILD_DIR) -interaction=nonstopmode main.tex && \
		xelatex -output-directory=$(BUILD_DIR) -interaction=nonstopmode main.tex

paper-only:
	@mkdir -p $(BUILD_DIR)
	python3 scripts/gen_paper_data.py
	export PATH=/Library/TeX/texbin:$$PATH && \
		xelatex -output-directory=$(BUILD_DIR) -interaction=nonstopmode main.tex && \
		bibtex $(BUILD_DIR)/main && \
		xelatex -output-directory=$(BUILD_DIR) -interaction=nonstopmode main.tex && \
		xelatex -output-directory=$(BUILD_DIR) -interaction=nonstopmode main.tex

all: results paper

clean:
	rm -rf $(BUILD_DIR)/
	rm -f generated/*.tex