# Step 2: measurement validation (Oct 19, 2026)

Checks that `sudo perf stat -e power/energy-pkg/` measures CPU energy correctly on this laptop before any pipeline is measured. Session: 21:48 to 22:32 (America/New_York). AC power connected, power profile `balanced`.

**Result: both tests pass.** See `validation_summary.txt`.

| File | Content |
| --- | --- |
| `criteria.txt` | Pass limits, written before the first measurement |
| `start_time.txt`, `end_time.txt` | Session start and end |
| `cpu_state_before.txt`, `cpu_state_after.txt`, `all_governors.txt` | Governor, EPP and Turbo Boost before and after; governor of all 16 CPUs |
| `baseline_01.csv` to `baseline_05.csv` | Raw `perf stat -x,` output of five `sleep 30` runs |
| `baseline.csv`, `idle_power_w.txt` | Average power of each run; idle power = median (4.776 W) |
| `sleep_10.csv`, `sleep_check.txt` | Test 1: `sleep 10` measured against idle power × time (error 0.38%) |
| `calibration.txt` | Timing of the CPU loop used to choose N = 400,000,000 |
| `cpu_n.csv`, `cpu_2n.csv`, `cpu_net.csv`, `cpu_ratio.txt` | Test 2: CPU loop with N and 2N iterations; net-energy ratio 1.854 |
| `validation_summary.txt` | PASS/FAIL for both tests |

Raw files were produced by commands run by hand; they are collected in `scripts/validate_measurement.sh`. Derived files are recomputed from the raw files with `scripts/analyze_validation.sh results/validation`. On Oct 19 the five raw baseline files were first saved as `results/validation.baseline_0N.csv` (a typo in the path) and then moved here unchanged.

**Observation:** the 2N run took 2.07 times as long as the N run but used only 1.85 times the net energy; net power fell from 20.3 W to 18.2 W. Longer runs slow down, probably because of heat or because the process moves between performance and efficiency cores.
