#!/usr/bin/env python3
"""Next-action estimators compared: one dot per (estimator, model), per metric.

Reads results/nextaction/summary.csv (run `nextaction.py score` first) and
writes results/figures/estimators.svg. Stdlib only.

  python3 plot_estimators.py           # pure-LLM distributions
  python3 plot_estimators.py --masked  # the same, renormalized onto applicable actions
"""

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SUMMARY = ROOT / "results" / "nextaction" / "summary.csv"
OUT = ROOT / "results" / "figures"

DOMAINS = [("blockwords", "BlockWords", "10 decision points · 128 actions"),
           ("intrusion", "IntrusionDetection", "20 decision points · 90 actions")]
ESTIMATORS = [
    ("verbalized", "Verbalized (1 answer)"),
    ("verbalized-mean", "Verbalized (mean of 3)"),
    ("sampling", "Sampling (K = 10)"),
    ("nexttoken", "Next-token"),
    ("nexttoken-preamble", "Next-token + preamble"),
]
MODELS = [
    ("hf:Qwen/Qwen2.5-7B-Instruct", "Qwen2.5-7B-Instruct", "#2a78d6", "circle"),
    ("hf:meta-llama/Meta-Llama-3-8B-Instruct", "Llama-3-8B-Instruct", "#eb6834", "diamond"),
]
# (column, title, direction note, axis max, tick step)
METRICS = [
    ("top5", "Top-5 accuracy", "higher is better", 1.0, 0.25),
    ("nll", "NLL of true action", "lower is better", 10.0, 2.5),
    ("ece", "ECE", "lower is better", 1.0, 0.25),
    ("invalid", "Invalid mass", "lower is better", 1.0, 0.25),
]
BASELINES = [("uniform-applicable", "uniform over applicable", "#52514e", "8 5"),
             ("uniform-all", "uniform over all", "#898781", "2 5")]

INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"

LABEL_W = 330          # estimator names, left of the first column
PANEL_W, GAP = 330, 60
ROW_H = 58
PANEL_H = ROW_H * len(ESTIMATORS)
TOP = 270
BLOCK_GAP = 190
W = LABEL_W + len(METRICS) * PANEL_W + (len(METRICS) - 1) * GAP + 60
H = TOP + len(DOMAINS) * PANEL_H + (len(DOMAINS) - 1) * BLOCK_GAP + 150


def load():
    data = {}
    with SUMMARY.open() as f:
        for r in csv.DictReader(f):
            data[(r["estimator"], r["model"], r["masked"] == "True", r["domain"])] = r
    return data


def text(x, y, s, size=22, color=INK2, anchor="start", weight=400):
    s = s.replace("&", "&amp;").replace("<", "&lt;")
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{s}</text>')


def marker(kind, x, y, color, size=15):
    s = size / 2
    ring = f'stroke="{SURFACE}" stroke-width="2"'
    if kind == "circle":
        return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{s:.1f}" fill="{color}" {ring}/>'
    s *= 1.3
    pts = [(x, y - s), (x + s, y), (x, y + s), (x - s, y)]
    return f'<polygon points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}" fill="{color}" {ring}/>'


def fmt_tick(v):
    return str(int(v)) if v == int(v) else f"{v:g}"


