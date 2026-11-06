#!/usr/bin/env python3
"""LLMs as recognizers on the CLARA grids: one dot per (method, family, evidence level).

Reads results/clara/summary.csv (run `clara.py score` first) and writes
results/figures/clara_p_true.svg or clara_accuracy.svg. Stdlib only.

  python3 plot_clara.py                     # P(true)
  python3 plot_clara.py --metric accuracy   # accuracy (1/k for a k-way tie at the top)
"""

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SUMMARY = ROOT / "results" / "clara" / "summary.csv"
OUT = ROOT / "results" / "figures"

FAMILIES = [("SimpleGrid", "SimpleGrid", "2–9 goals"),
            ("TwoPackage", "TwoPackage", "4 goals"),
            ("TwoPackageOneway", "TwoPackageOneway", "4 goals"),
            ("ThreePackage", "ThreePackage", "8 goals"),
            ("FourPackage", "FourPackage", "12 goals")]
LEVELS = [(25, "25% of the plan observed", "the real test: no candidate goal is reached yet"),
          (100, "Whole plan observed", "the stop rule alone scores 1.0: each plan ends when its goal holds")]
# LLMs in fixed categorical order, then the cheapest-plan recognizer, then the no-model baseline.
METHODS = [
    ("gpt-6-luna", "gpt-6-luna", "#2a78d6", "circle"),
    ("gpt-5.4-mini", "gpt-5.4-mini", "#eb6834", "circle"),
    ("jev-latest", "Jev", "#1baf7a", "circle"),
    ("hf:Qwen/Qwen2.5-7B-Instruct", "Qwen2.5-7B", "#eda100", "circle"),
    ("hf:meta-llama/Meta-Llama-3-8B-Instruct", "Llama-3-8B", "#e87ba4", "circle"),
    ("max-term", "max-term (recognizer)", "#1f1f1e", "square"),
    ("stop-rule", "stop rule (no model)", "#898781", "ring"),
]
METRICS = {"p_true": "P(true goal)", "accuracy": "Accuracy"}

INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"

LABEL_W = 270          # method names, left of the first column
PANEL_W, GAP = 250, 44
ROW_H = 40
PANEL_H = ROW_H * len(METHODS)
TOP = 340
BLOCK_GAP = 200
W = LABEL_W + len(FAMILIES) * PANEL_W + (len(FAMILIES) - 1) * GAP + 50
H = TOP + len(LEVELS) * PANEL_H + (len(LEVELS) - 1) * BLOCK_GAP + 160


def load():
    with SUMMARY.open() as f:
        return {(r["model"], r["family"], int(r["pct"])): r for r in csv.DictReader(f)}


def text(x, y, s, size=22, color=INK2, anchor="start", weight=400):
    s = s.replace("&", "&amp;").replace("<", "&lt;")
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{s}</text>')


def marker(kind, x, y, color, size=15):
    s = size / 2
    if kind == "ring":
        return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{s:.1f}" fill="{SURFACE}" stroke="{color}" stroke-width="3"/>'
    ring = f'stroke="{SURFACE}" stroke-width="2"'
    if kind == "square":
        return f'<rect x="{x - s:.1f}" y="{y - s:.1f}" width="{size}" height="{size}" rx="2" fill="{color}" {ring}/>'
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{s:.1f}" fill="{color}" {ring}/>'


def build(data, metric):
    el = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
          f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    el.append(text(40, 56, f"LLMs as recognizers on the CLARA grid benchmarks: {METRICS[metric]}", 34, INK, weight=600))
    el.append(text(40, 96, "Mean over evidence files; each LLM answered every file 3 times.", 21, INK2))
    el.append(text(40, 126, "Stems run from chance to the score, so a dot left of the dashed line is below chance.",
                   21, INK2))
    el.append(f'<line x1="40" y1="164" x2="80" y2="164" stroke="{INK2}" stroke-width="2" stroke-dasharray="6 5"/>')
    el.append(text(92, 171, "chance = 1 / number of candidate goals", 21, INK2))

    for bi, (pct, title, note) in enumerate(LEVELS):
        top = TOP + bi * (PANEL_H + BLOCK_GAP)
        el.append(text(40, top - 96, title, 28, INK, weight=600))
        el.append(text(40 + len(title) * 15 + 24, top - 96, note, 21, MUTED))

        for mi, (_, label, _, _) in enumerate(METHODS):
            el.append(text(LABEL_W - 24, top + (mi + 0.5) * ROW_H + 7, label, 21, INK, "end"))

        for fi, (fam, ftitle, fnote) in enumerate(FAMILIES):
            left = LABEL_W + fi * (PANEL_W + GAP)
            px = lambda v: left + v * PANEL_W
            el.append(text(left, top - 46, ftitle, 21, INK, weight=600))
            el.append(text(left, top - 20, fnote, 18, MUTED))

            # Recessive grid, a baseline axis and dotted row guides.
            for i in range(5):
                v = i / 4
                el.append(f'<line x1="{px(v):.1f}" y1="{top}" x2="{px(v):.1f}" y2="{top + PANEL_H}" '
                          f'stroke="{AXIS if i == 0 else GRID}" stroke-width="{2 if i == 0 else 1}"/>')
                el.append(text(px(v), top + PANEL_H + 28, f"{v:g}", 17, MUTED, "middle"))
            for mi in range(1, len(METHODS)):
                y = top + mi * ROW_H
                el.append(f'<line x1="{left}" y1="{y}" x2="{left + PANEL_W}" y2="{y}" stroke="{GRID}" '
                          f'stroke-width="1" stroke-dasharray="1 4"/>')

            # The stop rule answers every file, so its chance is the panel's chance.
            chance = float(data[("stop-rule", fam, pct)]["chance"])
            el.append(f'<line x1="{px(chance):.1f}" y1="{top - 4}" x2="{px(chance):.1f}" y2="{top + PANEL_H}" '
                      f'stroke="{INK2}" stroke-width="2" stroke-dasharray="6 5"/>')

            for mi, (key, _, color, kind) in enumerate(METHODS):
                y = top + (mi + 0.5) * ROW_H
                r = data.get((key, fam, pct))
                if not r or not r[metric]:
                    el.append(text(px(chance) + 10, y + 6, "no results", 17, MUTED))
                    continue
                v = float(r[metric])
                el.append(f'<line x1="{px(chance):.1f}" y1="{y:.1f}" x2="{px(v):.1f}" y2="{y:.1f}" '
                          f'stroke="{color}" stroke-width="2" stroke-opacity="0.45"/>')
                el.append(marker(kind, px(v), y, color))

    foot = ["CLARA has no max-term records for ThreePackage or FourPackage. SharpSAT-TD and MC-SAT solved only some "
            "small grids, so they are left out here",
            "and compared with each LLM on shared files in results/clara/report.md, which also gives 95% intervals."]
    el.append(text(40, H - 62, foot[0], 19, MUTED))
    el.append(text(40, H - 34, foot[1], 19, MUTED))
    el.append("</svg>")
    return "\n".join(el)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metric", choices=sorted(METRICS), default="p_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"clara_{args.metric}.svg"
    out.write_text(build(load(), args.metric))
    print(out)


if __name__ == "__main__":
    main()
