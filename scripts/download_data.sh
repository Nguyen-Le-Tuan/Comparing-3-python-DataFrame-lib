#!/usr/bin/env bash
# Download the two benchmark datasets and verify every file before use.
set -Eeuo pipefail
export LC_ALL=C

INSURANCE_URL='https://www.kaggle.com/api/v1/datasets/download/mirichoi0218/insurance'
ML_URL='https://files.grouplens.org/datasets/movielens/ml-1m.zip'
INSURANCE_ZIP_SHA='c1ab7d5b3563c2f36905749fdd49669de156a179cd34a70388a1a413f049feb1'
INSURANCE_CSV_SHA='388eff679557d08ac19f463d025de5e0b4adc482537c8456d19934d78621fd47'
ML_ZIP_SHA='a6898adb50b9ca05aa231689da44c217cb524e7ebd39d264c56e2832f2c54e20'
ML_RATINGS_SHA='506d64ca44484487c11dc2d9a28de5c54948213e6b96285e298afe28d6ea4e0f'
ML_USERS_SHA='1dc3a95300cb19f7c10e027daf29b8cdf1d908dab65b5edfb45950aa389a10a3'
ML_MOVIES_SHA='0140fc2356357c1a851d0f52e893a1e4d3696df632c4141cea8d5bc3d621f0b9'
ML_README_SHA='2d5ddce86ccbd247207456165827b4b9ddf27282bca93807d4c763e28414f133'

usage() {
  printf 'Usage: %s [--verify-only] [--allow-unverified-ml-tls] [insurance|ml-1m|all]\n' "$0"
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

verify_only=0
allow_unverified_ml_tls=0
dataset=all
dataset_set=0
for argument in "$@"; do
  case $argument in
    --help) usage; exit 0 ;;
    --verify-only) verify_only=1 ;;
    --allow-unverified-ml-tls) allow_unverified_ml_tls=1 ;;
    insurance|ml-1m|all)
      (( dataset_set == 0 )) || { usage >&2; exit 2; }
      dataset=$argument
      dataset_set=1
      ;;
    *) usage >&2; exit 2 ;;
  esac
done
(( verify_only == 0 || allow_unverified_ml_tls == 0 )) || die 'TLS fallback is not used with --verify-only.'

for command_name in sha256sum unzip mktemp; do
  command -v "$command_name" >/dev/null || die "Missing command: $command_name"
done
if (( verify_only == 0 )); then
  command -v curl >/dev/null || die 'Missing command: curl'
fi

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
raw_dir="$repo_root/data/raw"
if (( verify_only == 0 )); then
  mkdir -p -- "$raw_dir"
fi
[[ ! -L $repo_root/data && ! -L $raw_dir ]] || die 'The data directories must not be symlinks.'
[[ ! -L $raw_dir/ml-1m ]] || die 'The MovieLens directory must not be a symlink.'

tmp_dir=$(mktemp -d)
trap 'rm -rf -- "$tmp_dir"' EXIT

verify_sha() {
  local path=$1 expected=$2 actual
  [[ -f $path && ! -L $path ]] || die "Missing regular file: $path"
  actual=$(sha256sum -- "$path")
  actual=${actual%% *}
  [[ $actual == "$expected" ]] || die "SHA-256 mismatch: $path (got $actual)"
  printf 'SHA-256 OK: %s\n' "${path#"$repo_root"/}"
}

# Reuse only verified archives; never replace a conflicting local file.
ensure_archive() {
  local url=$1 target=$2 expected=$3 temp=$4 allow_tls_fallback=${5:-0} curl_status=0
  if [[ ! -e $target && ! -L $target ]]; then
    (( verify_only == 0 )) || die "Missing archive: $target"
    printf 'Downloading %s\n' "$url"
    curl --fail --location --retry 3 --connect-timeout 15 --max-time 300 \
      --proto '=https' --proto-redir '=https' --silent --show-error \
      --output "$temp" "$url" || curl_status=$?
    if (( curl_status == 60 && allow_tls_fallback == 1 )); then
      # Accept the fallback only after checking the pinned archive hash.
      printf 'WARNING: GroupLens TLS issuer was not verified; checking pinned SHA-256.\n' >&2
      curl --insecure --fail --location --retry 3 --connect-timeout 15 --max-time 300 \
        --proto '=https' --proto-redir '=https' --silent --show-error \
        --output "$temp" "$url"
    elif (( curl_status != 0 )); then
      die "Download failed (curl exit $curl_status): $url"
    fi
    verify_sha "$temp" "$expected"
    mv --no-clobber -- "$temp" "$target"
  fi
  verify_sha "$target" "$expected"
}

# Extract fixed ZIP members so archive paths cannot choose output locations.
ensure_member() {
  local archive=$1 member=$2 target=$3 expected=$4 temp=$5
  if [[ ! -e $target && ! -L $target ]]; then
    (( verify_only == 0 )) || die "Missing extracted file: $target"
    unzip -p "$archive" "$member" > "$temp"
    verify_sha "$temp" "$expected"
    mkdir -p -- "$(dirname -- "$target")"
    mv --no-clobber -- "$temp" "$target"
  fi
  verify_sha "$target" "$expected"
}

if [[ $dataset == insurance || $dataset == all ]]; then
  ensure_archive "$INSURANCE_URL" "$raw_dir/insurance.zip" "$INSURANCE_ZIP_SHA" "$tmp_dir/insurance.zip"
  ensure_member "$raw_dir/insurance.zip" insurance.csv "$raw_dir/insurance.csv" \
    "$INSURANCE_CSV_SHA" "$tmp_dir/insurance.csv"
fi

if [[ $dataset == ml-1m || $dataset == all ]]; then
  ensure_archive "$ML_URL" "$raw_dir/ml-1m.zip" "$ML_ZIP_SHA" "$tmp_dir/ml-1m.zip" \
    "$allow_unverified_ml_tls"
  for member in ratings.dat users.dat movies.dat README; do
    case $member in
      ratings.dat) expected=$ML_RATINGS_SHA ;;
      users.dat) expected=$ML_USERS_SHA ;;
      movies.dat) expected=$ML_MOVIES_SHA ;;
      README) expected=$ML_README_SHA ;;
    esac
    ensure_member "$raw_dir/ml-1m.zip" "ml-1m/$member" "$raw_dir/ml-1m/$member" \
      "$expected" "$tmp_dir/$member"
  done
fi

printf 'Dataset check complete: %s\n' "$dataset"
