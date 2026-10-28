# DataFrame energy replication on a laptop

This repository tests two results from [Kumar, Imran, and Kosar's paper](https://arxiv.org/pdf/2511.08644): Insurance + Random Forest (C1) and MovieLens-1M + collaborative filtering (C2). It compares Pandas, Polars, and Dask on one laptop. This is a small-scale replication, not an exact reproduction of the paper's hardware, software, or energy metric. The [protocol](PROTOCOL.md) fixes the workload and decision rules; the [report](report/REPORT.md) gives the interpretation. The scope is being extended ([protocol v2](PROTOCOL.md)) to SVR, XGBoost and TabNet on Insurance, NCF on ML-1M, GPU energy, and a version comparison with the paper's library versions; results for these are pending.

## Setup

Run these commands from the repository root on Ubuntu. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) first if needed. Dataset setup also needs `curl`, `unzip`, and `sha256sum`.

```bash
uv venv --python 3.12
uv pip sync requirements.lock --python .venv/bin/python
./scripts/download_data.sh
./scripts/download_data.sh --verify-only
```

`requirements.in` lists direct Python dependencies; `requirements.lock` pins the resolved package versions used for the measurements. The download script obtains Insurance from [Kaggle](https://www.kaggle.com/datasets/mirichoi0218/insurance) and MovieLens-1M from [GroupLens](https://grouplens.org/datasets/movielens/1m/). It checks SHA-256 before extracting fixed archive members and refuses to replace a local file with a different hash. The pipeline reads `data/raw/insurance.csv` and the `ratings.dat`, `users.dat`, and `movies.dat` files under `data/raw/ml-1m/`. Protocol Section 3 records the Insurance CSV and ML-1M ZIP hashes; the script also pins both archives and all extracted files.

The `data/` directory is ignored by Git. Do not commit the ML-1M archive or extracted files: its included `README` prohibits redistribution without separate permission and requires acknowledgment in publications. This Ubuntu host's `curl` does not trust the current GroupLens TLS issuer. Prefer fixing local CA trust, or download `ml-1m.zip` from the [official page](https://grouplens.org/datasets/movielens/1m/) in a browser, place it at `data/raw/ml-1m.zip`, and rerun the script. If neither works, `./scripts/download_data.sh --allow-unverified-ml-tls` explicitly permits a TLS-verification fallback **only for GroupLens**. The pinned ZIP SHA-256 must still match before the file is saved or extracted; the default command never bypasses TLS checks.

## Run the pipelines

Use `--lib pandas|polars|dask`, `--data insurance|ml-1m`, and `--stage data|full`. The `data` stage stops after preprocessing and checksums; `full` also runs Random Forest or TruncatedSVD.

```bash
.venv/bin/python pipeline.py --lib pandas --data insurance --stage data
.venv/bin/python pipeline.py --lib pandas --data insurance --stage full
.venv/bin/python pipeline.py --lib polars --data ml-1m --stage full
```

The three backends must produce matching shapes, feature/axis order, and checksums before energy results are compared. See Protocol Sections 4 and 7 for the expected outputs and all twelve configurations.

The measurement runner needs Ubuntu `perf` with CPU RAPL access, `/usr/bin/time`, `powerprofilesctl`, `nmcli`, `ip`, and `sudo`. A pilot is optional and excluded from the final analysis:

```bash
sudo ./scripts/run_measurements.sh --pilot pandas insurance data
```

The full command below creates a **new** session under `results/raw/`. It measures 12 configurations with one warm-up and ten measured runs each. Before running it, follow Protocol Section 7: AC power, balanced profile, specified CPU settings, Wi-Fi off, no default route, and other apps closed. Do not use a casual run as a replacement for the committed full session.

```bash
sudo ./scripts/run_measurements.sh
```

To reanalyze the committed session without overwriting `results/analysis/`, give the analysis script a fresh output directory:

```bash
analysis_dir=$(mktemp -d)
.venv/bin/python scripts/analyze_results.py results/raw/full-20261025-135703-JICxLk --output-dir "$analysis_dir"
printf 'Analysis output: %s\n' "$analysis_dir"
```

## Results

These are local medians of **net CPU package energy** for `--stage full`, ten measured runs per configuration. Package energy is not the paper's core-plus-DRAM energy.

| Dataset | Pandas | Polars | Dask | Interpretation |
| --- | ---: | ---: | ---: | --- |
| Insurance | 16.736 J | 18.309 J | 26.061 J | C1 partially reproduced: Dask highest, but Pandas and Polars differ clearly. |
| ML-1M | 76.238 J | 76.632 J | 197.827 J | C2 is not covered by the pre-measurement verdict categories: Pandas and Polars have overlapping 95% intervals; Dask is clearly highest. |

The [full table and figure](report/REPORT.md#3-results), [derived summary](results/analysis/summary.csv), and [raw full session](results/raw/full-20261025-135703-JICxLk/) are retained. The raw session includes failed runs if any; none of the 120 measured runs failed. No ML-1M data are in the repository.

## Limits and AI assistance

The result applies to this laptop, dataset versions, and chosen models. Insurance has 1,338 rows versus the paper's reported 1,000; the library versions and energy domains also differ. RAPL package energy includes other machine activity even after idle subtraction. The C2 outcome rule has a gap when Pandas and Polars are indistinguishable but Dask is clearly higher. Untested models and GPU energy receive no verdict; see the report for details.

I chose the claims, preprocessing rules, measurement conditions, and C2 interpretation; I ran and checked the measurements, including one manual median. The pipeline was developed step by step with AI assistance. AI also helped draft supporting scripts, documentation, and report prose. The measurements and raw files came from my machine, not from AI.
