# Replication Protocol: Energy Use of Pandas, Polars and Dask on a Laptop

| Field | Value |
| --- | --- |
| Author | Le Tuan Nguyen (University at Buffalo, CS) |
| Study type | Small-scale **replication**: personal laptop, current library versions |
| Session 1 (C1–C2) | Registered before measurement in commit `4badf06`; status set to FROZEN in `5881ae5`; measured Oct 25, 2026 |
| Session 2 (C3–C6, version comparison) | Registered Oct 28, 2026, before measurement; frozen before the session starts |
| Repository | https://github.com/Nguyen-Le-Tuan/Comparing-3-python-DataFrame-lib |

## 0. Original paper

- **Paper:** *Energy Consumption of Dataframe Libraries for End-to-End Deep Learning Pipelines: A Comparative Analysis*.
- **Authors:** Punit Kumar, Asif Imran, and Tevfik Kosar
- **DOI:** 10.48550/arXiv.2511.08644
- **Reported setup:** 16-core / 32-thread CPU at 2.10 GHz, 128 GB RAM, NVIDIA Tesla V100 32 GB, 1 TB NVMe SSD, Ubuntu 20.04 LTS with Linux kernel 5.4; Python 3.8.12, Pandas 1.4.2, Polars 0.10.18, Dask 2022.2.0. CPU energy from `perf stat` (energy-cores + energy-ram); GPU energy from pynvml sampled every second. One warm-up run, then five measured runs; 40 s idle between runs; a fresh process per run; varied run order.

## 1. Claims and hypotheses

- **C1:** Testing the energy consumption of Pandas, Polars and Dask on the Insurance Dataset. The paper reported that by using *Random Forest*, Pandas and Polars use similar CPU energy (146.8 J) while Dask uses more 14% (167.4 J); however, on SVR and XGBoost, Dask is even higher (20-22%).
- **C2:** Testing on the MovieLens 1M will result in energy uses: Polars < Pandas < Dask.
- **C3 (Insurance, SVR):** _To be written before session 2._
- **C4 (Insurance, XGBoost):** _To be written before session 2._
- **C5 (Insurance, TabNet):** _To be written before session 2._
- **C6 (ML-1M, NCF):** _To be written before session 2._
- **Where in the paper:** Table 1; Section 4.1 and Figure 5 (Insurance); Section 4.3 and Figure 3a (ML-1M).
- **Hypothesis for session 1, written before measurement:** Because the Insurance dataset is in tabular format and only has 1k rows while the MovieLens is 1M samples, I assume that Pandas will perform the best in the Insurance Dataset while the Polars will be the best in the ML-1M. I have these assumptions because I already knew that Pandas is still advantageous on small data while Polars (which written in Rust) will outperform Pandas on larger data (from several GB to hundred GB).
- **Hypothesis for session 2:** _To be written before session 2 and not edited after it starts._

Paper values from Table 1, checked against the arXiv HTML version. I compare directions and relative gaps, not absolute joules (Section 8).

