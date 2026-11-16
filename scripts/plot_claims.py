#!/usr/bin/env python3
"""Draw C1-C6 median/95% CI figures from the committed analysis CSVs.

Reproduce with:
  uv run --no-project --python 3.12.14 --with matplotlib==3.11.2 \
    python scripts/plot_claims.py

C1-C2 use the session-1 summary; C3-C6 use current-stack session 2.
The figures show measured results, not simulated values or paper joules.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

plt.rcParams["svg.fonttype"] = "none"  # Keep figure labels as searchable text.


ROOT = Path(__file__).resolve().parents[1]
LIBRARIES = ("pandas", "polars", "dask")
COLORS = {"pandas": "#2563eb", "polars": "#059669", "dask": "#ea580c"}
SESSION1 = ROOT / "results/analysis/summary.csv"
SESSION2 = ROOT / "results/analysis/session2-20261116-012318-MJNiIT/summary.csv"
OUTPUT = ROOT / "results/analysis/claim_figures"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def estimates(rows: list[dict[str, str]], filters: dict[str, str],
              fields: tuple[str, str, str]) -> dict[str, tuple[float, float, float]]:
    """Get one median and CI per library; fail instead of silently omitting data."""
    result = {}
    for library in LIBRARIES:
        matches = [row for row in rows if row["library"] == library and
                   all(row[key] == value for key, value in filters.items())]
        if len(matches) != 1:
            raise ValueError(f"Expected one {library} row for {filters}, found {len(matches)}")
        median, low, high = (float(matches[0][field]) for field in fields)
        if not low <= median <= high:
            raise ValueError(f"Invalid confidence interval for {library}: {filters}")
        result[library] = (median, low, high)
    return result


def panel(fig, box: tuple[float, float, float, float], title: str,
          values: dict[str, tuple[float, float, float]], xlim: tuple[float, float],
          ticks: tuple[float, ...], xlabel: str) -> None:
    """Draw one panel in the style of the existing session-1 dot/CI figure."""
    left, bottom, width, height = box
    border = FancyBboxPatch((left, bottom), width, height,
                            boxstyle="round,pad=0.006,rounding_size=0.012",
                            transform=fig.transFigure, fill=False, linewidth=0.8,
                            edgecolor="#d1d5db")
    fig.add_artist(border)
    fig.text(left + 0.025, bottom + height - 0.07, title,
             fontsize=13, fontweight="bold", color="#111827")

    ax = fig.add_axes((left + 0.095, bottom + 0.14, width - 0.23, height - 0.26))
    ax.set_xlim(*xlim)
    ax.set_ylim(-0.5, 2.5)
    ax.set_xticks(ticks)
    ax.set_yticks((2, 1, 0))
    ax.set_yticklabels((name.title() for name in LIBRARIES), fontsize=11)
    ax.set_xlabel(xlabel, fontsize=10, color="#475569", labelpad=10)
    ax.grid(axis="x", color="#e5e7eb", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", labelsize=9, colors="#475569", length=0, pad=8)
    ax.tick_params(axis="y", colors="#111827", length=0, pad=8)
    for spine in ax.spines.values():
        spine.set_visible(False)

    for y, library in zip((2, 1, 0), LIBRARIES):
        median, low, high = values[library]
        ax.errorbar(median, y, xerr=((median - low,), (high - median,)),
                    fmt="o", color=COLORS[library], ecolor=COLORS[library],
                    elinewidth=2.7, capsize=5, capthick=2,
                    markersize=9, markeredgecolor="white", markeredgewidth=1,
                    zorder=3)
        ax.text(1.035, y, f"{median:.2f} J", transform=ax.get_yaxis_transform(),
                va="center", ha="left", fontsize=10, color="#111827")


def figure(claim: str, subtitle: str, panels: list[tuple], output: Path) -> None:
    wide = len(panels) == 2
    fig = plt.figure(figsize=(12 if wide else 8, 4.25), facecolor="white")
    fig.text(0.5, 0.93, claim, ha="center", fontsize=17, fontweight="bold",
             color="#111827")
    fig.text(0.5, 0.865, subtitle, ha="center", fontsize=10, color="#475569")
    boxes = ((0.025, 0.115, 0.46, 0.66), (0.515, 0.115, 0.46, 0.66)) if wide \
            else ((0.035, 0.115, 0.93, 0.66),)
    for box, args in zip(boxes, panels):
        panel(fig, box, *args)
    svg_path = output.with_suffix(".svg")
    fig.savefig(svg_path, format="svg", facecolor="white")
    # Matplotlib writes spaces before newlines in SVG path data. Newlines remain
    # valid path separators, so remove only trailing whitespace for clean diffs.
    svg_path.write_text("\n".join(line.rstrip() for line in
                                  svg_path.read_text(encoding="utf-8").splitlines()) + "\n",
                        encoding="utf-8")
    fig.savefig(output.with_suffix(".png"), format="png", dpi=160, facecolor="white")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session1-summary", type=Path, default=SESSION1)
    parser.add_argument("--session2-summary", type=Path, default=SESSION2)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    first, second = read_rows(args.session1_summary), read_rows(args.session2_summary)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    old = ("median_net_j", "ci95_low_net_j", "ci95_high_net_j")
    cpu = ("median_cpu_net_j", "ci95_low_cpu_net_j", "ci95_high_cpu_net_j")
    gpu = ("median_gpu_net_j", "ci95_low_gpu_net_j", "ci95_high_gpu_net_j")

    specs = (
        ("C1 · Insurance / Random Forest", "Session 1 · full-stage CPU package energy · median of 10 runs; whiskers: 95% bootstrap CI",
         [("Insurance / Random Forest", estimates(first, {"dataset": "insurance", "stage": "full"}, old),
           (0, 30), (0, 10, 20, 30), "Net CPU package energy (J)")]),
        ("C2 · MovieLens-1M / TruncatedSVD", "Session 1 · full-stage CPU package energy · median of 10 runs; whiskers: 95% bootstrap CI",
         [("MovieLens-1M / TruncatedSVD", estimates(first, {"dataset": "ml-1m", "stage": "full"}, old),
           (0, 215), (0, 50, 100, 150, 200), "Net CPU package energy (J)")]),
        ("C3 · Insurance / SVR", "Session 2 · full-stage CPU package energy · median of 10 runs; whiskers: 95% bootstrap CI",
         [("Insurance / SVR", estimates(second, {"environment": "current", "dataset": "insurance", "model": "svr", "stage": "full"}, cpu),
           (0, 27), (0, 5, 10, 15, 20, 25), "Net CPU package energy (J)")]),
        ("C4 · Insurance / XGBoost", "Session 2 · full-stage CPU package energy · median of 10 runs; whiskers: 95% bootstrap CI",
         [("Insurance / XGBoost", estimates(second, {"environment": "current", "dataset": "insurance", "model": "xgboost", "stage": "full"}, cpu),
           (0, 30), (0, 10, 20, 30), "Net CPU package energy (J)")]),
        ("C5 · Insurance / TabNet", "Session 2 · full-stage CPU package energy · median of 10 runs; whiskers: 95% bootstrap CI · zoomed x-axis",
         [("Insurance / TabNet", estimates(second, {"environment": "current", "dataset": "insurance", "model": "tabnet", "stage": "full"}, cpu),
           (70, 86), (72, 76, 80, 84), "Net CPU package energy (J)")]),
        ("C6 · MovieLens-1M / NCF", "Session 2 · full stage · median of 10 runs; whiskers: 95% bootstrap CI · separate zoomed joule scales",
         [("CPU package energy", estimates(second, {"environment": "current", "dataset": "ml-1m", "model": "ncf", "stage": "full"}, cpu),
           (710, 890), (720, 760, 800, 840, 880), "Net CPU package energy (J)"),
          ("GPU board energy", estimates(second, {"environment": "current", "dataset": "ml-1m", "model": "ncf", "stage": "full"}, gpu),
           (225, 234), (226, 228, 230, 232, 234), "Net GPU board energy (J)")]),
    )
    for index, (title, subtitle, panels) in enumerate(specs, start=1):
        figure(title, subtitle, panels, args.output_dir / f"claim_C{index}")
        print(f"Wrote claim_C{index}.svg and claim_C{index}.png")


if __name__ == "__main__":
    main()
