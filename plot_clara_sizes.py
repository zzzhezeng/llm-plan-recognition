#!/usr/bin/env python3
"""LLMs as recognizers on the CLARA grids, by grid size: one line per method, one panel per family.

Reads results/clara/summary_by_size.csv (run `clara.py score` first) and writes
results/figures/clara_by_size_p_true.svg or clara_by_size_accuracy.svg. Stdlib only.

  python3 plot_clara_sizes.py                     # P(true)
  python3 plot_clara_sizes.py --metric accuracy   # accuracy (1/k for a k-way tie at the top)
"""

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SUMMARY = ROOT / "results" / "clara" / "summary_by_size.csv"
OUT = ROOT / "results" / "figures"

FAMILIES = [("SimpleGrid", "N − 1 goals on an N×N grid"),
            ("TwoPackage", "4 goals"),
            ("TwoPackageOneway", "4 goals"),
            ("ThreePackage", "8 goals"),
            ("FourPackage", "12 goals")]
LEVELS = [(25, "25% of the plan observed", "the stop rule scores exactly chance here"),
          (100, "Whole plan observed", "the stop rule scores 1.0 at every size")]
# LLMs on solid lines in plot_clara.py's colors, then the recognizers on dashed ink lines.
SERIES = [
    ("gpt-6-luna", "gpt-6-luna", "#2a78d6", "circle", None),
    ("gpt-5.4-mini", "gpt-5.4-mini", "#eb6834", "triangle", None),
    ("jev-latest", "Jev", "#1baf7a", "diamond", None),
    ("hf:Qwen/Qwen2.5-7B-Instruct", "Qwen2.5-7B", "#eda100", "down", None),
    ("hf:meta-llama/Meta-Llama-3-8B-Instruct", "Llama-3-8B", "#e87ba4", "circle", None),
    ("max-term", "max-term (recognizer)", "#1f1f1e", "square", "8 5"),
    ("sharpsat-td", "SharpSAT-TD (recognizer)", "#1f1f1e", "ring", "2 5"),
]
RECOGNIZERS = {"max-term", "sharpsat-td"}
METRICS = {"p_true": "P(true goal)", "accuracy": "Accuracy"}

INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"

STEP = 54              # pixels between neighbouring grid sizes
PAD = 30               # inside a panel, beyond its smallest and largest size
MIN_W = 170
GAP = 60
LEFT = 120
PANEL_H = 320
TOP = 370
BLOCK_GAP = 210


def load():
    with SUMMARY.open() as f:
        return {(r["model"], r["family"], int(r["size"]), int(r["pct"])): r for r in csv.DictReader(f)}


def text(x, y, s, size=22, color=INK2, anchor="start", weight=400):
    s = s.replace("&", "&amp;").replace("<", "&lt;")
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{s}</text>')


def marker(kind, x, y, color, size=13):
    s = size / 2
    if kind == "ring":
        return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{s:.1f}" fill="{SURFACE}" stroke="{color}" stroke-width="2.5"/>'
    ring = f'stroke="{SURFACE}" stroke-width="2"'
    if kind == "circle":
        return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{s:.1f}" fill="{color}" {ring}/>'
    if kind == "square":
        return f'<rect x="{x - s:.1f}" y="{y - s:.1f}" width="{size}" height="{size}" rx="2" fill="{color}" {ring}/>'
    if kind == "diamond":
        s *= 1.25
        pts = [(x, y - s), (x + s, y), (x, y + s), (x - s, y)]
    elif kind == "triangle":
        s *= 1.2
        pts = [(x, y - s), (x + s, y + s * 0.8), (x - s, y + s * 0.8)]
    else:  # down
        s *= 1.2
        pts = [(x, y + s), (x + s, y - s * 0.8), (x - s, y - s * 0.8)]
    p = " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)
    return f'<polygon points="{p}" fill="{color}" {ring}/>'


