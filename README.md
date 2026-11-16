# DataFrame energy replication on a laptop

This repository tests six results from [Kumar, Imran, and Kosar's paper](https://arxiv.org/pdf/2511.08644) across two sessions. It compares Pandas, Polars and Dask on one laptop using Insurance with Random Forest, SVR, XGBoost and TabNet, and MovieLens-1M with collaborative filtering and NCF. Session 2 also measures NCF GPU energy and compares an older Python 3.8 software stack. This is a small-scale replication, not an exact reproduction of the paper's hardware, software or energy metric. The [protocol](PROTOCOL.md) fixes the workload and decision rules; the [report](report/REPORT.md) gives the interpretation.

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

Use `--lib pandas|polars|dask`, `--data insurance|ml-1m`, and `--stage data|full`. The `data` stage stops after preprocessing and checksums; `full` also trains the chosen model. `--model` defaults to `rf` for Insurance and `svd` for ML-1M so the session-1 commands still work. Insurance also accepts `svr`, `xgboost` and `tabnet`; ML-1M also accepts `ncf`.

```bash
.venv/bin/python pipeline.py --lib pandas --data insurance --stage data
.venv/bin/python pipeline.py --lib pandas --data insurance --stage full
.venv/bin/python pipeline.py --lib polars --data ml-1m --stage full
.venv/bin/python pipeline.py --lib pandas --data insurance --model svr --stage full
```

`models.py` holds the shared training code after the dataframe backends produce arrays. TabNet and NCF require CUDA on GPU 0; they stop if it is unavailable. Functional checks, which do **not** use `perf` or measure energy, are:

```bash
.venv/bin/python scripts/smoke_session2.py --models svr xgboost tabnet ncf
```

The older-stack comparison uses only Insurance and Random Forest. Create its separate environment and check that its three backends produce the same input checksums and split indices as the current environment:

```bash
uv python install 3.8.12
uv venv --python 3.8.12 .venv-legacy
uv pip sync requirements-legacy.lock --python .venv-legacy/bin/python
.venv/bin/python scripts/smoke_legacy.py
```

`uv venv` may warn that the project requires Python 3.12 or newer. The separate `.venv-legacy` intentionally uses Python 3.8 with `requirements-legacy.lock`; its smoke test passed in a fresh clone.

Session-2 measurement code is in `scripts/run_session2.sh`; GPU power logging and offline integration are in `scripts/gpu_power.py`, the controlled GPU meter check is in `scripts/validate_gpu.py`, and session-2 raw-data auditing is in `scripts/analyze_session2.py`. These are separate from the session-1 runner and analyzer. The protocol and measurement code were frozen at tag `session2-frozen-20261116` before the official session on Nov 16, 2026. The runner completed 30 warm-ups and 300 measured runs; the raw session and analysis are linked below. A new official run requires an explicit `--full` flag, a passing GPU validation file and the prepared environment in Protocol Section 7.

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

The [session-1 table and figure](report/REPORT.md#3-results), [derived summary](results/analysis/summary.csv), and [raw full session](results/raw/full-20261025-135703-JICxLk/) are retained. The raw session includes failed runs if any; none of the 120 measured runs failed.

Session 2 found Pandas < Polars < Dask in net CPU energy for SVR, XGBoost and TabNet. NCF showed no clear Pandas–Polars CPU difference and clearly higher Dask CPU energy; its three GPU-energy intervals all overlap. Under the frozen criteria, C3, C4 and C6 CPU are **partially reproduced**; C5 and C6 GPU are **not reproduced**. The older Python 3.8 stack narrowed Dask's Random Forest gap over Pandas, while the categorical version-comparison outcome remained **no change**. See the [session-2 interpretation](report/REPORT.md#8-session-2-new-models-and-software-stack-comparison), [30-configuration summary](results/analysis/session2-20261116-012318-MJNiIT/summary.csv), [raw session](results/raw/full-20261116-012318-MJNiIT/) and [reproducibility audit](results/analysis/session2-20261116-012318-MJNiIT/reproducibility.md). The session completed with 300/300 measured runs, matching checksums and CV below 10%. No ML-1M dataset files are redistributed in this repository.

## Limits and AI assistance

The results apply to this laptop, dataset versions and chosen models. Insurance has 1,338 rows versus the paper's reported 1,000; the library versions and energy domains also differ. RAPL package energy includes other machine activity even after idle subtraction. The C2 outcome rule has a gap when Pandas and Polars are indistinguishable but Dask is clearly higher. COCO models and DRAM energy remain untested; see the report for details.

I chose the claims, preprocessing rules, measurement conditions, and C2 interpretation; I ran and checked the measurements, including one manual median. The pipeline was developed step by step with AI assistance. AI also helped draft supporting scripts, documentation, and report prose. The measurements and raw files came from my machine, not from AI.
