#!/usr/bin/env python3
"""P(true goal) vs. number of observations: FiFO-R&G against the LLMs.

Reads results/summary.csv (run `bench.py score` first) and writes SVGs to
results/figures/. Stdlib only.

  python3 plot_curves.py                        # all models
  python3 plot_curves.py --exclude gpt-5.5@high # match a slide that omits it
"""

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SUMMARY = ROOT / "results" / "summary.csv"
OUT = ROOT / "results" / "figures"

DOMAINS = [("blockwords", "BlockWords", 21), ("intrusion", "IntrusionDetection", 10)]

# Reference (FiFO) first, then LLMs in fixed categorical order.
SERIES = [
    ("baseline:FiFO-R&G", "FiFO-R&G", "#1f1f1e", "square"),
    ("gpt-4.1", "gpt-4.1", "#2a78d6", "circle"),
    ("gpt-5.4-mini", "gpt-5.4-mini", "#eb6834", "triangle"),
    ("gpt-5.4-mini@high", "gpt-5.4-mini@high", "#1baf7a", "diamond"),
    ("gpt-5.5@high", "gpt-5.5@high", "#eda100", "down"),
    ("jev-latest", "Jev", "#8a4fd3", "diamond"),
    ("hf:Qwen/Qwen2.5-7B-Instruct", "Qwen2.5-7B", "#d23f7a", "circle"),
    ("hf:meta-llama/Meta-Llama-3-8B-Instruct", "Llama-3-8B", "#3b9fb8", "triangle"),
]

INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"

W, H = 1800, 920
PANEL_W, PANEL_H = 700, 520
PANEL_TOP = 220
PANEL_LEFT = [110, 1000]
YMAX = 1.0


def load():
    data = {}
    with SUMMARY.open() as f:
        for r in csv.DictReader(f):
            if r["p_true"]:
                data[(r["model"], r["domain"], int(r["k"]))] = float(r["p_true"])
    return data


def marker(kind, x, y, color, size):
    s = size / 2
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


def text(x, y, s, size=26, color=INK2, anchor="start", weight=400):
    s = s.replace("&", "&amp;").replace("<", "&lt;")
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{s}</text>')


def build(data, series):
    el = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
          f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']

    # Legend across the top, wrapping onto a second row when it runs out of width.
    x, y = PANEL_LEFT[0], 60
    for _, label, color, kind in series:
        w = 4 if label.startswith("FiFO") else 3
        name = label + (" (ours)" if label.startswith("FiFO") else "")
        if x + 56 + len(name) * 14 > W - 40:
            x, y = PANEL_LEFT[0], y + 46
        el.append(f'<line x1="{x}" y1="{y}" x2="{x + 44}" y2="{y}" stroke="{color}" stroke-width="{w}"/>')
        el.append(marker(kind, x + 22, y, color, 14 if label.startswith("FiFO") else 12))
        el.append(text(x + 56, y + 9, name, 26, INK, weight=600 if label.startswith("FiFO") else 400))
        x += 56 + len(name) * 14 + 44
    if x + 56 + 13 * 14 > W - 40:
        x, y = PANEL_LEFT[0], y + 46
    el.append(f'<line x1="{x}" y1="{y}" x2="{x + 44}" y2="{y}" stroke="{MUTED}" stroke-width="2" stroke-dasharray="6 6"/>')
    el.append(text(x + 56, y + 9, "uniform guess", 26, INK2))

    for (dom, title, n_goals), left in zip(DOMAINS, PANEL_LEFT):
        top = PANEL_TOP
        px = lambda k: left + (k - 1) / 4 * PANEL_W
        py = lambda p: top + (1 - p / YMAX) * PANEL_H

        el.append(text(left, top - 50, title, 32, INK, weight=600))
        el.append(text(left + PANEL_W, top - 50, f"{n_goals} candidate goals", 26, MUTED, "end"))

        for t in [i * 0.25 for i in range(int(round(YMAX / 0.25)) + 1)]:
            y = py(t)
            color = AXIS if t == 0 else GRID
            el.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + PANEL_W}" y2="{y:.1f}" stroke="{color}" stroke-width="{2 if t == 0 else 1}"/>')
            el.append(text(left - 16, y + 9, f"{t:.2f}".rstrip("0").rstrip(".") if t not in (0, 1) else str(int(t)), 24, MUTED, "end"))
        for k in range(1, 6):
            el.append(text(px(k), top + PANEL_H + 40, str(k), 24, MUTED, "middle"))
        el.append(text(left + PANEL_W / 2, top + PANEL_H + 86, "Number of observed actions", 26, INK2, "middle"))
        if left == PANEL_LEFT[0]:
            el.append(f'<text transform="translate({left - 78},{top + PANEL_H / 2}) rotate(-90)" font-family="{FONT}" '
                      f'font-size="26" fill="{INK2}" text-anchor="middle">P(true goal)</text>')

        chance = 1 / n_goals
        el.append(f'<line x1="{left}" y1="{py(chance):.1f}" x2="{left + PANEL_W}" y2="{py(chance):.1f}" '
                  f'stroke="{MUTED}" stroke-width="2" stroke-dasharray="6 6"/>')

        # LLMs first, FiFO last so it paints on top.
        for key, label, color, kind in series[1:] + series[:1]:
            pts = [(k, data[(key, dom, k)]) for k in range(1, 6) if (key, dom, k) in data]
            if not pts:
                continue
            fifo = label.startswith("FiFO")
            d = " ".join(f"{'M' if i == 0 else 'L'}{px(k):.1f},{py(p):.1f}" for i, (k, p) in enumerate(pts))
            el.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{4 if fifo else 3}" '
                      f'stroke-linejoin="round" stroke-linecap="round"/>')
            for k, p in pts:
                el.append(marker(kind, px(k), py(p), color, 16 if fifo else 13))
            if fifo:
                k, p = pts[-1]
                el.append(text(px(k) + 18, py(p) + 9, f"{p:.2f}", 26, INK, weight=600))

    el.append(text(PANEL_LEFT[0], H - 24,
                   "LLM points: mean of 3 runs. FiFO-R&G was computed at 1, 3 and 5 observations.", 24, MUTED))
    el.append("</svg>")
    return "\n".join(el)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exclude", nargs="*", default=[], help="model keys to leave out")
    ap.add_argument("--out", default=None, help="output file name (default depends on --exclude)")
    ap.add_argument("--ymax", type=float, default=1.0, help="top of the y axis (a multiple of 0.25)")
    args = ap.parse_args()
    global YMAX
    YMAX = args.ymax
    data = load()
    top_value = max(v for (m, _, _), v in data.items() if m in {s[0] for s in SERIES} - set(args.exclude))
    if top_value > YMAX:
        raise SystemExit(f"--ymax {YMAX} would clip a point at {top_value:.2f}")
    # Models without results yet are left out of the plot and the legend.
    series = [s for s in SERIES if s[0] not in args.exclude and any(m == s[0] for m, _, _ in data)]
    name = args.out or ("p_true_curves.svg" if not args.exclude else "p_true_curves_" + "_".join(
        e.replace("@", "-").replace(".", "") for e in args.exclude).replace("gpt-", "no-gpt-") + ".svg")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(build(data, series))
    print(OUT / name)


if __name__ == "__main__":
    main()
