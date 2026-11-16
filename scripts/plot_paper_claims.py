#!/usr/bin/env python3
"""Draw the paper-side C1–C6 comparison figures from PROTOCOL.md Table 1.

The source values are from Kumar, Imran and Kosar, Table 1
(https://arxiv.org/html/2511.08644). The paper does not give per-row confidence
intervals in that table, so these figures show point values only. No benchmark
or local measurement is run by this script.

Reproduce with:
  uv run --no-project --python 3.12.14 --with matplotlib==3.11.2 \
    python scripts/plot_paper_claims.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from plot_claims import COLORS, LIBRARIES

plt.rcParams["svg.fonttype"] = "none"

ROOT = Path(__file__).resolve().parents[1]
TITLES = {
    "C1": "Insurance / Random Forest",
    "C2": "MovieLens-1M / CF",
    "C3": "Insurance / SVR",
    "C4": "Insurance / XGBoost",
    "C5": "Insurance / TabNet",
    "C6": "MovieLens-1M / NCF",
}


def paper_values(protocol: Path) -> dict[str, dict[str, dict[str, float]]]:
    """Read the six three-backend rows in the protocol's paper-value table."""
    values: dict[str, dict[str, dict[str, float]]] = {claim: {} for claim in TITLES}
    for line in protocol.read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 7 or cells[0] not in TITLES:
            continue
        claim, _, _, backend, _, cpu, gpu = cells
        library = backend.lower()
        if library not in LIBRARIES or library in values[claim]:
            raise ValueError(f"Unexpected or duplicate paper row: {line}")
        values[claim][library] = {
            "cpu": float(cpu.replace(",", "")),
            "gpu": float(gpu.replace(",", "")),
        }
    for claim, rows in values.items():
        if set(rows) != set(LIBRARIES):
            raise ValueError(f"Missing paper values for {claim}: {rows}")
    return values


def panel(fig, box, title, values, domain):
    left, bottom, width, height = box
    border = FancyBboxPatch(
        (left, bottom), width, height,
        boxstyle="round,pad=0.006,rounding_size=0.012",
        transform=fig.transFigure, fill=False, linewidth=0.8,
        edgecolor="#d1d5db",
    )
    fig.add_artist(border)
    fig.text(left + 0.025, bottom + height - 0.07, title,
             fontsize=13, fontweight="bold", color="#111827")

    ax = fig.add_axes((left + 0.095, bottom + 0.14, width - 0.23, height - 0.26))
    maximum = max(values.values())
    ax.set_xlim(0, maximum * 1.12)
    ax.set_ylim(-0.5, 2.5)
    ax.set_yticks((2, 1, 0))
    ax.set_yticklabels((name.title() for name in LIBRARIES), fontsize=11)
    ax.set_xlabel(f"Paper {domain} energy (J)", fontsize=10,
                  color="#475569", labelpad=10)
    ax.grid(axis="x", color="#e5e7eb", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", labelsize=9, colors="#475569", length=0, pad=8)
    ax.tick_params(axis="y", colors="#111827", length=0, pad=8)
    for spine in ax.spines.values():
        spine.set_visible(False)

    for y, library in zip((2, 1, 0), LIBRARIES):
        value = values[library]
        ax.plot(value, y, "o", color=COLORS[library], markersize=9,
                markeredgecolor="white", markeredgewidth=1, zorder=3)
        ax.text(1.035, y, f"{value:,.2f} J",
                transform=ax.get_yaxis_transform(), va="center", ha="left",
                fontsize=10, color="#111827")


def figure(claim, rows, output, domains=None):
    domains = domains or (("cpu", "gpu") if claim == "C6" else ("cpu",))
    wide = len(domains) == 2
    fig = plt.figure(figsize=(12 if wide else 8, 4.25), facecolor="white")
    fig.text(0.5, 0.93, f"{claim} · {TITLES[claim]}", ha="center",
             fontsize=17, fontweight="bold", color="#111827")
    fig.text(0.5, 0.865, "Paper · Table 1 point values; confidence intervals not reported per row",
             ha="center", fontsize=10, color="#475569")
    boxes = ((0.025, 0.115, 0.46, 0.66), (0.515, 0.115, 0.46, 0.66)) if wide \
            else ((0.035, 0.115, 0.93, 0.66),)
    for box, domain in zip(boxes, domains):
        title = "CPU: core + RAM" if domain == "cpu" else "GPU: V100 power rails"
        panel(fig, box, title, {name: rows[name][domain] for name in LIBRARIES},
              domain.upper())
    svg_path = output.with_suffix(".svg")
    fig.savefig(svg_path, format="svg", facecolor="white")
    svg_path.write_text("\n".join(line.rstrip() for line in
                                  svg_path.read_text(encoding="utf-8").splitlines()) + "\n",
                        encoding="utf-8")
    fig.savefig(output.with_suffix(".png"), format="png", dpi=160,
                facecolor="white")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=ROOT / "PROTOCOL.md")
    parser.add_argument("--output-dir", type=Path,
                        default=ROOT / "results/analysis/claim_figures")
    args = parser.parse_args()
    values = paper_values(args.protocol)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for claim, rows in values.items():
        figure(claim, rows, args.output_dir / f"claim_{claim}_paper")
        print(f"Wrote claim_{claim}_paper.svg and .png")
    for domain in ("cpu", "gpu"):
        figure("C6", values["C6"], args.output_dir / f"claim_C6_{domain}_paper",
               (domain,))
        print(f"Wrote claim_C6_{domain}_paper.svg and .png")


if __name__ == "__main__":
    main()
