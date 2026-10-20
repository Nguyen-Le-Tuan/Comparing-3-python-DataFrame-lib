#!/usr/bin/env bash
# Step 2: idle baseline and the two validation tests for RAPL energy measurement.
# Collects the commands run by hand on 2026-10-19 that produced results/validation/.
# Usage: scripts/validate_measurement.sh [output_dir]
#   The default output_dir is a new timestamped folder, so the original results are never overwritten.
# Needs sudo for perf (perf_event_paranoid = 4). Takes about 10 minutes.
# Before running: AC power connected, power profile "balanced", browser and IDE closed.
set -euo pipefail
export LC_ALL=C

OUT="${1:-results/validation-$(date +%Y%m%d-%H%M%S)}"
PY=.venv/bin/python
# Calibrated on 2026-10-19 so that one run takes about 15 s (1e8: 3.52 s, 2e8: 7.44 s, 4e8: 14.76 s)
N=400000000
LOOP='import sys; sum(i*i for i in range(int(sys.argv[1])))'

mkdir -p "$OUT"
if [ -n "$(ls -A "$OUT")" ]; then
  echo "$OUT is not empty; choose a new folder" >&2
  exit 1
fi

# Settings that change CPU power. Added after the first session: power profile, AC power, CPU temperature.
cpu_state() {
  grep . /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor \
    /sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference \
    /sys/devices/system/cpu/intel_pstate/no_turbo
  echo "power_profile:$(powerprofilesctl get 2>/dev/null || echo unknown)"
  echo "ac_online:$(cat /sys/class/power_supply/A*/online 2>/dev/null | head -n 1)"
  for z in /sys/class/thermal/thermal_zone*; do
    if [ "$(cat "$z/type")" = "x86_pkg_temp" ]; then
      echo "cpu_package_temp_C:$(( $(cat "$z/temp") / 1000 ))"
    fi
  done
}

date -Is > "$OUT/start_time.txt"
echo 'Sleep error <= 15%; CPU 2N/N net-energy ratio = 1.8 to 2.2' > "$OUT/criteria.txt"
cpu_state > "$OUT/cpu_state_before.txt"
grep -H . /sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_governor > "$OUT/all_governors.txt"
sudo -v

# Idle baseline: 5 runs of sleep 30 s, 40 s pause after each
for i in 01 02 03 04 05; do
  sudo env LC_ALL=C perf stat -x, -e power/energy-pkg/ -- sleep 30 2> "$OUT/baseline_${i}.csv"
  sleep 40
done

# Test 1: sleep 10 s
sudo env LC_ALL=C perf stat -x, -e power/energy-pkg/ -- sleep 10 2> "$OUT/sleep_10.csv"
sleep 40

# Test 2: the same CPU loop with N and 2N iterations (timing check first, not measured with perf)
/usr/bin/time -f 'elapsed=%e s' -o "$OUT/calibration.txt" "$PY" -c "$LOOP" "$N"
sleep 40
sudo env LC_ALL=C perf stat -x, -e power/energy-pkg/ -- "$PY" -c "$LOOP" "$N" 2> "$OUT/cpu_n.csv"
sleep 40
sudo env LC_ALL=C perf stat -x, -e power/energy-pkg/ -- "$PY" -c "$LOOP" "$((2 * N))" 2> "$OUT/cpu_2n.csv"

cpu_state > "$OUT/cpu_state_after.txt"
date -Is > "$OUT/end_time.txt"

"$(dirname "$0")/analyze_validation.sh" "$OUT"