| Claim | Model | Dataset | Backend | Runtime (s) | CPU energy (J) | GPU energy (J) |
| --- | --- | --- | --- | ---: | ---: | ---: |
| C1 | Random Forest | Insurance | Pandas | 0.817 | 146.760 | 26.01 |
| C1 | Random Forest | Insurance | Polars | 0.815 | 146.776 | 25.99 |
| C1 | Random Forest | Insurance | Dask | 1.027 | 167.436 | 31.73 |
| C2 | CF | ML-1M | Pandas | 34.156 | 3,328.320 | 2,270.88 |
| C2 | CF | ML-1M | Polars | 14.203 | 1,437.000 | 1,816.50 |
| C2 | CF | ML-1M | Dask | 38.482 | 3,748.080 | 2,472.66 |
| C3 | SVR | Insurance | Pandas | 0.160 | 87.706 | 8.65 |
| C3 | SVR | Insurance | Polars | 0.168 | 87.712 | 7.50 |
| C3 | SVR | Insurance | Dask | 0.364 | 106.572 | 12.14 |
| C4 | XGBoost | Insurance | Pandas | 0.204 | 96.336 | 8.67 |
| C4 | XGBoost | Insurance | Polars | 0.192 | 96.218 | 8.65 |
| C4 | XGBoost | Insurance | Dask | 0.410 | 115.654 | 15.02 |
| C5 | TabNet | Insurance | Pandas | 1.688 | 447.914 | 106.42 |
| C5 | TabNet | Insurance | Polars | 1.826 | 245.066 | 113.21 |
| C5 | TabNet | Insurance | Dask | 1.844 | 334.002 | 109.98 |
| C6 | NCF | ML-1M | Pandas | 17.916 | 1,801.422 | 339.39 |
| C6 | NCF | ML-1M | Polars | 2.526 | 497.992 | 142.76 |
| C6 | NCF | ML-1M | Dask | 64.871 | 6,313.152 | 2,139.67 |

## 2. Scope

I check six results from Table 1 on two datasets, Insurance and MovieLens-1M, in two measurement sessions. For each library, I measure energy and runtime for the **data stage alone** and for **the full run (data stage + model training)**.

| Item | Dataset | Downstream model | Session |
| --- | --- | --- | --- |
| C1 | Insurance | Random Forest | 1 |
| C2 | MovieLens-1M | Collaborative filtering (TruncatedSVD) | 1 |
| C3 | Insurance | SVR | 2 |
| C4 | Insurance | XGBoost | 2 |
| C5 | Insurance | TabNet | 2 |
| C6 | MovieLens-1M | Neural collaborative filtering (NCF), GPU energy measured | 2 |
| Version comparison | Insurance | Python 3.8 with the paper's versions (Pandas 1.4.2, Polars 0.10.18, Dask 2022.2.0), to separate library-version effects from hardware effects | 2 |

**Not tested:** ResNet and Mask R-CNN on COCO, because training them exceeds this laptop's 4 GB of GPU memory and about 14 GB of usable RAM; DRAM energy, because the CPU exposes no DRAM energy counter.

## 3. Data

