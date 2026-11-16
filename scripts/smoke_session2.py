#!/usr/bin/env python3
"""Functional checks only: no perf, energy sampling, idle baseline, or benchmark."""

from __future__ import annotations

import argparse
import math
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKENDS = ("pandas", "polars", "dask")
MODEL_DATA = {"svr": "insurance", "xgboost": "insurance", "tabnet": "insurance", "ncf": "ml-1m"}
CHECKSUM_KEYS = {
    "insurance": ("Feature order:", "X shape:", "y shape:", "X sum:", "y sum:"),
    "ml-1m": ("X shape:", "Nonzero ratings:", "X sum:", "UserID order SHA-256:", "MovieID order SHA-256:"),
}


def field(output: str, prefix: str) -> str:
    matches = [line[len(prefix):].strip() for line in output.splitlines() if line.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"Expected one {prefix!r} line, found {len(matches)}")
    return matches[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", choices=MODEL_DATA, default=list(MODEL_DATA))
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results/smoke_test" /
                        f"session2-{datetime.now():%Y%m%d-%H%M%S}")
    args = parser.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        parser.error("Output directory must be empty; smoke evidence is not overwritten")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1",
               CUBLAS_WORKSPACE_CONFIG=":4096:2", PYTHONDONTWRITEBYTECODE="1")
    lines = ["# Session 2 functional smoke test", "", "No energy or benchmark measurement was run.", ""]
    for model in args.models:
        dataset = MODEL_DATA[model]
        checksums: dict[str, dict[str, str]] = {}
        metrics: dict[str, dict[str, float]] = {}
        splits: dict[str, dict[str, str]] = {}
        for stage in ("data", "full"):
            for backend in BACKENDS:
                command = [sys.executable, "pipeline.py", "--lib", backend,
                           "--data", dataset, "--stage", stage, "--model", model]
                result = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True)
                stem = f"{backend}_{dataset}_{model}_{stage}"
                (args.output_dir / f"{stem}.stdout.txt").write_text(result.stdout, encoding="utf-8")
                (args.output_dir / f"{stem}.stderr.txt").write_text(result.stderr, encoding="utf-8")
                if result.returncode:
                    raise SystemExit(f"{stem} failed ({result.returncode}); inspect the saved stderr")
                values = {key: field(result.stdout, key) for key in CHECKSUM_KEYS[dataset]}
                if stage == "data":
                    checksums[backend] = values
                elif values != checksums[backend]:
                    raise SystemExit(f"{stem}: data/full checksum mismatch")
                if stage == "full":
                    if dataset == "insurance":
                        splits[backend] = {
                            key: field(result.stdout, key)
                            for key in ("Train rows:", "Test rows:", "Train index SHA-256:", "Test index SHA-256:")
                        }
                        metric_keys = ("Test R²:", "Test RMSE:")
                    else:
                        splits[backend] = {
                            line.split(" SHA-256:")[0]: line.split(" SHA-256:")[1].strip()
                            for line in result.stdout.splitlines() if "pairs:" in line and "SHA-256:" in line
                        }
                        if len(splits[backend]) != 4:
                            raise SystemExit(f"{stem}: expected four NCF pair hashes")
                        metric_keys = ("Test BCE:", "Test ROC AUC:")
                    metrics[backend] = {key: float(field(result.stdout, key)) for key in metric_keys}
                    if not all(math.isfinite(value) for value in metrics[backend].values()):
                        raise SystemExit(f"{stem}: non-finite test metric")
                    device = field(result.stdout, "Model device:") if model in ("xgboost", "tabnet", "ncf") else "cpu"
                    if model == "xgboost" and device != "cpu" or model in ("tabnet", "ncf") and not device.startswith("cuda"):
                        raise SystemExit(f"{stem}: unexpected device {device}")
                lines.append(f"- PASS `{stem}`")
        first = BACKENDS[0]
        if any(checksums[backend] != checksums[first] for backend in BACKENDS[1:]):
            raise SystemExit(f"{model}: backend input checksums differ")
        if any(splits[backend] != splits[first] for backend in BACKENDS[1:]):
            raise SystemExit(f"{model}: backend split indices or sampled pairs differ")
        for key, value in metrics[first].items():
            if any(abs(metrics[backend][key] - value) > 1e-5 for backend in BACKENDS[1:]):
                raise SystemExit(f"{model}: backend {key} differs")
        lines.append(f"- PASS `{model}`: matching checksums, splits and metrics across backends")
    summary = args.output_dir / "summary.md"
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"PASS: {len(args.models)} models; evidence: {summary}")


if __name__ == "__main__":
    main()
