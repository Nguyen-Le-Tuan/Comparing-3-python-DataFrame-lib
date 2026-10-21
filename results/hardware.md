# Hardware and software setup

Recorded on 2026-10-19 (America/New_York). Laptop: Lenovo IdeaPad Gaming 3 15IAH7, on AC power.

## CPU

| Item | Value |
| --- | --- |
| Model | Intel Core i5-12500H (Alder Lake) |
| Cores / threads | 12 cores, 16 threads: 4 performance cores with Hyper-Threading (`cpu0`–`cpu7`, max 4.5 GHz) + 8 efficiency cores (`cpu8`–`cpu15`, max 3.3 GHz); min 0.4 GHz |
| Cache | L1d 448 KiB, L1i 640 KiB (12 instances); L2 9 MiB (6 instances); L3 18 MiB shared |
| Frequency driver | `intel_pstate`, active mode |
| Governor | `powersave` on all 16 CPUs; EPP `balance_performance`; Turbo Boost on; power profile `balanced` |
| Power limits (powercap, `package-0`) | long_term 200 W (window ≈ 32 s), short_term 115 W, as reported by Linux; the firmware may enforce lower limits |

## Memory and storage

| Item | Value |
| --- | --- |
| RAM | 16 GB installed; 14.8 GiB visible to Linux (`MemTotal` 15,563,044 kB) |
| Swap | 12 GiB |
| Storage | WD Green SN350 500 GB NVMe (system disk); Micron MTFDKCD512TFK 512 GB NVMe |

## GPU

| Item | Value |
| --- | --- |
| Discrete GPU | NVIDIA GeForce RTX 3050 Laptop (GA107M), 4 GB, compute capability 8.6 |
| Integrated GPU | Intel Iris Xe (Alder Lake-P GT2) |
| NVIDIA driver | Kernel module 610.57.04 loaded; user-space libraries 615.71 (package `nvidia-driver-615` installed on 2026-10-19). `nvidia-smi` fails with "Driver/library version mismatch" until the next reboot |
| CUDA toolkit | 13.3 (`nvcc` V13.3.73); 13.0 and 13.1 also installed under `/usr/local` |
| CUDA check | `cuda_check.cu` compiled with `nvcc -O2` and ran on 2026-10-19: `CUDA kernel OK: 42` |

To do after the reboot: confirm `nvidia-smi` works and record the driver version that is loaded.

## Software

| Item | Value |
| --- | --- |
| OS | Ubuntu 26.04.1 LTS |
| Kernel | 7.0.0-38-generic |
| Compilers | gcc / g++ 15.2.0; CMake 4.2.3 |
| perf | 7.0.14 |
| Python | 3.14.4 (system) |

## Energy counters (RAPL)

| Item | Value |
| --- | --- |
| `perf` events | `power/energy-pkg/`, `power/energy-cores/`, `power/energy-gpu/`, `power/energy-psys/` |
| powercap domains | `package-0` (with `core` and `uncore`), `psys` |
| Not available | DRAM energy (`energy-ram`) |
| Access | root only (`perf_event_paranoid` = 4; `energy_uj` readable by root only), so energy is measured with `sudo perf stat` |
| Idle package power | 4.776 W: median of 5 × `sleep 30`, range 4.755–4.814 W |

`energy-gpu` is the Intel integrated GPU, not the RTX 3050. NVIDIA GPU power comes from NVML (`nvidia-smi`, `pynvml`).

The idle power and two validation tests come from step 2 of the reproduction project `Comparing-3-python-DataFrame-lib` on the same day (files in its `results/validation/`). `sleep 10` matched idle power × time within 0.38%. A CPU loop with twice the iterations used 1.854 times the net energy (limit: 1.8–2.2). In that test the 30 s run drew less net power than the 15 s run (18.2 W vs 20.3 W), so long runs slow down.

## Baseline workload (`baseline.csv`)

- **Workload:** pure-Python sum of squares, `sum(i*i for i in range(100_000_000))`. It is single-threaded, CPU-bound and uses almost no memory (max RSS ≈ 9.5 MB).
- **How:** `./run_baseline.sh`: 1 warm-up (discarded), then 10 runs with 5 s pauses, pinned to `cpu2` (a performance core) with `taskset`, timed with `/usr/bin/time`.
- **Columns:** `run`, `cpu`, `n`, `elapsed_s` (wall time), `user_s`, `sys_s`, `max_rss_kb`, `start_time`.
- **Result (2026-10-19, 23:17):** median 3.77 s, range 3.75–3.95 s, coefficient of variation 1.68%. CPU package at 69 °C before the runs; the usual desktop apps were open.
- **Not measured here:** energy per run (needs `sudo perf stat`).

Step 2 of the reproduction timed the same loop at 3.52 s without pinning, using the Python 3.12 of that project's virtual environment. The two numbers are not directly comparable.
