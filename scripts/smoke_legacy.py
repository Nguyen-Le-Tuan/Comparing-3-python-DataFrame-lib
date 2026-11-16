#!/usr/bin/env python3
"""Check Insurance preprocessing and RF split in both Python environments."""

from __future__ import annotations

import os
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKENDS = ("pandas", "polars", "dask")
KEYS = ("Feature order:", "X shape:", "y shape:", "X sum:", "y sum:",
        "Train index SHA-256:", "Test index SHA-256:")


def extract(output: str, key: str) -> str:
    matches = [line for line in output.splitlines() if line.startswith(key)]
    if len(matches) != 1:
        raise ValueError(f"Missing or repeated {key!r}")
    return matches[0]


def main() -> None:
    output_dir = ROOT / "results/smoke_test" / f"session2_legacy-{datetime.now():%Y%m%d-%H%M%S}"
    if output_dir.exists():
        raise SystemExit(f"Smoke evidence directory already exists: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
    expected = {}
    lines = ["# Session 2 version-comparison smoke test", "",
             "Functional output checks only; no benchmark measurement.", ""]
    for environment, executable in (
        ("current", ROOT / ".venv/bin/python"),
        ("legacy", ROOT / ".venv-legacy/bin/python"),
    ):
        if not executable.is_file():
            raise SystemExit(f"Missing environment: {executable}")
        lines.append(f"## {environment}")
        for backend in BACKENDS:
            for stage in ("data", "full"):
                name = f"{environment}_{backend}_{stage}"
                result = subprocess.run([
                    str(executable), "pipeline.py", "--lib", backend,
                    "--data", "insurance", "--stage", stage, "--model", "rf",
                ], cwd=ROOT, env=env, text=True, capture_output=True)
                (output_dir / f"{name}.stdout.txt").write_text(result.stdout, encoding="utf-8")
                (output_dir / f"{name}.stderr.txt").write_text(result.stderr, encoding="utf-8")
                if result.returncode:
                    raise SystemExit(f"{name} failed; inspect saved stderr")
                keys = KEYS[:5] if stage == "data" else KEYS
                observed = tuple(extract(result.stdout, key) for key in keys)
                baseline = expected.setdefault(stage, observed)
                if observed != baseline:
                    raise SystemExit(f"{name} differs from current Pandas {stage} output")
                lines.append(f"- PASS `{name}`")
        lines.append("")
    (output_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"PASS: matching inputs and split indices; evidence: {output_dir}")


if __name__ == "__main__":
    main()
