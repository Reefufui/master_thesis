# Ускорение растеризации неявных поверхностей на GPU

**Магистерская диссертация** — Ускорение алгоритмов растеризации поверхностей, заданных неявными функциями, на графических процессорах

**Andrey Trifonov** — МГУ им. М.В. Ломоносова, 2026

---

## Структура

```
.
├── thesis/           # Диссертация (XeLaTeX)
│   ├── main.tex
│   ├── chapters/     # 6 глав
│   ├── Makefile
│   └── bench/         # Бенчмарки
├── article/          # Статья (PG2026 Eurographics)
│   └── *.tex, *.sty  # Официальный шаблон
└── sdf_raster/       # Исходный код (submodule)
```

---

## Диссертация

```bash
cd thesis

# Установка пакетов (если нужно)
tlmgr install gost tex-gyre comment lastpage

# Сборка (XeLaTeX)
make all       # бенчмарки + данные + PDF
make paper     # только PDF
make clean
```

**Pipeline:** `gen_paper_data.py` → `xelatex` → `bibtex` → `xelatex` → `xelatex`

**Результат:** `thesis/build/main.pdf`

---

## Статья

Шаблон PG2026 Eurographics с [pacificgraphics2026.github.io](https://pacificgraphics2026.github.io/)

```bash
cd article

# Сборка шаблона (pdflatex)
pdflatex EGauthorGuidelines-PG2026-sub.tex
```

---

## Клонирование

```bash
git clone --recurse-submodules https://github.com/Reefufui/master_thesis.git
cd master_thesis

# Сборка sdf_raster
cd sdf_raster && mkdir build && cd build
cmake .. && cmake --build . --config Release
```

---

## Требования

- CMake 3.20+, C++20, Vulkan SDK 1.3+
- Python 3.10+
- TeX Live (xelatex, bibtex)
