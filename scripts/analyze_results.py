#!/usr/bin/env python3
"""Audit measured runs and summarize CPU package energy."""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from statistics import fmean, median, stdev

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SESSION = REPO_ROOT / "results/raw/full-20261025-135703-JICxLk"
LIBRARIES = ("pandas", "polars", "dask")
DATASETS = ("insurance", "ml-1m")
STAGES = ("data", "full")
CONFIGURATIONS = tuple(product(LIBRARIES, DATASETS, STAGES))
IDENTITY_FIELDS = ("sequence", "kind", "round", "lib", "dataset", "stage")
RUN_FIELDS = set(IDENTITY_FIELDS) | {
    "run_id", "exit_code", "energy_pkg_j", "energy_cores_j",
    "elapsed_s", "max_rss_kb", "status",
}
SUMMARY_FIELDS = (
    "dataset", "library", "stage", "n", "median_net_j", "q1_net_j",
    "q3_net_j", "iqr_net_j", "trimmed_mean_net_j", "ci95_low_net_j",
    "ci95_high_net_j", "cv_net_pct", "median_runtime_s", "q1_runtime_s",
    "q3_runtime_s", "iqr_runtime_s", "ci95_low_runtime_s",
    "ci95_high_runtime_s", "median_peak_rss_mib",
)


@dataclass(frozen=True)
class MeasuredRun:
    library: str
    dataset: str
    stage: str
    round_number: int
    net_energy_j: float
    elapsed_s: float
    peak_rss_kb: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "session_dir", type=Path, nargs="?", default=DEFAULT_SESSION,
        help="Full measurement session directory.",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=REPO_ROOT / "results/analysis",
        help="Directory for derived analysis files.",
    )
    return parser.parse_args()


def read_idle_power(session_dir: Path) -> float:
    path = session_dir / "idle/idle_power_w.txt"
    try:
        value = float(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError) as error:
        raise ValueError(f"Cannot read idle power: {path}") from error
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"Invalid idle power: {value}")
    return value


def read_csv_rows(path: Path, required_fields: set[str]) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8") as source:
            reader = csv.DictReader(source)
            missing = required_fields - set(reader.fieldnames or ())
            if missing:
                raise ValueError(f"Missing columns in {path}: {sorted(missing)}")
            rows = list(reader)
    except OSError as error:
        raise ValueError(f"Cannot read CSV: {path}") from error
    if not rows:
        raise ValueError(f"Empty CSV: {path}")
    return rows


def audit_session(session_dir: Path) -> tuple[float, list[MeasuredRun]]:
    status_path = session_dir / "session_status.txt"
    try:
        status = status_path.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise ValueError(f"Cannot read session status: {status_path}") from error
    if status != "COMPLETE":
        raise ValueError(f"Session is not complete: {status}")

    idle_power_w = read_idle_power(session_dir)
    schedule = read_csv_rows(session_dir / "schedule.csv", set(IDENTITY_FIELDS))
    runs = read_csv_rows(session_dir / "runs.csv", RUN_FIELDS)
    if len(schedule) != 132 or len(runs) != 132:
        raise ValueError(
            f"Expected 132 scheduled and recorded runs, got {len(schedule)} and {len(runs)}"
        )

    warmups: set[tuple[str, str, str]] = set()
    measured_keys: set[tuple[int, str, str, str]] = set()
    measured: list[MeasuredRun] = []
    for sequence, (planned, row) in enumerate(zip(schedule, runs, strict=True), start=1):
        if any(planned[field] != row[field] for field in IDENTITY_FIELDS):
            raise ValueError(f"Schedule mismatch at sequence {sequence}")
        if int(row["sequence"]) != sequence:
            raise ValueError(f"Sequence mismatch at row {sequence}")
        if row["status"] != "OK" or row["exit_code"] != "0":
            raise ValueError(f"Failed run retained at sequence {sequence}: {row['status']}")

        configuration = (row["lib"], row["dataset"], row["stage"])
        if configuration not in CONFIGURATIONS:
            raise ValueError(f"Unknown configuration at sequence {sequence}: {configuration}")
        run_dir = session_dir / "runs" / row["run_id"]
        if any(
            not (run_dir / name).is_file()
            for name in ("perf.csv", "time.txt", "stdout.txt", "stderr.txt")
        ):
            raise ValueError(f"Missing raw file at sequence {sequence}: {run_dir}")

        try:
            round_number = int(row["round"])
            energy_pkg_j = float(row["energy_pkg_j"])
            energy_cores_j = float(row["energy_cores_j"])
            elapsed_s = float(row["elapsed_s"])
            peak_rss_kb = int(row["max_rss_kb"])
        except ValueError as error:
            raise ValueError(f"Invalid number at sequence {sequence}") from error
        if not all(
            math.isfinite(value) and value > 0
            for value in (energy_pkg_j, energy_cores_j, elapsed_s)
        ):
            raise ValueError(f"Non-positive or non-finite measurement at sequence {sequence}")
        if peak_rss_kb <= 0:
            raise ValueError(f"Invalid peak RSS at sequence {sequence}")

        if row["kind"] == "warmup" and round_number == 0:
            if configuration in warmups:
                raise ValueError(f"Duplicate warm-up: {configuration}")
            warmups.add(configuration)
        elif row["kind"] == "measured" and 1 <= round_number <= 10:
            key = (round_number, *configuration)
            if key in measured_keys:
                raise ValueError(f"Duplicate measured run: {key}")
            measured_keys.add(key)
            measured.append(
                MeasuredRun(
                    library=row["lib"], dataset=row["dataset"], stage=row["stage"],
                    round_number=round_number,
                    net_energy_j=energy_pkg_j - idle_power_w * elapsed_s,
                    elapsed_s=elapsed_s, peak_rss_kb=peak_rss_kb,
                )
            )
        else:
            raise ValueError(f"Invalid kind or round at sequence {sequence}")

    expected_measured = {
        (round_number, *configuration)
        for round_number in range(1, 11)
        for configuration in CONFIGURATIONS
    }
    if warmups != set(CONFIGURATIONS) or measured_keys != expected_measured:
        raise ValueError("Warm-ups or measured configurations are incomplete")
    return idle_power_w, measured


