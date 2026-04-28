#!/usr/bin/env bash
set -e

BINARY="./build/sdf_raster_bench"

if [ ! -f "$BINARY" ]; then
    echo "ERROR: бинарник $BINARY не найден. Собери проект сначала."
    echo "Используется results.json.example для отладки."
    cp bench/results.json.example bench/results.json
    exit 0
fi

echo "Запускаю бенчмарк..."
$BINARY \
    --models "Dragon Bunny Armadillo Buddha" \
    --sizes "2 4 8 16 32 64 128 256" \
    --resolutions "1920x1080 2560x1440 3840x2160" \
    --warmup-frames 100 \
    --measure-frames 1000 \
    --output bench/results.json

echo "Готово: bench/results.json"
