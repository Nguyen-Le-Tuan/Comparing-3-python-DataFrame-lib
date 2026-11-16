#!/usr/bin/env bash
# Session 2 only. Explicit --full is required; never invoked by smoke tests.
# Pilot: sudo ./scripts/run_session2.sh --pilot current pandas insurance svr full
# Full:  sudo ./scripts/run_session2.sh --full --gpu-validation PATH
set -Eeuo pipefail
export LC_ALL=C

# Keep the shared scikit-learn/BLAS workload single-threaded in every process.
# Record this choice in PROTOCOL.md before the full run.
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export CUBLAS_WORKSPACE_CONFIG=:4096:2
# Avoid root-owned __pycache__ files in the repository and virtualenv.
export PYTHONDONTWRITEBYTECODE=1

ORDER_SEED=42
PAUSE_SECONDS=40
MODE=
PILOT_ENV=-
PILOT_LIB=-
PILOT_DATA=-
PILOT_MODEL=-
PILOT_STAGE=-
GPU_VALIDATION=

usage() {
  printf 'Usage: sudo %s --pilot <current|legacy> <pandas|polars|dask> <insurance|ml-1m> <model> <data|full>\n' "$0"
  printf '       sudo %s --full --gpu-validation <passing-validation-file>\n' "$0"
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

if [[ ${1:-} == --help ]]; then
  usage
  exit 0
fi
if [[ ${1:-} == --pilot && $# -eq 6 ]]; then
  MODE=pilot
  PILOT_ENV=$2
  PILOT_LIB=$3
  PILOT_DATA=$4
  PILOT_MODEL=$5
  PILOT_STAGE=$6
  [[ $PILOT_ENV == current || $PILOT_ENV == legacy ]] || die "Invalid environment: $PILOT_ENV"
  [[ $PILOT_LIB == pandas || $PILOT_LIB == polars || $PILOT_LIB == dask ]] || die "Invalid library: $PILOT_LIB"
  [[ $PILOT_DATA == insurance || $PILOT_DATA == ml-1m ]] || die "Invalid dataset: $PILOT_DATA"
  [[ $PILOT_STAGE == data || $PILOT_STAGE == full ]] || die "Invalid stage: $PILOT_STAGE"
  if [[ $PILOT_ENV == legacy ]]; then
    [[ $PILOT_DATA == insurance && $PILOT_MODEL == rf ]] || die 'Legacy environment supports only Insurance/RF.'
  elif [[ $PILOT_DATA == insurance ]]; then
    [[ $PILOT_MODEL == rf || $PILOT_MODEL == svr || $PILOT_MODEL == xgboost || $PILOT_MODEL == tabnet ]] || die 'Invalid Insurance model.'
  else
    [[ $PILOT_MODEL == svd || $PILOT_MODEL == ncf ]] || die 'Invalid MovieLens model.'
  fi
elif [[ ${1:-} == --full && ${2:-} == --gpu-validation && $# -eq 3 ]]; then
  MODE=full
  GPU_VALIDATION=$(readlink -f -- "$3")
  [[ -f $GPU_VALIDATION ]] || die "Missing GPU validation: $GPU_VALIDATION"
  grep -Fqx 'status=PASS' "$GPU_VALIDATION" || die 'GPU validation did not pass.'
elif (( $# != 0 )); then
  usage >&2
  exit 2
else
  usage >&2
  exit 2
fi

(( EUID == 0 )) || die 'Run with sudo so perf can read RAPL events.'
[[ ${SUDO_UID:-} =~ ^[0-9]+$ && ${SUDO_GID:-} =~ ^[0-9]+$ ]] || die 'Run via sudo from your own account, not a root login.'
(( SUDO_UID > 0 )) || die 'Do not launch this script from a root login.'

for command_name in perf powerprofilesctl nmcli ip sha256sum awk sort sed git readlink; do
  command -v "$command_name" >/dev/null || die "Missing command: $command_name"
done
[[ -x /usr/bin/time ]] || die '/usr/bin/time is missing.'

REPO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
cd -- "$REPO_ROOT"
PY_CURRENT="$REPO_ROOT/.venv/bin/python"
PY_LEGACY="$REPO_ROOT/.venv-legacy/bin/python"
[[ -x $PY_CURRENT && -x $PY_LEGACY ]] || die 'Both Python environments must exist.'
for input_file in \
  pipeline.py models.py PROTOCOL.md requirements.lock requirements-legacy.lock \
  data/raw/insurance.csv \
  data/raw/ml-1m/ratings.dat data/raw/ml-1m/users.dat data/raw/ml-1m/movies.dat; do
  [[ -f $input_file ]] || die "Missing input: $input_file"
done

RAW_ROOT="$REPO_ROOT/results/raw"
[[ ! -L $RAW_ROOT ]] || die 'results/raw must not be a symlink.'
if [[ ! -d $RAW_ROOT ]]; then
  install -d -m 0755 -o "$SUDO_UID" -g "$SUDO_GID" -- "$RAW_ROOT"
fi
SESSION_DIR=$(mktemp -d "$RAW_ROOT/${MODE}-$(date +%Y%m%d-%H%M%S)-XXXXXX")
SESSION_COMPLETE=0
GPU_SAMPLER_PID=

ac_online() {
  local supply
  for supply in /sys/class/power_supply/*; do
    [[ -r $supply/type && -r $supply/online ]] || continue
    if [[ $(<"$supply/type") == Mains && $(<"$supply/online") == 1 ]]; then
      printf '1\n'
      return 0
    fi
  done
  printf '0\n'
}

cpu_temp_c() {
  local zone raw
  for zone in /sys/class/thermal/thermal_zone*; do
    [[ -r $zone/type && -r $zone/temp ]] || continue
    if [[ $(<"$zone/type") == x86_pkg_temp ]]; then
      raw=$(<"$zone/temp")
      awk -v millidegrees="$raw" 'BEGIN {printf "%.1f\n", millidegrees/1000}'
      return 0
    fi
  done
  return 1
}

capture_state() {
  local cpu path
  printf 'time=%s\n' "$(date -Is)"
  printf 'kernel=%s\n' "$(uname -r)"
  printf 'ac_online=%s\n' "$(ac_online)"
  printf 'power_profile=%s\n' "$(powerprofilesctl get 2>&1 || true)"
  printf 'wifi_radio=%s\n' "$(nmcli radio wifi 2>&1 || true)"
  printf 'ipv4_default_route=%s\n' "$(ip -4 route show default | tr '\n' ' ')"
  printf 'ipv6_default_route=%s\n' "$(ip -6 route show default | tr '\n' ' ')"
  printf 'no_turbo=%s\n' "$(< /sys/devices/system/cpu/intel_pstate/no_turbo)"
  printf 'cpu0_epp=%s\n' "$(< /sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference)"
  printf 'cpu_package_temp_c=%s\n' "$(cpu_temp_c || printf unavailable)"
  for cpu in /sys/devices/system/cpu/cpu[0-9]*; do
    path="$cpu/cpufreq/scaling_governor"
    [[ -r $path ]] || continue
    printf '%s=%s\n' "${cpu##*/}_governor" "$(<"$path")"
  done
}

cleanup() {
  local result=$?
  trap - EXIT
  if [[ -n $GPU_SAMPLER_PID ]]; then
    kill "$GPU_SAMPLER_PID" 2>/dev/null || true
    wait "$GPU_SAMPLER_PID" 2>/dev/null || true
  fi
  capture_state > "$SESSION_DIR/cpu_state_after.txt" 2>&1 || true
  if (( result == 0 && SESSION_COMPLETE == 1 )); then
    printf 'COMPLETE\n' > "$SESSION_DIR/session_status.txt"
  else
    printf 'INCOMPLETE exit_code=%s\n' "$result" > "$SESSION_DIR/session_status.txt"
  fi
  chown -R -- "$SUDO_UID:$SUDO_GID" "$SESSION_DIR"
  printf 'Session: %s\n' "$SESSION_DIR"
  exit "$result"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

log() {
  printf '%s %s\n' "$(date -Is)" "$*" | tee -a "$SESSION_DIR/runner.log"
}

verify_full_conditions() {
  local cpu path count=0
  [[ $(ac_online) == 1 ]] || die 'AC power is not connected.'
  [[ $(powerprofilesctl get) == balanced ]] || die 'Power profile is not balanced.'
  [[ $(nmcli radio wifi) == disabled ]] || die 'Wi-Fi radio is not disabled; enable airplane mode.'
  [[ -z $(ip -4 route show default) && -z $(ip -6 route show default) ]] || die 'A default network route remains; disconnect networking.'
  [[ $(< /sys/devices/system/cpu/intel_pstate/no_turbo) == 0 ]] || die 'Turbo Boost setting changed.'
  [[ $(< /sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference) == balance_performance ]] || die 'CPU EPP changed.'
  for cpu in /sys/devices/system/cpu/cpu[0-9]*; do
    path="$cpu/cpufreq/scaling_governor"
    [[ -r $path ]] || continue
    [[ $(<"$path") == powersave ]] || die "Governor changed: $path"
    (( count += 1 ))
  done
  (( count == 16 )) || die "Expected 16 CPU governors, found $count."
  cpu_temp_c >/dev/null || die 'CPU package temperature sensor is unavailable.'
}

log "Starting $MODE session; seed=$ORDER_SEED; pause=${PAUSE_SECONDS}s"
capture_state > "$SESSION_DIR/cpu_state_before.txt"
if [[ $MODE == full ]]; then
  verify_full_conditions
else
  log 'Pilot does not enforce AC, balanced profile, or offline state; its data is not part of the final analysis.'
fi

{
  printf 'mode=%s\nseed=%s\npause_seconds=%s\n' "$MODE" "$ORDER_SEED" "$PAUSE_SECONDS"
  printf 'python_current_command=%s\n' "$PY_CURRENT"
  printf 'python_current_executable=%s\n' "$("$PY_CURRENT" -c 'import sys; print(sys.executable)')"
  printf 'python_current_realpath=%s\n' "$("$PY_CURRENT" -c 'import os, sys; print(os.path.realpath(sys.executable))')"
  printf 'python_current_version=%s\n' "$("$PY_CURRENT" --version 2>&1)"
  printf 'python_legacy_command=%s\n' "$PY_LEGACY"
  printf 'python_legacy_executable=%s\n' "$("$PY_LEGACY" -c 'import sys; print(sys.executable)')"
  printf 'python_legacy_realpath=%s\n' "$("$PY_LEGACY" -c 'import os, sys; print(os.path.realpath(sys.executable))')"
  printf 'python_legacy_version=%s\n' "$("$PY_LEGACY" --version 2>&1)"
  if [[ $MODE == full ]]; then
    printf 'gpu_validation_source=%s\n' "$GPU_VALIDATION"
  fi
  printf 'perf=%s\n' "$(perf --version)"
  printf 'openblas_threads=%s\nomp_threads=%s\nmkl_threads=%s\n' \
    "$OPENBLAS_NUM_THREADS" "$OMP_NUM_THREADS" "$MKL_NUM_THREADS"
  printf 'python_dont_write_bytecode=%s\n' "$PYTHONDONTWRITEBYTECODE"
  printf 'git_commit=%s\n' "$(git -c safe.directory="$REPO_ROOT" rev-parse HEAD)"
} > "$SESSION_DIR/environment.txt"
cp requirements.lock "$SESSION_DIR/requirements-current.lock"
cp requirements-legacy.lock "$SESSION_DIR/requirements-legacy.lock"
if [[ $MODE == full ]]; then
  cp "$GPU_VALIDATION" "$SESSION_DIR/gpu_validation.txt"
fi
git -c safe.directory="$REPO_ROOT" status --short > "$SESSION_DIR/git_status_before.txt"
sha256sum scripts/run_session2.sh scripts/gpu_power.py scripts/validate_gpu.py \
  scripts/analyze_session2.py pipeline.py models.py PROTOCOL.md \
  requirements.lock requirements-legacy.lock \
  data/raw/insurance.csv data/raw/ml-1m/*.dat > "$SESSION_DIR/input_sha256.txt"

# Emit the exact process order before measuring anything. Each measured round
# contains one seeded random permutation of all 30 configurations.
"$PY_CURRENT" - "$ORDER_SEED" "$MODE" "$PILOT_ENV" "$PILOT_LIB" "$PILOT_DATA" "$PILOT_MODEL" "$PILOT_STAGE" \
  > "$SESSION_DIR/schedule.csv" <<'PYCODE'
import csv
import itertools
import random
import sys

seed, mode, pilot_env, pilot_lib, pilot_data, pilot_model, pilot_stage = sys.argv[1:]
rng = random.Random(int(seed))
if mode == "pilot":
    configurations = [(pilot_env, pilot_lib, pilot_data, pilot_model, pilot_stage)]
    rounds = 1
else:
    configurations = []
    for lib in ("pandas", "polars", "dask"):
        configurations.extend(("current", lib, "insurance", model, "full")
                              for model in ("rf", "svr", "xgboost", "tabnet"))
        configurations.extend(("current", lib, "ml-1m", model, "full")
                              for model in ("svd", "ncf"))
        configurations.extend((("current", lib, "insurance", "rf", "data"),
                               ("current", lib, "ml-1m", "svd", "data"),
                               ("legacy", lib, "insurance", "rf", "full"),
                               ("legacy", lib, "insurance", "rf", "data")))
    rounds = 10

writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(("sequence", "kind", "round", "environment", "lib", "dataset", "model", "stage"))
sequence = 0
warmups = configurations.copy()
rng.shuffle(warmups)
for configuration in warmups:
    sequence += 1
    writer.writerow((sequence, "warmup", 0, *configuration))
for round_number in range(1, rounds + 1):
    ordered = configurations.copy()
    rng.shuffle(ordered)
    for configuration in ordered:
        sequence += 1
        writer.writerow((sequence, "measured", round_number, *configuration))
PYCODE

# This parser matches the perf -x, CSV format already validated in step 2:
# energy (J), unit, event name, event running time (ns), ...
perf_metric() {
  local file=$1 event=$2
  awk -F, -v event="$event" '
    $3 == event && $1+0 > 0 && $4+0 > 0 {
      printf "%.6f,%.9f\n", $1, $4/1e9
      found++
    }
    END {if (found != 1) exit 1}
  ' "$file"
}

BASELINE_RUNS=5
EXPECTED_MEASURED=300
EXPECTED_WARMUPS=30
if [[ $MODE == pilot ]]; then
  BASELINE_RUNS=1
  EXPECTED_MEASURED=1
  EXPECTED_WARMUPS=1
fi
mkdir -- "$SESSION_DIR/idle" "$SESSION_DIR/runs"
printf 'id,kind,start_ns,end_ns\n' > "$SESSION_DIR/gpu_windows.csv"
"$PY_CURRENT" scripts/gpu_power.py sample --output "$SESSION_DIR/gpu_samples.csv" &
GPU_SAMPLER_PID=$!
sleep 3
kill -0 "$GPU_SAMPLER_PID" || die 'GPU sampler did not start.'
monotonic_ns() { "$PY_CURRENT" -c 'import time; print(time.monotonic_ns())'; }
printf 'file,energy_J,elapsed_s,power_W\n' > "$SESSION_DIR/idle/baseline.csv"
for (( i=1; i<=BASELINE_RUNS; i++ )); do
  [[ $MODE == pilot ]] || verify_full_conditions
  printf -v baseline_number '%02d' "$i"
  baseline_file="$SESSION_DIR/idle/baseline_${baseline_number}.csv"
  log "Idle baseline $i/$BASELINE_RUNS"
  gpu_idle_start=$(monotonic_ns)
  if ! perf stat -x, -o "$baseline_file" -e power/energy-pkg/ -- sleep 30 \
       > "$SESSION_DIR/idle/baseline_${baseline_number}.stdout.txt" \
       2> "$SESSION_DIR/idle/baseline_${baseline_number}.stderr.txt"; then
    die "Idle baseline failed: $baseline_file"
  fi
  gpu_idle_end=$(monotonic_ns)
  printf 'baseline_%02d,idle,%s,%s\n' "$i" "$gpu_idle_start" "$gpu_idle_end" >> "$SESSION_DIR/gpu_windows.csv"
  baseline_info=$(perf_metric "$baseline_file" 'power/energy-pkg/') || die "Invalid idle perf output: $baseline_file"
  IFS=, read -r baseline_j baseline_s <<< "$baseline_info"
  awk -v file="$(basename "$baseline_file")" -v e="$baseline_j" -v s="$baseline_s" \
    'BEGIN {printf "%s,%.6f,%.9f,%.6f\n", file, e, s, e/s}' \
    >> "$SESSION_DIR/idle/baseline.csv"
  sleep "$PAUSE_SECONDS"
done
median_line=$(( (BASELINE_RUNS + 1) / 2 ))
tail -n +2 "$SESSION_DIR/idle/baseline.csv" | cut -d, -f4 | sort -n \
  | sed -n "${median_line}p" > "$SESSION_DIR/idle/idle_power_w.txt"
[[ -s $SESSION_DIR/idle/idle_power_w.txt ]] || die 'Could not calculate idle power.'
log "Idle power: $(< "$SESSION_DIR/idle/idle_power_w.txt") W"

printf 'sequence,kind,round,environment,lib,dataset,model,stage,run_id,start_time,end_time,cpu_temp_c,exit_code,energy_pkg_j,energy_cores_j,elapsed_s,max_rss_kb,status\n' \
  > "$SESSION_DIR/runs.csv"

numeric_sum_matches() {
  local label=$1 expected=$2 output=$3
  awk -v label="$label" -v expected="$expected" '
    $1 == label && $2 == "sum:" {
      difference = $3 - expected
      if (difference < 0) difference = -difference
      valid = (difference < 0.000001)
      found++
    }
    END {if (found != 1 || !valid) exit 1}
  ' "$output"
}

check_pipeline_output() {
  local dataset=$1 model=$2 stage=$3 output=$4
  grep -Fqx "Model: $model" "$output" || return 1
  if [[ $dataset == insurance ]]; then
    numeric_sum_matches X 2288.0 "$output" || return 1
    numeric_sum_matches y 17755824.990759 "$output" || return 1
    grep -Fq 'X shape: (1338, 9) dtype: float64' "$output" || return 1
  else
    numeric_sum_matches X 3582313.0 "$output" || return 1
    grep -Fqx 'Nonzero ratings: 1000209' "$output" || return 1
    grep -Fq 'X shape: (6040, 3706) dtype: float64' "$output" || return 1
    grep -Fqx 'UserID order SHA-256: 778f9345757ada755e448c9333f347a68fdfd7654ff7fc1cfa8d230398106103' "$output" || return 1
    grep -Fqx 'MovieID order SHA-256: e28d14fcbf71098b6196f208ffe97401262c7312caf73893f8994bce5a0ac4c0' "$output" || return 1
  fi
  if [[ $stage == full ]]; then
    if [[ $dataset == insurance ]]; then
      grep -Fq 'Test R²:' "$output" || return 1
      grep -Fq 'Test RMSE:' "$output" || return 1
      if [[ $model == tabnet ]]; then
        grep -Eq '^Model device: cuda(:0)?$' "$output" || return 1
      elif [[ $model == xgboost ]]; then
        grep -Fqx 'Model device: cpu' "$output" || return 1
      fi
    elif [[ $model == ncf ]]; then
      grep -Fq 'Test BCE:' "$output" || return 1
      grep -Fq 'Test ROC AUC:' "$output" || return 1
      grep -Fqx 'Model device: cuda:0' "$output" || return 1
    else
      grep -Fqx 'SVD output shape: (6040, 50)' "$output" || return 1
    fi
  fi
}

run_one() {
  local sequence=$1 kind=$2 round=$3 environment=$4 lib=$5 dataset=$6 model=$7 stage=$8
  local run_id run_dir start_time end_time temperature command_exit status py
  local gpu_start gpu_end
  local pkg_info core_info pkg_j core_j elapsed_s max_rss_kb unused
  printf -v run_id '%03d_%s_r%02d_%s_%s_%s_%s_%s' \
    "$sequence" "$kind" "$round" "$environment" "$lib" "$dataset" "$model" "$stage"
  run_dir="$SESSION_DIR/runs/$run_id"
  mkdir -- "$run_dir"
  [[ $MODE == pilot ]] || verify_full_conditions
  temperature=$(cpu_temp_c) || die 'CPU package temperature sensor disappeared.'
  if [[ $environment == current ]]; then py=$PY_CURRENT; else py=$PY_LEGACY; fi
  start_time=$(date -Is)
  gpu_start=$(monotonic_ns)
  log "START $run_id temp=${temperature}C"

  if /usr/bin/time -v -o "$run_dir/time.txt" \
       perf stat -x, -o "$run_dir/perf.csv" \
       -e power/energy-pkg/,power/energy-cores/ -- \
       "$py" pipeline.py --lib "$lib" --data "$dataset" --stage "$stage" --model "$model" \
       > "$run_dir/stdout.txt" 2> "$run_dir/stderr.txt"; then
    command_exit=0
  else
    command_exit=$?
  fi
  gpu_end=$(monotonic_ns)
  printf '%s,run,%s,%s\n' "$run_id" "$gpu_start" "$gpu_end" >> "$SESSION_DIR/gpu_windows.csv"
  end_time=$(date -Is)

  pkg_j=NA
  core_j=NA
  elapsed_s=NA
  max_rss_kb=NA
  status=OK
  if [[ $command_exit -ne 0 ]]; then
    status=COMMAND_FAILED
  fi
  if pkg_info=$(perf_metric "$run_dir/perf.csv" 'power/energy-pkg/') && \
     core_info=$(perf_metric "$run_dir/perf.csv" 'power/energy-cores/'); then
    IFS=, read -r pkg_j elapsed_s <<< "$pkg_info"
    IFS=, read -r core_j unused <<< "$core_info"
  else
    status=INVALID_PERF
  fi
  max_rss_kb=$(awk -F: '/Maximum resident set size/ {gsub(/[[:space:]]/, "", $2); print $2}' "$run_dir/time.txt" 2>/dev/null || true)
  if [[ ! $max_rss_kb =~ ^[0-9]+$ ]]; then
    max_rss_kb=NA
    status=INVALID_RSS
  fi
  if (( command_exit == 0 )) && ! check_pipeline_output "$dataset" "$model" "$stage" "$run_dir/stdout.txt"; then
    status=OUTPUT_MISMATCH
  fi
  printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
    "$sequence" "$kind" "$round" "$environment" "$lib" "$dataset" "$model" "$stage" "$run_id" \
    "$start_time" "$end_time" "$temperature" "$command_exit" \
    "$pkg_j" "$core_j" "$elapsed_s" "$max_rss_kb" "$status" \
    >> "$SESSION_DIR/runs.csv"
  log "END $run_id status=$status pkg_J=$pkg_j elapsed_s=$elapsed_s rss_kB=$max_rss_kb"
  [[ $status == OK ]] || die "Run failed; raw files are retained in $run_dir"
}

previous_run=0
while IFS=, read -r sequence kind round environment lib dataset model stage; do
  [[ $sequence == sequence ]] && continue
  if (( previous_run == 1 )); then
    sleep "$PAUSE_SECONDS"
  fi
  run_one "$sequence" "$kind" "$round" "$environment" "$lib" "$dataset" "$model" "$stage"
  previous_run=1
done < "$SESSION_DIR/schedule.csv"

awk -F, -v measured="$EXPECTED_MEASURED" -v warmups="$EXPECTED_WARMUPS" '
  NR > 1 && $2 == "measured" && $18 == "OK" {m++}
  NR > 1 && $2 == "warmup" && $18 == "OK" {w++}
  END {if (m != measured || w != warmups) exit 1}
' "$SESSION_DIR/runs.csv" || die 'Run counts do not match the pre-registered schedule.'

sleep 3  # preserve the delayed NVML power reading after the final run
kill "$GPU_SAMPLER_PID"
wait "$GPU_SAMPLER_PID"
GPU_SAMPLER_PID=
"$PY_CURRENT" scripts/gpu_power.py summarize \
  --samples "$SESSION_DIR/gpu_samples.csv" \
  --windows "$SESSION_DIR/gpu_windows.csv" --output-dir "$SESSION_DIR/gpu"

{
  printf 'mode=%s\nseed=%s\nwarmups=%s\nmeasured=%s\n' \
    "$MODE" "$ORDER_SEED" "$EXPECTED_WARMUPS" "$EXPECTED_MEASURED"
  printf 'idle_power_w=%s\n' "$(< "$SESSION_DIR/idle/idle_power_w.txt")"
  printf 'completed_at=%s\n' "$(date -Is)"
} > "$SESSION_DIR/summary.txt"
SESSION_COMPLETE=1
log "Session complete: $EXPECTED_MEASURED measured runs."
