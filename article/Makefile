.PHONY: all pdf clean

BUILD_DIR = build

pdf:
	@mkdir -p $(BUILD_DIR)
	export PATH=/Library/TeX/texbin:$$PATH && \
		xelatex -output-directory=$(BUILD_DIR) -interaction=nonstopmode main.tex ; \
		-bibtex $(BUILD_DIR)/main 2>/dev/null || true ; \
		xelatex -output-directory=$(BUILD_DIR) -interaction=nonstopmode main.tex ; \
		xelatex -output-directory=$(BUILD_DIR) -interaction=nonstopmode main.tex ; \
		true

clean:
	rm -rf $(BUILD_DIR)/