#!/usr/bin/env python3
"""Audit and summarize only a complete session-2 measurement directory."""

from __future__ import annotations

import argparse
import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path

import numpy as np


LIBRARIES = ("pandas", "polars", "dask")


def configurations() -> set[tuple[str, str, str, str, str]]:
    result = set()
    for lib in LIBRARIES:
        result.update(("current", lib, "insurance", model, "full")
                      for model in ("rf", "svr", "xgboost", "tabnet"))
        result.update(("current", lib, "ml-1m", model, "full")
                      for model in ("svd", "ncf"))
        result.update({("current", lib, "insurance", "rf", "data"),
                       ("current", lib, "ml-1m", "svd", "data"),
                       ("legacy", lib, "insurance", "rf", "full"),
                       ("legacy", lib, "insurance", "rf", "data")})
    return result


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        result = list(csv.DictReader(file))
    if not result:
        raise ValueError(f"Empty CSV: {path}")
    return result


def numeric(value: str, label: str, *, positive: bool = False) -> float:
    try:
        number = float(value)
    except ValueError as error:
        raise ValueError(f"Invalid {label}: {value}") from error
    if not math.isfinite(number) or positive and number <= 0:
        raise ValueError(f"Invalid {label}: {value}")
    return number


def audit(session: Path) -> dict[tuple[str, str, str, str, str], list[dict[str, float]]]:
    if (session / "session_status.txt").read_text(encoding="utf-8").strip() != "COMPLETE":
        raise ValueError("Session is incomplete")
    required = ("requirements-current.lock", "requirements-legacy.lock", "environment.txt",
                "gpu_samples.csv", "gpu_windows.csv", "gpu_validation.txt", "input_sha256.txt")
    if any(not (session / name).is_file() for name in required):
        raise ValueError("Missing session environment or GPU evidence")
    if "status=PASS" not in (session / "gpu_validation.txt").read_text(encoding="utf-8").splitlines():
        raise ValueError("GPU validation did not pass")
    environment = (session / "environment.txt").read_text(encoding="utf-8")
    for name in ("python_current_executable", "python_current_realpath",
                 "python_legacy_executable", "python_legacy_realpath"):
        if not any(line.startswith(name + "=") and line.split("=", 1)[1]
                   for line in environment.splitlines()):
            raise ValueError(f"Missing {name} in environment log")
    idle_cpu = numeric((session / "idle/idle_power_w.txt").read_text().strip(), "CPU idle W", positive=True)
    idle_gpu = numeric((session / "gpu/gpu_idle_power_w.txt").read_text().strip(), "GPU idle W", positive=True)
    scheduled, recorded, gpu_rows = (rows(session / path) for path in
                                     ("schedule.csv", "runs.csv", "gpu/gpu_runs.csv"))
    if len(scheduled) != 330 or len(recorded) != 330 or len(gpu_rows) != 330:
        raise ValueError("Expected 30 warm-ups and 300 measured runs, each with GPU data")
    gpu_by_id = {row["run_id"]: row for row in gpu_rows}
    if len(gpu_by_id) != 330:
        raise ValueError("Duplicate GPU run ID")
    identity = ("sequence", "kind", "round", "environment", "lib", "dataset", "model", "stage")
    expected = configurations()
    warmups = set()
    measured_keys = set()
    grouped = defaultdict(list)
    for sequence, (plan, run) in enumerate(zip(scheduled, recorded), start=1):
        if any(plan[field] != run[field] for field in identity) or int(run["sequence"]) != sequence:
            raise ValueError(f"Schedule/record mismatch at row {sequence}")
        key = tuple(run[field] for field in identity[3:])
        if key not in expected or run["status"] != "OK" or run["exit_code"] != "0":
            raise ValueError(f"Invalid run at row {sequence}")
        run_id = run["run_id"]
        if run_id not in gpu_by_id or any(
            not (session / "runs" / run_id / name).is_file()
            for name in ("perf.csv", "time.txt", "stdout.txt", "stderr.txt")
        ):
            raise ValueError(f"Missing raw files at row {sequence}")
        gpu = gpu_by_id[run_id]
        if run["kind"] == "warmup" and run["round"] == "0":
            if key in warmups:
                raise ValueError(f"Repeated warm-up: {key}")
            warmups.add(key)
            continue
        if run["kind"] != "measured" or not 1 <= int(run["round"]) <= 10:
            raise ValueError(f"Invalid measured run at row {sequence}")
        measured_key = (int(run["round"]),) + key
        if measured_key in measured_keys:
            raise ValueError(f"Duplicate measured run: {measured_key}")
        measured_keys.add(measured_key)
        runtime = numeric(run["elapsed_s"], "elapsed_s", positive=True)
        values = {
            "cpu_net_j": numeric(run["energy_pkg_j"], "energy_pkg_j", positive=True) - idle_cpu * runtime,
            "gpu_net_j": numeric(gpu["gpu_net_j"], "gpu_net_j"),
            "runtime_s": runtime,
            "rss_mib": numeric(run["max_rss_kb"], "max_rss_kb", positive=True) / 1024,
        }
        if values["cpu_net_j"] <= 0:
            raise ValueError(f"Non-positive CPU net energy: {run_id}")
        grouped[key].append(values)
    if warmups != expected or measured_keys != {(round_no,) + key for round_no in range(1, 11) for key in expected}:
        raise ValueError("Incomplete session-2 configuration schedule")
    return grouped