def quartiles(values: list[float]) -> tuple[float, float]:
    q1, q3 = np.quantile(values, (0.25, 0.75), method="linear")
    return float(q1), float(q3)


def trimmed_mean_10pct(values: list[float]) -> float:
    if len(values) != 10:
        raise ValueError("The 10% trimmed mean requires 10 measured runs")
    return fmean(sorted(values)[1:-1])


def bootstrap_median_ci(values: list[float]) -> tuple[float, float]:
    samples = np.asarray(values, dtype=float)
    rng = np.random.default_rng(42)
    indices = rng.integers(0, len(samples), size=(10_000, len(samples)))
    medians = np.median(samples[indices], axis=1)
    low, high = np.quantile(medians, (0.025, 0.975), method="linear")
    return float(low), float(high)


def summarize_measured_runs(measured: list[MeasuredRun]) -> list[dict[str, str | int | float]]:
    grouped: dict[tuple[str, str, str], list[MeasuredRun]] = {}
    for run in measured:
        key = (run.library, run.dataset, run.stage)
        grouped.setdefault(key, []).append(run)

    rows: list[dict[str, str | int | float]] = []
    for library, dataset, stage in CONFIGURATIONS:
        group = grouped.get((library, dataset, stage), [])
        if len(group) != 10:
            raise ValueError(f"Expected 10 measured runs for {library}/{dataset}/{stage}")
        energy = [run.net_energy_j for run in group]
        runtime = [run.elapsed_s for run in group]
        mean_energy = fmean(energy)
        if mean_energy <= 0:
            raise ValueError(f"Non-positive mean net energy for {library}/{dataset}/{stage}")
        cv_pct = 100 * stdev(energy) / mean_energy
        if cv_pct > 10:
            raise ValueError(f"Net energy CV exceeds 10% for {library}/{dataset}/{stage}")
        q1_energy, q3_energy = quartiles(energy)
        q1_runtime, q3_runtime = quartiles(runtime)
        low_energy, high_energy = bootstrap_median_ci(energy)
        low_runtime, high_runtime = bootstrap_median_ci(runtime)
        rows.append({
            "dataset": dataset,
            "library": library,
            "stage": stage,
            "n": len(group),
            "median_net_j": median(energy),
            "q1_net_j": q1_energy,
            "q3_net_j": q3_energy,
            "iqr_net_j": q3_energy - q1_energy,
            "trimmed_mean_net_j": trimmed_mean_10pct(energy),
            "ci95_low_net_j": low_energy,
            "ci95_high_net_j": high_energy,
            "cv_net_pct": cv_pct,
            "median_runtime_s": median(runtime),
            "q1_runtime_s": q1_runtime,
            "q3_runtime_s": q3_runtime,
            "iqr_runtime_s": q3_runtime - q1_runtime,
            "ci95_low_runtime_s": low_runtime,
            "ci95_high_runtime_s": high_runtime,
            "median_peak_rss_mib": median(run.peak_rss_kb / 1024 for run in group),
        })
    return rows


def write_summary(rows: list[dict[str, str | int | float]], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "summary.csv"
    with path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=SUMMARY_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return path


def main() -> None:
    args = parse_args()
    try:
        idle_power_w, measured = audit_session(args.session_dir)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    rows = summarize_measured_runs(measured)
    output_dir = args.output_dir.resolve()
    if output_dir == args.session_dir.resolve() or args.session_dir.resolve() in output_dir.parents:
        raise SystemExit("The output directory must be outside the raw session")
    summary_path = write_summary(rows, output_dir)
    manual_group = [
        run.net_energy_j for run in measured
        if (run.library, run.dataset, run.stage) == ("pandas", "insurance", "full")
    ]
    print(f"Session audit: 12 warm-ups and {len(measured)} measured runs complete")
    print(f"Idle package power: {idle_power_w:.6f} W")
    print(f"Pandas / Insurance / full median: {median(manual_group):.7f} J")
    print(f"Wrote {len(rows)} configurations to {summary_path}")


if __name__ == "__main__":
    main()
