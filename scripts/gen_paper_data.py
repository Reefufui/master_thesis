#!/usr/bin/env python3
import json
import os

os.makedirs("generated", exist_ok=True)

import json, os
example_path = "bench/results.json.example"
main_path = "bench/results.json"
data = json.load(open(main_path if os.path.exists(main_path) else example_path))

with open("generated/macros.tex", "w", encoding="utf-8") as f:
    def cmd(name, value):
        f.write("\\newcommand{\\" + name + "}{" + value + "}\n")

    hw = data["hardware"]
    cmd("HWgpu", hw["gpu"])
    cmd("HWcpu", hw["cpu"])
    cmd("HWcpuGHz", f'{hw["cpu_ghz"]:.1f}')
    cmd("HWramGB", str(hw["ram_gb"]))
    cmd("HWvulkan", hw["vulkan"])

    fps_by_size = data["fps_by_size"]
    ours_fps = [r["ours"] for r in fps_by_size]
    scom_fps = [r["scom_rt"] for r in fps_by_size]
    speedups = [o/s for o, s in zip(ours_fps, scom_fps)]

    cmd("SpeedupMin", f'{min(speedups):.1f}')
    cmd("SpeedupMax", f'{max(speedups):.1f}')
    cmd("SpeedupAvg", f'{sum(speedups)/len(speedups):.1f}')

    psnr = data["psnr"]
    psnr_diffs = [r["scom_rt"] - r["ours"] for r in psnr]

    cmd("PSNRdiffMax", f'{max(psnr_diffs):.1f}')
    cmd("PSNRdiffMin", f'{min(psnr_diffs):.1f}')

    ablation = data["ablation"]
    speedup_total = ablation[-1]["fps"] / ablation[0]["fps"]

    cmd("AblationSpeedup", f'{speedup_total:.1f}')

    res_data = data["fps_by_resolution"]
    deg_ours = res_data[0]["ours"] / res_data[-1]["ours"]
    deg_scom = res_data[0]["scom_rt"] / res_data[-1]["scom_rt"]

    cmd("ResDegOurs", f'{deg_ours:.1f}')
    cmd("ResDegScom", f'{deg_scom:.1f}')

def gen_table(filename, spec, header, rows, caption, label):
    with open(f"generated/{filename}", "w", encoding="utf-8") as f:
        f.write("\\begin{table}[h]\n")
        f.write("  \\centering\n")
        f.write(f"  \\caption{{{caption}}}\n")
        f.write(f"  \\label{{{label}}}\n")
        f.write(f"  \\begin{{tabular}}{{{spec}}}\n")
        f.write("    \\toprule\n")
        f.write(header + "\n")
        f.write("    \\midrule\n")
        for row in rows[:-1]:
            f.write(row + " \\\\\n")
        f.write(rows[-1] + " \\\\\n")
        f.write("    \\bottomrule\n")
        f.write("  \\end{tabular}\n")
        f.write("\\end{table}\n")

def gen_methods_comparison():
    with open("generated/tab_methods_comparison.tex", "w", encoding="utf-8") as f:
        f.write("\\begin{table}[h]\n")
        f.write("  \\centering\n")
        f.write("  \\caption{Сравнение методов рендеринга SDF.}\n")
        f.write("  \\label{tab:methods_comparison}\n")
        f.write("  \\begin{tabular}{lccc}\n")
        f.write("    \\toprule\n")
        f.write("    \\textbf{Метод} & \\textbf{Качество} & \\textbf{Производительность} & \\textbf{Точность SDF} \\\\\n")
        f.write("    \\midrule\n")
        f.write("    Sphere Tracing & Высокое & Низкая & Точная \\\\\n")
        f.write("    Volume Rendering (MLP) & Высокое & Очень низкая & Точная \\\\\n")
        f.write("    Voxel + RT & Среднее & Средняя & Приближённая \\\\\n")
        f.write("    \\textbf{SDF Rasterization (ours)} & \\textbf{Высокое} & \\textbf{Высокая} & \\textbf{Точная} \\\\\n")
        f.write("    \\bottomrule\n")
        f.write("  \\end{tabular}\n")
        f.write("\\end{table}\n")

gen_methods_comparison()