| Dataset | Source | License | Rows × columns | SHA-256 of downloaded file |
| --- | --- | --- | --- | --- |
| Insurance | Medical Cost Personal Datasets ([Kaggle](https://www.kaggle.com/datasets/mirichoi0218/insurance)) | [Database: Open Database, Contents: Database Contents](https://opendatacommons.org/licenses/dbcl/1-0/) | 1,338 rows × 7 columns | 388eff679557d08ac19f463d025de5e0b4adc482537c8456d19934d78621fd47 |
| MovieLens-1M | [GroupLens](https://grouplens.org/datasets/movielens/1m/) (paper cited) | Custom Non-Commercial / Academic Use | `users.dat`: 6,040 × 5; `movies.dat`: 3,883 × 3; `ratings.dat`: 1,000,209 × 4 | a6898adb50b9ca05aa231689da44c217cb524e7ebd39d264c56e2832f2c54e20 |

## 4. Pipeline definition

Based on *Algorithm 1: Unified Data Processing Pipeline* (Section 3.1 of the paper). All three libraries do exactly these steps.

**Insurance (C1, C3–C5)**

1. Load `insurance.csv` into a dataframe (expect 1,338 rows × 7 columns: `age`, `sex`, `bmi`, `children`, `smoker`, `region`, `charges`).
2. Impute missing values (numeric columns: the column mean; text columns: the most frequent value). Insurance has no missing cells, so this step changes nothing, but it still runs so that every library does the same work as in the paper. I use the mean instead of the median because Dask only computes an approximate median.
3. Encode the categorical columns (`sex`: male = 1, female = 0; `smoker`: yes = 1, no = 0; `region`: one-hot, one column per region in alphabetical order).
4. Standardize `age`, `bmi` and `children` (subtract the mean, divide by the sample standard deviation with ddof = 1). The target `charges` is not scaled.
5. Convert to NumPy arrays: `X` with 9 feature columns in a fixed order (`age`, `bmi`, `children`, `sex`, `smoker`, `region_northeast`, `region_northwest`, `region_southeast`, `region_southwest`) and `y` = `charges`. Slice `X` and `y` into mini-batches of 64 rows in file order (21 batches; the last one has 58 rows).

**MovieLens-1M (C2, C6)**

1. Load `ratings.dat` (1,000,209 × 4), `users.dat` (6,040 × 5) and `movies.dat` (3,883 × 3) with the `::` separator.
2. Join ratings to users on `UserID` and to movies on `MovieID`, validating many-to-one joins and preserving all 1,000,209 ratings.
3. Check that each `(UserID, MovieID)` pair is unique; pivot `Rating` to rows = sorted `UserID`, columns = sorted rated `MovieID`, and fill unrated cells with 0, giving a 6,040 × 3,706 `float64` matrix `X`.
4. Slice `X` into batches of 64 user rows in sorted-UserID order without shuffling and sum every batch. The data-stage checksum is the `X` shape, sum, nonzero count and ordered-ID hashes.
5. `--stage full` trains the downstream model on `X`; `--stage data` stops after the checksum. There is no target `y` in this pipeline.

**Rules for both datasets**

- **Output checksum:** the program prints the shapes of the output arrays and the sum of all their elements, computed over the mini-batches so every batch is used. All three libraries must give the same shapes, the same feature-column order and sums that differ by less than 1e-6 before any energy comparison. For ML-1M, the ordered `UserID` and `MovieID` axes are compared as well.
- **Library-specific choices:**
  - Pandas: eager, `pd.read_csv` with default settings.
  - Polars: lazy, `pl.scan_csv` and expressions, with a single `.collect()` before the NumPy conversion, because the paper credits Polars' lazy expressions for its efficiency. For ML-1M, Polars scans and joins lazily, collects the joined rows once, then pivots eagerly before NumPy conversion; the rated `MovieID` columns are not known before scanning, so the pivot cannot be lazy.
  - Dask: `dd.read_csv` with the default block size and the default threaded scheduler; the number of partitions is printed at runtime. Categorical columns are made "known" with `.categorize()` before one-hot encoding. For ML-1M, Dask reads `::` with the Python CSV engine, joins the three tables, checks joined-row and unique-pair counts, categorizes `MovieID`, then uses `pivot_table(aggfunc="first")`. Because pairs are unique, this gives the same matrix as the Pandas pivot. The matrix is sorted by numeric `UserID` and `MovieID` before NumPy conversion.
- **Randomness:** mini-batches are taken in file order, so the data stage has no randomness. Models use seed 42; the measurement schedule is randomized separately with seed 42 (Section 7).
- **Two stages per configuration:** `--stage data` runs only the dataframe part; `--stage full` also trains the downstream model. Training energy is estimated as *full* − *data*.
- **Downstream models.** The paper reports no hyperparameters, so these are my choices. Insurance models train on 80% of the rows (`train_test_split` with `test_size=0.2`, `random_state=42`: 1,070 training rows, 268 test rows) and print the test R² as a sanity check; the mini-batch step is kept only to follow the paper.
  - Random Forest (C1): scikit-learn `RandomForestRegressor` with default hyperparameters (100 trees, one CPU core) and `random_state=42`.
  - CF (C2): `TruncatedSVD(n_components=50, random_state=42)` on the whole `X`, giving a 6,040 × 50 user-factor matrix.
  - SVR (C3): _kernel, hyperparameters, and whether `charges` is scaled; to be fixed before session 2._
  - XGBoost (C4): _hyperparameters, threads and `random_state`; to be fixed before session 2._
  - TabNet (C5): _hyperparameters, epochs, batch size and device; to be fixed before session 2._
  - NCF (C6): _input derived from `X`, architecture, embedding size, loss, epochs, batch size and device; to be fixed before session 2._

## 5. Comparisons

- **Baseline:** Pandas. **Compared:** Polars, Dask.
- **Session 1:** 3 libraries × 2 datasets × 2 stages = 12 configurations.
- **Session 2:** _to be fixed before session 2: the full-stage configurations for C3–C6, which data-stage configurations are re-measured, whether Random Forest and TruncatedSVD are re-run as reference points, and the version-comparison configurations._

## 6. Metrics and how they are measured

| Metric | Unit | Tool and formula |
| --- | --- | --- |
| Runtime | s | `power/energy-pkg/` event running time from `perf stat -x,` (nanoseconds / 1e9); `/usr/bin/time -v` keeps wall-clock time for cross-checking |
| CPU package energy | J | `power/energy-pkg/` via `sudo perf stat` |
| CPU core energy | J | `power/energy-cores/` via `sudo perf stat` |
| Net CPU package energy | J | package energy − session idle package power × runtime; core energy is reported separately, not substituted for package energy |
| Training energy (derived) | J | median net package energy of `--stage full` minus that of `--stage data` for the same library and dataset; an estimate, not a separately metered phase |
| Peak memory | kB (convert to MB in analysis) | maximum resident set size from `/usr/bin/time -v` |
| GPU energy | J | Session 2 only, via NVML. _Method (cumulative energy counter or fixed-interval sampling) and GPU idle baseline to be fixed before session 2._ |
| Disk I/O / usage | Not measured | Storage hardware is reported in Section 10, not treated as a workload metric |

The measurement runner is `scripts/run_measurements.sh`. It calls `perf stat` and `/usr/bin/time -v` around each fresh pipeline process, records both RAPL domains, and checks the pipeline output. It sets `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1` and `PYTHONDONTWRITEBYTECODE=1` for every run, and is launched once per session:

```bash
sudo ./scripts/run_measurements.sh
```

A pilot uses `sudo ./scripts/run_measurements.sh --pilot pandas insurance data`; its results are stored separately and never analyzed. For session 2, the runner, pipeline and analysis script are extended for C3–C6, GPU energy and the version comparison before the session is frozen.

## 7. Procedure

Before each session, review the pilot output and this protocol, then freeze and commit the protocol and runner before the first measured run. If a pilot reveals a problem, fix and document it before freezing.

1. **Before measuring:** AC power for the whole session; browser, IDE and other avoidable apps closed; Airplane mode on. The runner requires Wi-Fi disabled and no IPv4/IPv6 default route. CPU settings stay fixed: governor `powersave` on all 16 logical CPUs (`intel_pstate`, active mode), CPU0 EPP `balance_performance`, power profile `balanced`, Turbo Boost enabled (`no_turbo=0`). The runner checks these before every baseline and pipeline run and records system state before and after the session. Closing apps is manual and cannot be verified by the script.
2. **Idle baseline:** the runner measures `power/energy-pkg/` during `sleep 30` five times with a 40 s pause after each; idle power is the median of the five average powers. Each session has its own baseline.
3. **Measurement validation** (pass limits in `results/validation/criteria.txt`, written before the first measurement; both must pass before any pipeline is measured):
   - Test 1: the energy of `sleep 10` is within 15% of idle power × elapsed time.
   - Test 2: a single-threaded loop, `sum(i*i for i in range(N))` with N = 400,000,000 (about 15 s), run with N and 2N iterations; the 2N/N ratio of net energy must be between 1.8 and 2.2.
   - Scripts: `scripts/validate_measurement.sh` and `scripts/analyze_validation.sh`. Result on Oct 19, 2026: idle 4.776 W (4.755–4.814 W); Test 1 error 0.38%; Test 2 ratio 1.854; both pass (`results/validation/`). The tests are repeated if the kernel, BIOS or power settings change.
   - Session 2 adds a GPU validation test, _defined with its pass limit before session 2_, which must pass before measuring.
4. **Smoke test:** every configuration runs in both stages through Pandas, Polars and Dask; input shape, columns and missing values are checked; output shapes, feature or ID order and checksums must match across libraries. Session 1 evidence is in `results/smoke_test/`. In session 2 the same check covers the new models and the version-comparison environment.
5. **Runs per configuration:** one warm-up of each configuration (excluded from analysis), then 10 rounds in which each configuration appears once. Order within warm-ups and each round is randomized with schedule seed 42. Each run is a fresh Python process, with a 40 s pause between runs and the CPU package temperature recorded before each run. Session 1: 12 configurations, 12 warm-ups, 120 measured runs.
6. **Raw data and failures:** each session has its own directory under `results/raw/full-.../` with the schedule, input SHA-256 values, Git state, pre/post CPU/network/power state, idle baseline, `runs.csv`, and each run's `perf.csv`, `time.txt`, stdout and stderr. Warm-ups and failed attempts stay in the raw data. The runner stops on a failed run and marks the session `INCOMPLETE`; such a session is not used. Pilots are stored under `results/raw/pilot-.../`. No result is deleted after inspection.
7. **Session notes:** after each session, `session_notes.md` in its raw directory states whether apps were closed, whether AC and Airplane mode held, and any interruptions, updates, thermal concerns or reruns.

## 8. Analysis plan

For each configuration (library × dataset × stage), I report the median and interquartile range (IQR) of net energy and runtime over the 10 measured runs. I use the median because one run may be unusually slow when a background process wakes up. I also report the trimmed mean, because the paper uses it.

- **Decision rule:** two libraries "differ" only if the 95% bootstrap confidence intervals of their median net energy do not overlap (10,000 resamples, seed 42); otherwise I report "no clear difference". The same rule is used for runtime.
- **Comparison with the paper:** my laptop and library versions differ from the paper's, so I compare the **direction** of the results (which library uses more energy, and by roughly what percentage), not the absolute joules. Table 1 reports end-to-end numbers, so this comparison uses `--stage full`.
- **Ranking on my laptop:** I rank Pandas, Polars and Dask by median net energy and report my ranking next to the paper's.
- **Decomposition:** the share of the data stage in the end-to-end energy, *data* / *full*.
- **Across sessions:** each session has its own idle baseline, so results from different sessions are compared only by direction and ratio.

## 9. Outcome criteria

Each claim is judged on `--stage full` with the decision rule in Section 8. Criteria for C1 and C2 were written before session 1:

| Outcome | C1: Insurance, Random Forest | C2: MovieLens-1M, CF |
| --- | --- | --- |
| Reproduced | No clear difference between Pandas and Polars in net energy, **and** Dask has the highest net energy and the longest runtime, clearly different from both | Polars < Pandas < Dask in net energy, with each difference clear |
| Partially reproduced | Only one of the two parts holds | Polars is the lowest, but the order of Pandas and Dask is unclear or reversed |
| Not reproduced | Neither part holds | Polars is not the lowest |
| Not tested | — | Not run before the report is written |

Criteria for C3–C6 and the version comparison: _to be written before session 2._ Each must state the outcome when the intervals of two libraries overlap, the case the C2 criteria leave open (Section 13).

**Stop and fix first** (no conclusion is drawn until the problem is fixed):

- an energy-measurement validation test fails (the `sleep` test, the 2× CPU-loop test or, in session 2, the GPU test);
- the three libraries give different checksums or a different feature-column order;
- the coefficient of variation (standard deviation / mean) of net energy within one configuration is above 10%.

The hypotheses in Section 1 are checked separately in the report; they do not change these outcomes.

## 10. Environment

| Item | Value |
| --- | --- |
| CPU | Intel Core i5-12500H (12 cores: 4 performance + 8 efficient, 16 threads) |
| RAM | 16 GB |
| GPU | NVIDIA GeForce RTX 3050 Laptop, 4 GB; NVIDIA kernel module 615.71.09 (from `/proc/driver/nvidia/version`, Oct 25, 2026) |
| OS / kernel | Ubuntu 26.04.1 LTS, kernel 7.0.0-38-generic |
| Storage | WD Green SN350 500 GB NVMe (`/dev/nvme1n1p2`, ext4); repository and raw data on this volume |
| perf | 7.0.14 |
| Python | 3.12.14 (via uv) |
| Library versions | Locked in `requirements.lock`: Pandas 3.0.6, Polars 2.0.0, Dask 2026.8.0, pyarrow 26.0.0, numpy 2.5.4, scikit-learn 1.9.1 |
| Version-comparison environment | Python 3.8 with Pandas 1.4.2, Polars 0.10.18, Dask 2022.2.0; exact versions recorded once installed |
| RAPL domains | package, core, uncore, psys; **no DRAM** |

## 11. Known differences from the paper and threats to validity

- Laptop instead of workstation; current library versions instead of the 2022 versions (the version comparison isolates part of this).
- Insurance has 1,338 rows, while the paper reports 1,000 records; the difference is kept rather than silently subsampling.
- RAPL measures the whole CPU package, not only the pipeline process; the idle baseline and closed apps reduce this noise.
- No DRAM energy domain, so CPU energy is not the paper's energy-cores + energy-ram sum.
- Possible thermal throttling: temperature is recorded before each run, but clock throttling is not measured directly.
- Disk I/O is not measured.
- One-thread BLAS/OpenMP settings and the laptop's power policy may change timings relative to the paper, but they are fixed across all local configurations.
- The paper is inconsistent: it states both "five runs, trimmed mean and 95% CI" and "mean of four measured runs"; its Insurance row count differs from the cited dataset; Section 4.1 says TabNet requires a GPU, but Section 3.2.2 lists only ResNet, Mask R-CNN and NCF as GPU experiments, and Table 1 reports GPU energy for SVR and XGBoost without naming their device.
- The paper does not report hyperparameters, the train/test split, the CF algorithm, or the architecture and device of any model; the choices in Section 4 are mine.
- Session 2 was planned after the session-1 results were known. Its claims, hypotheses, settings and criteria are written before any session-2 measurement.

## 12. Use of AI assistance

Pipeline code is written with AI assistance, one step at a time, then reviewed, run and annotated by the author. Sections 2, 4, 7, 8 and 9 of this protocol and the scripts in `scripts/` were drafted with AI assistance from the author's decisions and terminal commands, then reviewed by the author; the current structure of this document was revised the same way on Oct 28, 2026. The claims, hypotheses, data choices and all measurements are the author's own.

## 13. Notes after measurement

| Date | Note | Reason |
| --- | --- | --- |
| 2026-10-25 | Analysis conventions set in `scripts/analyze_results.py` (described in `results/analysis/method.md`) after session 1: percentile bootstrap interval for the median; quartiles with linear interpolation; 10% trimmed mean drops the lowest and highest of the 10 values; CV = sample standard deviation / mean net energy; data share and training estimate use stage medians, not paired run differences; peak memory reported in MiB (kB / 1024) instead of MB. | These details were not specified before measurement. The script reports measurements and derived statistics; I interpret each claim separately. |
| 2026-10-25 | For C2, I report the outcome as "not covered by the pre-registered criteria" when Pandas and Polars have overlapping energy CIs while Dask is clearly higher. The Section 9 categories are unchanged. | Section 9 does not specify what "Polars is the lowest" means when the Pandas–Polars difference is unclear. Its partial-outcome row also requires Pandas–Dask to be unclear or reversed, which is not observed. A standard label would force the result into a row whose conditions do not fit. |
