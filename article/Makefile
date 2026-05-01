.PHONY: all pdf clean

BUILD_DIR = build

pdf:
	@mkdir -p $(BUILD_DIR)
	export PATH=/Library/TeX/texbin:$$PATH && \
		pdflatex -output-directory=$(BUILD_DIR) -interaction=nonstopmode main.tex && \
		-bibtex $(BUILD_DIR)/main || true && \
		pdflatex -output-directory=$(BUILD_DIR) -interaction=nonstopmode main.tex && \
		pdflatex -output-directory=$(BUILD_DIR) -interaction=nonstopmode main.tex

clean:
	rm -rf $(BUILD_DIR)/