#!/usr/bin/env python3
import json
import os

os.makedirs("generated", exist_ok=True)

data = json.load(open("bench/results.json"))

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

ROW_END = " \\\\\n"

def write_table(filename, rows, formatter):
    with open(f"generated/{filename}", "w", encoding="utf-8") as f:
        for i, row in enumerate(rows):
            line = formatter(row)
            eol = ROW_END if i < len(rows) - 1 else "\n"
            f.write(line + eol)

write_table("tab_fps_by_size.tex", data["fps_by_size"],
    lambda r: f"    {r['model']} ({r['size_mb']} МБ) & {r['ours']:.1f} & {r['mesh']:.1f} & {r['scom_rt']:.1f}")

write_table("tab_fps_by_res.tex", data["fps_by_resolution"],
    lambda r: f"    {r['resolution']} & {r['ours']:.1f} & {r['scom_rt']:.1f}")

write_table("tab_psnr.tex", data["psnr"],
    lambda r: f"    {r['model']} & {r['ours']:.1f} & {r['scom_rt']:.1f}")

write_table("tab_culling.tex", data["culling"],
    lambda r: f"    {r['model']} & {r['frustum_pct']} & {r['hiz_pct']} & {r['total_pct']}")

def ablation_fmt(r):
    gain = str(r["gain_pct"]) if r["gain_pct"] is not None else "---"
    return f"    {r['config']} & {r['fps']:.1f} & {gain}"

write_table("tab_ablation.tex", data["ablation"], ablation_fmt)

with open("generated/tab_city.tex", "w", encoding="utf-8") as f:
    c = data["city_scene"]
    rows = [
        f"    FPS & {c['fps']:.1f}",
        f"    GPU Scene Memory & {c['gpu_memory_mb']} МБ",
        f"    Всего листьев & {c['total_leaves']:,}",
        f"    Активных листьев & {c['active_leaves']:,}",
        f"    Отсечено Frustum & {c['frustum_pct']}\%",
        f"    Отсечено Hi-Z & {c['hiz_pct']}\%",
        f"    Отсечено LOD & {c['lod_pct']}\%",
    ]
    f.write(ROW_END.join(rows) + "\n")

print("Generated files in generated/")
