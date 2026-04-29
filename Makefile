.PHONY: all results paper paper-only clean

RESULTS_JSON = bench/results.json

results: $(RESULTS_JSON)
	python3 scripts/gen_paper_data.py

$(RESULTS_JSON):
	bash bench/run_bench.sh

paper: results
	export PATH=/Library/TeX/texbin:$$PATH && \
	xelatex -interaction=nonstopmode main.tex && \
	bibtex main && \
	xelatex -interaction=nonstopmode main.tex && \
	xelatex -interaction=nonstopmode main.tex

paper-only:
	python3 scripts/gen_paper_data.py
	export PATH=/Library/TeX/texbin:$$PATH && \
	xelatex -interaction=nonstopmode main.tex && \
	bibtex main && \
	xelatex -interaction=nonstopmode main.tex && \
	xelatex -interaction=nonstopmode main.tex

all: results paper

clean:
	rm -f *.aux *.log *.toc *.out *.bbl *.blg
	rm -rf generated/