gen_table("tab_fps_by_size.tex", "lrrrr",
    "    \\textbf{Модель} & \\textbf{предложенный} & \\textbf{Mesh} & \\textbf{SCom RT} \\\\",
    [f"    {r['model']} ({r['size_mb']} МБ) & {r['ours']:.1f} & {r['mesh']:.1f} & {r['scom_rt']:.1f}" for r in data["fps_by_size"]],
    "FPS при различном размере SCom-файла.",
    "tab:fps_by_size")

gen_table("tab_fps_by_res.tex", "lrrr",
    "    \\textbf{Разрешение} & \\textbf{предложенный} & \\textbf{SCom RT} \\\\",
    [f"    {r['resolution']} & {r['ours']:.1f} & {r['scom_rt']:.1f}" for r in data["fps_by_resolution"]],
    "FPS при различном разрешении.",
    "tab:fps_by_resolution")

gen_table("tab_psnr.tex", "lrrr",
    "    \\textbf{Модель} & \\textbf{предложенный} & \\textbf{SCom RT (ref)} \\\\",
    [f"    {r['model']} & {r['ours']:.1f} & {r['scom_rt']:.1f}" for r in data["psnr"]],
    "PSNR (дБ) для различных моделей.",
    "tab:psnr")

gen_table("tab_culling.tex", "lrrrr",
    "    \\textbf{Модель} & \\textbf{Frustum} & \\textbf{Hi-Z} & \\textbf{Итого} \\\\",
    [f"    {r['model']} & {r['frustum_pct']} & {r['hiz_pct']} & {r['total_pct']}" for r in data["culling"]],
    "Доля отсечённых узлов октодерева.",
    "tab:culling_stats")

def ablation_rows():
    rows = []
    for r in data["ablation"]:
        gain = f"+{r['gain_pct']}" if r["gain_pct"] is not None else "---"
        rows.append(f"    {r['config']} & {r['fps']:.1f} & {gain}")
    return rows

gen_table("tab_ablation.tex", "lrrr",
    "    \\textbf{Конфигурация} & \\textbf{FPS} & \\textbf{Прирост} \\\\",
    ablation_rows(),
    "Ablation study: вклад каждого компонента.",
    "tab:ablation")

with open("generated/tab_city.tex", "w", encoding="utf-8") as f:
    c = data["city_scene"]
    f.write("\\begin{table}[h]\n")
    f.write("  \\centering\n")
    f.write("  \\caption{Метрики на сцене города.}\n")
    f.write("  \\label{tab:city_metrics}\n")
    f.write("  \\begin{tabular}{lr}\n")
    f.write("    \\toprule\n")
    f.write("    \\textbf{Метрика} & \\textbf{Значение} \\\\\n")
    f.write("    \\midrule\n")
    f.write(f"    FPS & {c['fps']:.1f} \\\\\n")
    f.write(f"    GPU Scene Memory & {c['gpu_memory_mb']} МБ \\\\\n")
    f.write(f"    Всего листьев & {c['total_leaves']:,} \\\\\n")
    f.write(f"    Активных листьев & {c['active_leaves']:,} \\\\\n")
    f.write(f"    Отсечено Frustum & {c['frustum_pct']}\\% \\\\\n")
    f.write(f"    Отсечено Hi-Z & {c['hiz_pct']}\\% \\\\\n")
    f.write(f"    Отсечено LOD & {c['lod_pct']}\\% \\\\\n")
    f.write("    \\bottomrule\n")
    f.write("  \\end{tabular}\n")
    f.write("\\end{table}\n")

with open("generated/tab_scenes.tex", "w", encoding="utf-8") as f:
    f.write("\\begin{table}[h]\n")
    f.write("  \\centering\n")
    f.write("  \\caption{Тестовые модели.}\n")
    f.write("  \\label{tab:scenes}\n")
    f.write("  \\begin{tabular}{lrr}\n")
    f.write("    \\toprule\n")
    f.write("    \\textbf{Модель} & \\textbf{Треугольников} & \\textbf{Размер SCom, МБ} \\\\\n")
    f.write("    \\midrule\n")
    for s in data["scenes"]:
        tris = f"{s['triangles']:,}".replace(",", "\\,")
        f.write(f"    {s['model']} & {tris} & {s['size_mb']} \\\\\n")
    f.write("    \\bottomrule\n")
    f.write("  \\end{tabular}\n")
    f.write("\\end{table}\n")

print("Generated files in generated/")
