#!/usr/bin/env python3
"""Log NVML board power and integrate marked idle/run windows offline."""

from __future__ import annotations

import argparse
import csv
import math
import signal
import statistics
import time
from pathlib import Path


SAMPLE_PERIOD_S = 0.1
RUN_PAD_NS = 2_000_000_000


def sample(output: Path, gpu_index: int) -> None:
    import pynvml

    stop = False

    def handle_stop(_signum, _frame):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGTERM, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)
    output.parent.mkdir(parents=True, exist_ok=True)
    pynvml.nvmlInit()
    try:
        gpu = pynvml.nvmlDeviceGetHandleByIndex(gpu_index)
        with output.open("w", newline="", encoding="utf-8", buffering=1) as file:
            writer = csv.writer(file)
            writer.writerow(("monotonic_ns", "power_w"))
            next_tick = time.monotonic()
            while not stop:
                timestamp = time.monotonic_ns()
                watts = pynvml.nvmlDeviceGetPowerUsage(gpu) / 1000.0
                writer.writerow((timestamp, f"{watts:.6f}"))
                next_tick += SAMPLE_PERIOD_S
                time.sleep(max(0, next_tick - time.monotonic()))
    finally:
        pynvml.nvmlShutdown()


def read_samples(path: Path) -> list[tuple[int, float]]:
    with path.open(newline="", encoding="utf-8") as file:
        rows = [(int(row["monotonic_ns"]), float(row["power_w"])) for row in csv.DictReader(file)]
    if len(rows) < 2 or any(b[0] <= a[0] for a, b in zip(rows, rows[1:])):
        raise ValueError("GPU samples need at least two increasing timestamps")
    if any(not math.isfinite(power) or power < 0 for _, power in rows):
        raise ValueError("Invalid GPU power reading")
    return rows


def integrate(samples: list[tuple[int, float]], start_ns: int, end_ns: int) -> float:
    """Trapezoid integral with linearly interpolated power at both boundaries."""
    if not samples[0][0] <= start_ns < end_ns <= samples[-1][0]:
        raise ValueError("GPU samples do not cover the requested window")

    def at(timestamp: int) -> float:
        for (t0, p0), (t1, p1) in zip(samples, samples[1:]):
            if t0 <= timestamp <= t1:
                return p0 + (p1 - p0) * (timestamp - t0) / (t1 - t0)
        raise ValueError("Timestamp outside GPU sample coverage")

    points = [(start_ns, at(start_ns))]
    points.extend((t, p) for t, p in samples if start_ns < t < end_ns)
    points.append((end_ns, at(end_ns)))
    return sum((b[0] - a[0]) / 1e9 * (a[1] + b[1]) / 2 for a, b in zip(points, points[1:]))


def summarize(samples_path: Path, windows_path: Path, output_dir: Path) -> None:
    samples = read_samples(samples_path)
    with windows_path.open(newline="", encoding="utf-8") as file:
        windows = list(csv.DictReader(file))
    idle_powers = []
    runs = []
    for row in windows:
        start, end = int(row["start_ns"]), int(row["end_ns"])
        if row["kind"] == "idle":
            idle_powers.append(integrate(samples, start, end) / ((end - start) / 1e9))
        elif row["kind"] == "run":
            runs.append((row["id"], start, end))
        else:
            raise ValueError(f"Unknown GPU window kind: {row['kind']}")
    if not idle_powers:
        raise ValueError("At least one idle window is required")
    baseline = statistics.median(idle_powers)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "gpu_idle_power_w.txt").write_text(f"{baseline:.6f}\n", encoding="utf-8")
    with (output_dir / "gpu_runs.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(("run_id", "start_ns", "end_ns", "window_s", "gpu_energy_j", "gpu_net_j"))
        for run_id, start, end in runs:
            window_start, window_end = start - RUN_PAD_NS, end + RUN_PAD_NS
            energy = integrate(samples, window_start, window_end)
            duration = (window_end - window_start) / 1e9
            writer.writerow((run_id, start, end, f"{duration:.9f}",
                             f"{energy:.6f}", f"{energy - baseline * duration:.6f}"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sampler = sub.add_parser("sample", help="Sample until SIGINT or SIGTERM")
    sampler.add_argument("--output", type=Path, required=True)
    sampler.add_argument("--gpu-index", type=int, default=0)
    analysis = sub.add_parser("summarize", help="Integrate recorded windows")
    analysis.add_argument("--samples", type=Path, required=True)
    analysis.add_argument("--windows", type=Path, required=True)
    analysis.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "sample":
        sample(args.output, args.gpu_index)
    else:
        summarize(args.samples, args.windows, args.output_dir)


if __name__ == "__main__":
    main()
