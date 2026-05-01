# Accelerating Implicit Surface Rasterization on GPUs

**Master's Thesis** — Accelerating Rasterization of Surfaces Defined by Implicit Functions on Graphics Processors

**Andrey Trifonov** — Lomonosov Moscow State University, 2026

---

## Structure

```
.
├── thesis/           # Master's thesis (XeLaTeX)
│   ├── main.tex
│   ├── chapters/     # 6 chapters
│   ├── Makefile
│   └── bench/        # Benchmarks
├── article/          # Conference paper (PG2026 Eurographics)
│   └── *.tex, *.sty  # Official template
└── sdf_raster/       # Source code (submodule)
```

---

## Thesis

```bash
cd thesis

# Install packages (if needed)
tlmgr install gost tex-gyre comment lastpage

# Build (XeLaTeX)
make all       # benchmarks + data + PDF
make paper     # PDF only
make clean
```

**Pipeline:** `gen_paper_data.py` → `xelatex` → `bibtex` → `xelatex` → `xelatex`

**Output:** `thesis/build/main.pdf`

---

## Article

PG2026 Eurographics template from [pacificgraphics2026.github.io](https://pacificgraphics2026.github.io/)

```bash
cd article

# Build template (pdflatex)
pdflatex EGauthorGuidelines-PG2026-sub.tex
```

---

## Clone

```bash
git clone --recurse-submodules https://github.com/Reefufui/master_thesis.git
cd master_thesis

# Build sdf_raster
cd sdf_raster && mkdir build && cd build
cmake .. && cmake --build . --config Release
```

---

## Requirements

- CMake 3.20+, C++20, Vulkan SDK 1.3+
- Python 3.10+
- TeX Live (xelatex, bibtex)