def build(data, masked):
    el = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
          f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']

    title = ("Next-action uncertainty estimators" +
             (": renormalized onto applicable actions" if masked else ": pure-LLM distributions"))
    el.append(text(40, 56, title, 34, INK, weight=600))

    # Legend row: models, then baselines.
    x = 40
    for _, label, color, kind in MODELS:
        el.append(marker(kind, x + 9, 104, color, 16))
        el.append(text(x + 28, 112, label, 23, INK))
        x += 28 + len(label) * 12 + 50
    for _, label, color, dash in BASELINES:
        el.append(f'<line x1="{x}" y1="104" x2="{x + 40}" y2="104" stroke="{color}" stroke-width="2" stroke-dasharray="{dash}"/>')
        el.append(text(x + 52, 112, label, 23, INK2))
        x += 52 + len(label) * 11.5 + 50

    for bi, (dom, dom_title, dom_note) in enumerate(DOMAINS):
        top = TOP + bi * (PANEL_H + BLOCK_GAP)
        el.append(text(40, top - 62, dom_title, 28, INK, weight=600))
        el.append(text(LABEL_W, top - 62, dom_note, 22, MUTED))

        for ei, (_, est_label) in enumerate(ESTIMATORS):
            y = top + (ei + 0.5) * ROW_H
            el.append(text(LABEL_W - 24, y + 8, est_label, 22, INK, "end"))

        for mi, (key, mtitle, note, vmax, step) in enumerate(METRICS):
            left = LABEL_W + mi * (PANEL_W + GAP)
            px = lambda v: left + min(v, vmax) / vmax * PANEL_W
            el.append(text(left, top - 22, mtitle, 22, INK, weight=600))
            el.append(text(left + PANEL_W, top - 22, note, 18, MUTED, "end"))

            # Recessive grid and a baseline axis.
            n_ticks = int(round(vmax / step))
            for i in range(n_ticks + 1):
                v = i * step
                el.append(f'<line x1="{px(v):.1f}" y1="{top}" x2="{px(v):.1f}" y2="{top + PANEL_H}" '
                          f'stroke="{AXIS if i == 0 else GRID}" stroke-width="{2 if i == 0 else 1}"/>')
                el.append(text(px(v), top + PANEL_H + 30, fmt_tick(v), 18, MUTED, "middle"))
            for ei in range(1, len(ESTIMATORS)):
                y = top + ei * ROW_H
                el.append(f'<line x1="{left}" y1="{y}" x2="{left + PANEL_W}" y2="{y}" stroke="{GRID}" stroke-width="1" stroke-dasharray="1 4"/>')

            for bkey, _, color, dash in BASELINES:
                r = data.get(("baseline", bkey, False, dom))
                if r and r[key]:
                    v = float(r[key])
                    el.append(f'<line x1="{px(v):.1f}" y1="{top - 6}" x2="{px(v):.1f}" y2="{top + PANEL_H}" '
                              f'stroke="{color}" stroke-width="2" stroke-dasharray="{dash}"/>')

            for ei, (est, _) in enumerate(ESTIMATORS):
                yc = top + (ei + 0.5) * ROW_H
                for k, (mkey, _, color, kind) in enumerate(MODELS):
                    r = data.get((est, mkey, masked, dom))
                    if not r or not r[key]:
                        continue
                    v = float(r[key])
                    y = yc + (k - 0.5) * 18
                    el.append(f'<line x1="{px(0):.1f}" y1="{y:.1f}" x2="{px(v):.1f}" y2="{y:.1f}" '
                              f'stroke="{color}" stroke-width="2" stroke-opacity="0.35"/>')
                    el.append(marker(kind, px(v), y, color))
                    if v > vmax:
                        el.append(text(px(vmax) - 4, y - 10, f"{v:.1f}", 16, INK2, "end"))

    foot = ["Means over decision points of the reference plan. Every estimator scores all grounded actions, "
            "applicable or not; invalid mass = probability on actions whose preconditions are false.",
            "NLL mixes 1% uniform mass into every estimator, so a zero-probability miss stays finite."]
    if masked:
        foot[0] = ("Same outputs renormalized onto the actions applicable in the true current state "
                   "(the constraint ablation), so invalid mass is 0 by construction.")
    el.append(text(40, H - 62, foot[0], 19, MUTED))
    el.append(text(40, H - 34, foot[1], 19, MUTED))
    el.append("</svg>")
    return "\n".join(el)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--masked", action="store_true", help="plot the +mask (applicable-only) rows")
    args = ap.parse_args()
    data = load()
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / ("estimators_masked.svg" if args.masked else "estimators.svg")
    out.write_text(build(data, args.masked))
    print(out)


if __name__ == "__main__":
    main()