def interval(values: list[float]) -> tuple[float, float]:
    rng = np.random.default_rng(42)
    array = np.asarray(values, dtype=float)
    indices = rng.integers(0, 10, size=(10_000, 10))
    return tuple(float(x) for x in np.quantile(np.median(array[indices], axis=1), (0.025, 0.975)))


def summarize(grouped: dict) -> list[dict[str, object]]:
    summaries = []
    for key in sorted(configurations()):
        values = grouped[key]
        row: dict[str, object] = dict(zip(("environment", "library", "dataset", "model", "stage"), key))
        for metric in ("cpu_net_j", "gpu_net_j", "runtime_s", "rss_mib"):
            series = [item[metric] for item in values]
            row[f"median_{metric}"] = statistics.median(series)
            row[f"q1_{metric}"], row[f"q3_{metric}"] = (float(x) for x in np.quantile(series, (0.25, 0.75)))
            row[f"ci95_low_{metric}"], row[f"ci95_high_{metric}"] = interval(series)
            if metric == "cpu_net_j" or metric == "gpu_net_j" and key[3] == "ncf":
                mean = statistics.fmean(series)
                if mean <= 0 or statistics.stdev(series) / mean > 0.10:
                    raise ValueError(f"Net energy CV above 10% or non-positive: {key} {metric}")
        summaries.append(row)
    by_key = {tuple(row[field] for field in ("environment", "library", "dataset", "model", "stage")): row
              for row in summaries}
    for row in summaries:
        if row["stage"] != "full":
            continue
        data_model = "rf" if row["dataset"] == "insurance" else "svd"
        baseline = by_key[(row["environment"], row["library"], row["dataset"], data_model, "data")]
        data_j = float(baseline["median_cpu_net_j"])
        full_j = float(row["median_cpu_net_j"])
        row["data_share_pct"] = 100 * data_j / full_j
        row["training_estimate_j"] = full_j - data_j
    return summaries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session_dir", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    session, output = args.session_dir.resolve(), args.output_dir.resolve()
    if output == session or session in output.parents or output.exists() and any(output.iterdir()):
        parser.error("Output directory must be empty and outside the raw session")
    summary = summarize(audit(session))
    output.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(field for row in summary for field in row))
    with (output / "summary.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary)
    report = ["# Session 2 full-stage results", "",
              "| Environment | Dataset | Model | Library | Net CPU J | Net GPU J | Data share | Training estimate J |",
              "| --- | --- | --- | --- | ---: | ---: | ---: | ---: |"]
    for row in summary:
        if row["stage"] != "full":
            continue
        report.append(
            f"| {row['environment']} | {row['dataset']} | {row['model']} | {row['library']} | "
            f"{row['median_cpu_net_j']:.3f} | {row['median_gpu_net_j']:.3f} | "
            f"{row['data_share_pct']:.1f}% | {row['training_estimate_j']:.3f} |"
        )
    (output / "full_stage_table.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Audited 30 configurations and 300 measured runs; wrote {output}")


if __name__ == "__main__":
    main()
