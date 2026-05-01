# Воспроизведение результатов диссертации

**Ускорение алгоритмов растеризации поверхностей, заданных неявными функциями, на графических процессорах**

## Структура

```
.
├── thesis/           # Магистерская диссертация (LaTeX)
│   ├── main.tex
│   ├── chapters/
│   ├── Makefile      # make paper | make all | make clean
│   └── bench/        # Бенчмарки для sdf_raster
├── article/          # Английская статья (заготовка)
│   ├── main.tex
│   ├── sections/
│   └── Makefile      # make pdf
└── sdf_raster/       # Исходный код (git submodule)
```

## Быстрый старт (диссертация)

```bash
# 1. Клонировать репозиторий с подмодулями
git clone --recurse-submodules https://github.com/Reefufui/master_thesis.git
cd master_thesis

# 2. Сборка sdf_raster
cd sdf_raster
mkdir build && cd build
cmake .. && cmake --build . --config Release
cd ../..

# 3. Запуск бенчмарков (результаты в bench/results.json)
cd thesis
./bench/run_bench.sh

# 4. Генерация PDF
make all
```

## Быстрый старт (статья)

```bash
cd article
make pdf
```

## Детальная инструкция

### Требования

- **Сборка:** CMake 3.20+, C++20, Vulkan SDK 1.3+
- **Тесты:** Python 3.10+
- **LaTeX:** XeLaTeX, BibTeX, gost71u.bst (TeX Live)

### 1. Подмодули

Репозиторий содержит подмодуль `sdf_raster` — основную программу.

При клонировании без `--recurse-submodules`:
```bash
git clone https://github.com/Reefufui/master_thesis.git
cd master_thesis
git submodule update --init
```

### 2. Сборка sdf_raster

```bash
cd sdf_raster
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . -j$(nproc)
```

На выходе: `sdf_raster/build/src/SdfRaster`

### 3. Запуск бенчмарков

```bash
./bench/run_bench.sh
```

Скрипт выполняет бенчмарки и записывает результаты в `bench/results.json`.

**Структура results.json:**
```json
{
  "scenes": [...],
  "hardware": {...},
  "fps_by_size": [...],
  "fps_by_resolution": [...],
  "psnr": [...],
  "culling": [...],
  "ablation": [...],
  "city_scene": {...}
}
```

Для разработки без запуска бенчмарков используется `bench/results.json.example`.

### 4. Генерация таблиц

```bash
make results          # только генерация из bench/results.json
make results-only    # генерация из bench/results.json.example
```

Генерирует:
- `generated/macros.tex` — макросы с числами
- `generated/tab_*.tex` — таблицы с booktabs линиями

### 5. Сборка PDF

```bash
make paper            # генерация данных + PDF
make paper-only       # только PDF (данные уже есть)
make all              # всё вместе
```

Pipeline: `python3 scripts/gen_paper_data.py` → `xelatex` → `bibtex` → `xelatex` → `xelatex`

Требуется 2-3 прохода XeLaTeX для разрешения всех ссылок.

### 6. Очистка

```bash
make clean            # удалить aux, log, toc, generated/
```

## Структура проекта

```
master_thesis/
├── sdf_raster/       # submodule: программа рендеринга SDF
├── bench/
│   ├── results.json.example   # пример данных для разработки
│   └── run_bench.sh          # скрипт запуска бенчмарков
├── scripts/
│   └── gen_paper_data.py     # генерация таблиц из JSON
├── generated/        # автогенерированные .tex файлы (не коммитится)
├── main.tex          # исходник статьи
├── references.bib     # библиография
└── Makefile
```

## Устранение проблем

**LaTeX не находит gost71u:**
```bash
tlmgr install gost tex-gyre  # TeX Live
```

**Unicode ошибки:**
```bash
export PATH=/Library/TeX/texbin:$PATH
xelatex main.tex
```

**BibTeX ошибки:**
```bash
# убедиться что bibtex запущен после первого xelatex
xelatex main && bibtex main && xelatex main && xelatex main
```