def build(data, metric):
    sizes = {fam: sorted({s for m, f, s, _ in data if f == fam and m == "stop-rule"}) for fam, _ in FAMILIES}
    widths = [max(MIN_W, STEP * (len(sizes[fam]) - 1) + 2 * PAD) for fam, _ in FAMILIES]
    lefts = [LEFT + sum(widths[:i]) + GAP * i for i in range(len(FAMILIES))]
    W = lefts[-1] + widths[-1] + 40
    H = TOP + len(LEVELS) * PANEL_H + (len(LEVELS) - 1) * BLOCK_GAP + 170

    el = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
          f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    el.append(text(40, 56, f"LLMs as recognizers on the CLARA grids, by grid size: {METRICS[metric]}", 34, INK, weight=600))
    el.append(text(40, 96, "Each point is the mean over one grid size's evidence files; each LLM answered every "
                           "file 3 times.", 21, INK2))

    # Legend, wrapping onto a second row when it runs out of width.
    x, y = 40, 150
    entries = [(label, color, kind, dash) for _, label, color, kind, dash in SERIES]
    for label, color, kind, dash in entries + [("chance = 1 / number of goals", INK2, None, "6 5")]:
        width = 56 + len(label) * 11 + 44
        if x + width > W - 40:
            x, y = 40, y + 42
        el.append(f'<line x1="{x}" y1="{y}" x2="{x + 44}" y2="{y}" stroke="{color}" stroke-width="2"'
                  + (f' stroke-dasharray="{dash}"/>' if dash else "/>"))
        if kind:
            el.append(marker(kind, x + 22, y, color))
        el.append(text(x + 56, y + 7, label, 21, INK if kind else INK2))
        x += width

    for bi, (pct, title, note) in enumerate(LEVELS):
        top = TOP + bi * (PANEL_H + BLOCK_GAP)
        el.append(text(40, top - 96, title, 28, INK, weight=600))
        el.append(text(40 + len(title) * 15 + 24, top - 96, note, 21, MUTED))
        py = lambda v: top + (1 - v) * PANEL_H
        el.append(f'<text transform="translate({LEFT - 70},{top + PANEL_H / 2}) rotate(-90)" font-family="{FONT}" '
                  f'font-size="21" fill="{INK2}" text-anchor="middle">{METRICS[metric]}</text>')

        for (fam, fnote), left, width in zip(FAMILIES, lefts, widths):
            fs = sizes[fam]
            if len(fs) == 1:
                px = lambda s: left + width / 2
            else:
                px = lambda s, fs=fs: left + PAD + (s - fs[0]) / (fs[-1] - fs[0]) * (width - 2 * PAD)
            el.append(text(left, top - 46, fam, 21, INK, weight=600))
            el.append(text(left, top - 20, fnote, 18, MUTED))

            # Recessive grid and a baseline axis; y labels on the first panel only.
            for i in range(5):
                v = i / 4
                el.append(f'<line x1="{left}" y1="{py(v):.1f}" x2="{left + width}" y2="{py(v):.1f}" '
                          f'stroke="{AXIS if i == 0 else GRID}" stroke-width="{2 if i == 0 else 1}"/>')
                if left == lefts[0]:
                    el.append(text(left - 12, py(v) + 6, f"{v:g}", 17, MUTED, "end"))
            for s in fs:
                el.append(text(px(s), top + PANEL_H + 28, f"{s}×{s}", 16, MUTED, "middle"))

            for key, _, color, kind, dash in SERIES:
                pts = []
                for s in fs:
                    r = data.get((key, fam, s, pct))
                    # A recognizer that skipped files at this size averages a different, easier set.
                    if not r or not r[metric] or (key in RECOGNIZERS and r["files_answered"] != r["files_planned"]):
                        continue
                    pts.append((px(s), py(float(r[metric]))))
                if len(pts) > 1:
                    d = " ".join(f"{'M' if i == 0 else 'L'}{a:.1f},{b:.1f}" for i, (a, b) in enumerate(pts))
                    el.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"'
                              + (f' stroke-dasharray="{dash}"/>' if dash else "/>"))
                for a, b in pts:
                    el.append(marker(kind, a, b, color))

            # Chance goes on top: at 25% most methods sit right on it and would hide it.
            # The stop rule answers every file, so its chance is each size's chance.
            pts = [(px(s), py(float(data[("stop-rule", fam, s, pct)]["chance"]))) for s in fs]
            d = " ".join(f"{'M' if i == 0 else 'L'}{a:.1f},{b:.1f}" for i, (a, b) in enumerate(pts))
            el.append(f'<path d="{d}" fill="none" stroke="{SURFACE}" stroke-width="5" stroke-opacity="0.8"/>')
            el.append(f'<path d="{d}" fill="none" stroke="{INK2}" stroke-width="2" stroke-dasharray="6 5"/>')

    files = [int(r["files_planned"]) for (m, *_), r in data.items() if m == "stop-rule"]
    foot = [f"Each point averages {min(files)}–{max(files)} evidence files. Recognizers appear only at sizes where "
            "they answered every file. MC-SAT did so only on",
            "SimpleGrid 3×3 and 4×4 and is left out. CLARA has no max-term records for ThreePackage or FourPackage. "
            "Intervals: results/clara/report.md."]
    el.append(text(40, H - 62, foot[0], 19, MUTED))
    el.append(text(40, H - 34, foot[1], 19, MUTED))
    el.append("</svg>")
    return "\n".join(el)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metric", choices=sorted(METRICS), default="p_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"clara_by_size_{args.metric}.svg"
    out.write_text(build(load(), args.metric))
    print(out)


if __name__ == "__main__":
    main()
