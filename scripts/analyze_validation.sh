#!/usr/bin/env bash
# Step 2: compute idle power and the two validation checks from the raw perf files.
# Usage: scripts/analyze_validation.sh [validation_dir]   (default: results/validation)
# Same formulas as the commands run by hand on 2026-10-19; this script only adds CSV headers
# and a PASS/FAIL summary. It reads the raw files and never changes them.
set -euo pipefail
export LC_ALL=C

DIR="${1:-results/validation}"

# perf stat -x, writes: value,unit,event,counter run time (ns),percent,...
# Column 4 is how long the counter ran, which equals the elapsed time of the command.

# Idle baseline: average package power of each 30 s sleep run
{
  echo "file,energy_J,elapsed_s,power_W"
  for f in "$DIR"/baseline_0?.csv; do
    awk -F, '$3=="power/energy-pkg/" {printf "%s,%.2f,%.6f,%.6f\n", FILENAME, $1, $4/1e9, $1/($4/1e9)}' "$f"
  done
} > "$DIR/baseline.csv"

# Idle power = median of the baseline runs
tail -n +2 "$DIR/baseline.csv" | cut -d, -f4 | sort -n \
  | awk '{v[NR]=$1} END {if (NR%2) print v[(NR+1)/2]; else printf "%.6f\n", (v[NR/2]+v[NR/2+1])/2}' \
  > "$DIR/idle_power_w.txt"
P="$(cat "$DIR/idle_power_w.txt")"

# Test 1: sleep 10 s should use idle power x elapsed time
awk -F, -v p="$P" '$3=="power/energy-pkg/" {t=$4/1e9; x=p*t; d=$1-x; if (d<0) d=-d;
  printf "measured=%.3f J; expected=%.3f J; error=%.3f%%\n", $1, x, 100*d/x}' \
  "$DIR/sleep_10.csv" > "$DIR/sleep_check.txt"

# Test 2: twice the loop iterations should use about twice the net energy
{
  echo "file,energy_J,elapsed_s,net_J,net_power_W"
  for f in "$DIR/cpu_n.csv" "$DIR/cpu_2n.csv"; do
    awk -F, -v p="$P" '$3=="power/energy-pkg/" {t=$4/1e9; net=$1-p*t;
      printf "%s,%.3f,%.6f,%.3f,%.3f\n", FILENAME, $1, t, net, net/t}' "$f"
  done
} > "$DIR/cpu_net.csv"
awk -F, 'NR==2 {n=$4} NR==3 {printf "2N/N ratio = %.3f\n", $4/n}' "$DIR/cpu_net.csv" > "$DIR/cpu_ratio.txt"

# PASS/FAIL against the limits written in criteria.txt before measuring
err="$(sed -E 's/.*error=([0-9.]+)%.*/\1/' "$DIR/sleep_check.txt")"
ratio="$(sed -E 's/.*= ([0-9.]+)/\1/' "$DIR/cpu_ratio.txt")"
awk -v p="$P" -v e="$err" -v r="$ratio" 'BEGIN {
  printf "Idle power: %.3f W (median of the baseline runs)\n", p
  printf "Test 1, sleep 10 s: error %.3f%% -> %s (limit: 15%%)\n", e, (e <= 15 ? "PASS" : "FAIL")
  printf "Test 2, CPU loop 2N/N: net-energy ratio %.3f -> %s (range: 1.8 to 2.2)\n", r, (r >= 1.8 && r <= 2.2 ? "PASS" : "FAIL")
}' | tee "$DIR/validation_summary.txt"
