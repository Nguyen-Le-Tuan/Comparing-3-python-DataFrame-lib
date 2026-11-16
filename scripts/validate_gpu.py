#!/usr/bin/env python3
"""Controlled GPU meter check; run manually before a measurement session."""

from __future__ import annotations

import argparse
import csv
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

from gpu_power import RUN_PAD_NS, integrate, read_samples


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        parser.error("Output directory must be empty")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:2"
    import torch

    if not torch.cuda.is_available():
        raise SystemExit("CUDA unavailable; GPU validation cannot run")
    samples_path = args.output_dir / "gpu_samples.csv"
    sampler = subprocess.Popen([
        sys.executable, str(Path(__file__).with_name("gpu_power.py")),
        "sample", "--output", str(samples_path),
    ])
    windows = []

    def idle(label: str, settle_seconds: int) -> None:
        time.sleep(settle_seconds)  # allow the GPU power state to return to idle
        start = time.monotonic_ns()
        time.sleep(5)
        windows.append((label, "idle", start, time.monotonic_ns()))

    try:
        idle("idle_before", 3)
        torch.manual_seed(42)
        a = torch.randn((2048, 2048), device="cuda:0")
        b = torch.randn((2048, 2048), device="cuda:0")
        c = torch.empty_like(a)
        torch.cuda.synchronize()
        for number in (1, 2):
            time.sleep(3 if number == 1 else 40)
            start = time.monotonic_ns()
            while (time.monotonic_ns() - start) < 10_000_000_000:
                torch.mm(a, b, out=c)
                torch.cuda.synchronize()
            windows.append((f"load_{number}", "run", start, time.monotonic_ns()))
        idle("idle_after", 40)
        time.sleep(3)
    finally:
        sampler.terminate()
        sampler.wait(timeout=10)

    with (args.output_dir / "windows.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(("id", "kind", "start_ns", "end_ns"))
        writer.writerows(windows)
    samples = read_samples(samples_path)
    idle_values = [
        integrate(samples, start, end) / ((end - start) / 1e9)
        for _, kind, start, end in windows if kind == "idle"
    ]
    baseline = statistics.median(idle_values)
    net_values = [
        integrate(samples, start - RUN_PAD_NS, end + RUN_PAD_NS)
        - baseline * ((end - start) / 1e9 + 4)
        for _, kind, start, end in windows if kind == "run"
    ]
    idle_relative_gap = abs(idle_values[1] - idle_values[0]) / baseline
    ratio = max(net_values) / min(net_values) if min(net_values) > 0 else float("inf")
    passed = idle_relative_gap <= 0.10 and min(net_values) >= 100 and ratio <= 1.30
    report = (
        f"idle_power_w={baseline:.6f}\n"
        f"idle_relative_gap={idle_relative_gap:.6f}\n"
        f"load_1_net_j={net_values[0]:.6f}\n"
        f"load_2_net_j={net_values[1]:.6f}\n"
        f"load_ratio={ratio:.6f}\n"
        f"status={'PASS' if passed else 'FAIL'}\n"
    )
    (args.output_dir / "gpu_validation.txt").write_text(report, encoding="utf-8")
    print(report, end="")
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
