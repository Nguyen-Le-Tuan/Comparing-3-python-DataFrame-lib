# Replication Protocol: Energy Use of Pandas, Polars and Dask on a Laptop

| Field | Value |
| --- | --- |
| Author | Le Tuan Nguyen (University at Buffalo, CS) |
| Study type | Small-scale replication on a personal laptop |
| Session 1 (C1–C2) | Pandas, Polars and Dask on Insurance with Random Forest and MovieLens-1M with collaborative filtering; 25 October 2026 |
| Session 2 (C3–C6, version comparison) | The same three libraries on Insurance with SVR, XGBoost and TabNet, and MovieLens-1M with NCF; Python 3.8 comparison; 16 November 2026 |
| UB email | letuanng@buffalo.edu |

## 0. Original paper

The paper is *Energy Consumption of Dataframe Libraries for End-to-End Deep Learning Pipelines: A Comparative Analysis* by Punit Kumar, Asif Imran and Tevfik Kosar (DOI 10.48550/arXiv.2511.08644).

According to the paper, the experiments ran on a 16-core / 32-thread CPU at 2.10 GHz with 128 GB RAM, an NVIDIA Tesla V100 32 GB, a 1 TB NVMe SSD and Ubuntu 20.04 LTS (Linux kernel 5.4), using Python 3.8.12, Pandas 1.4.2, Polars 0.10.18 and Dask 2022.2.0. The authors measured CPU energy with `perf stat` (energy-cores + energy-ram) and GPU energy with pynvml, sampled once per second. They ran one warm-up and then five measured runs, each in a fresh process, with 40 s of idle time between runs and a varied run order.

## 1. Claims and hypotheses

- **C1 (Insurance, Random Forest):** The paper reported nearly equal CPU energy for Pandas and Polars (146.760 and 146.776 J), with Dask about 14% higher (167.436 J) and the longest runtime.
- **C2 (ML-1M, collaborative filtering):** The paper reported the CPU energy order Polars < Pandas < Dask (1,437.000, 3,328.320 and 3,748.080 J).
- **C3 (Insurance, SVR):** The paper reported that Pandas and Polars use the same CPU energy (87.706 J and 87.712 J), while Dask uses about 21.5% more (106.572 J).
- **C4 (Insurance, XGBoost):** The paper reported that Pandas and Polars use nearly the same CPU energy (96.336 J and 96.218 J), while Dask uses about 20.1% more (115.654 J).
- **C5 (Insurance, TabNet):** The paper reported that Polars uses the least CPU energy (245.066 J), Dask is in the middle (334.002 J) and Pandas uses the most (447.914 J), so Polars is 45.3% below Pandas. The paper's runtimes follow a different order (Pandas 1.688 s, Polars 1.826 s, Dask 1.844 s), so this claim is judged on energy only.
- **C6 (ML-1M, NCF):** With neural collaborative filtering (NCF) as the downstream model, the paper reported the order Polars < Pandas < Dask for both CPU energy (497.992 J, 1,801.422 J and 6,313.152 J) and GPU energy (142.76 J, 339.39 J and 2,139.67 J). On CPU, Pandas uses about 3.6 times and Dask about 12.7 times the energy of Polars. The CPU order and the GPU order are tested as two separate parts.
- **Where in the paper:** Table 1; Section 4.1 and Figure 5 (Insurance); Section 4.3 and Figure 3a (ML-1M).
- **Hypothesis for session 1:** Because the Insurance dataset is in tabular format and only has 1k rows while the MovieLens is 1M samples, I assume that Pandas will perform the best in the Insurance Dataset while the Polars will be the best in the ML-1M. I have these assumptions because I already knew that Pandas is still advantageous on small data while Polars (which written in Rust) will outperform Pandas on larger data (from several GB to hundred GB).
- **Hypothesis for session 2**, written before any session-2 measurement and not edited after it starts:
  - **H3–H4 (SVR, XGBoost):** Pandas < Polars < Dask in net energy, with a clear Pandas–Polars difference rather than the paper's tie. These models train in a fraction of a second, so the data stage and process start-up dominate each run.
  - **H5 (TabNet):** Training dominates, so the gaps between libraries are much smaller than the paper's 45% for Polars. Dask is still the highest, and Polars is not clearly the lowest.
  - **H6 (NCF):** CPU: no clear Pandas–Polars difference and Dask clearly the highest, with gaps far below the paper's 3.6× and 12.7×. GPU: no clear difference between libraries. All three libraries train the same model on the same arrays.
  - **HV (version comparison):** With the paper's older stack, Dask's gap over Pandas is smaller than in the current stack and closer to the paper's 14%.

Paper values come from Table 1 and were checked against the arXiv HTML version. I compare directions and relative gaps, not absolute joules (Section 8).

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

I check six results from Table 1 on two datasets, Insurance and MovieLens-1M, in two measurement sessions. For each library, I measure energy and runtime for two stages: the data stage alone, and the full run (data stage + model training).

| Item | Dataset | Downstream model | Session |
| --- | --- | --- | --- |
| C1 | Insurance | Random Forest | 1 |
| C2 | MovieLens-1M | Collaborative filtering (TruncatedSVD) | 1 |
| C3 | Insurance | SVR | 2 |
| C4 | Insurance | XGBoost | 2 |
| C5 | Insurance | TabNet | 2 |
| C6 | MovieLens-1M | Neural collaborative filtering (NCF), GPU energy measured | 2 |
| Version comparison | Insurance | Python 3.8 with the paper's versions (Pandas 1.4.2, Polars 0.10.18, Dask 2022.2.0), compared with the current environment on the same laptop; Python and dependency changes are part of the software-stack comparison | 2 |

ResNet and Mask R-CNN on COCO are not tested, because training them needs more than this laptop's 4 GB of GPU memory and about 14 GB of usable RAM. DRAM energy is not measured either, because the CPU has no DRAM energy counter.

## 3. Data

| Dataset | Source | License | Rows × columns | SHA-256 of downloaded file |
| --- | --- | --- | --- | --- |
| Insurance | Medical Cost Personal Datasets ([Kaggle](https://www.kaggle.com/datasets/mirichoi0218/insurance)) | [Database: Open Database, Contents: Database Contents](https://opendatacommons.org/licenses/dbcl/1-0/) | 1,338 rows × 7 columns | 388eff679557d08ac19f463d025de5e0b4adc482537c8456d19934d78621fd47 |
| MovieLens-1M | [GroupLens](https://grouplens.org/datasets/movielens/1m/) (paper cited) | Custom Non-Commercial / Academic Use | `users.dat`: 6,040 × 5; `movies.dat`: 3,883 × 3; `ratings.dat`: 1,000,209 × 4 | a6898adb50b9ca05aa231689da44c217cb524e7ebd39d264c56e2832f2c54e20 |

## 4. Pipeline definition

The pipeline follows *Algorithm 1: Unified Data Processing Pipeline* (Section 3.1 of the paper), and all three libraries run exactly these steps.

**Insurance (C1, C3–C5)**

1. Load `insurance.csv` into a dataframe (expect 1,338 rows × 7 columns: `age`, `sex`, `bmi`, `children`, `smoker`, `region`, `charges`).
2. Impute missing values (numeric columns: the column mean; text columns: the most frequent value). Insurance has no missing cells, so this step changes nothing, but it still runs so that every library does the same work as in the paper. I use the mean instead of the median because Dask only computes an approximate median.
3. Encode the categorical columns (`sex`: male = 1, female = 0; `smoker`: yes = 1, no = 0; `region`: one-hot, one column per region in alphabetical order).
4. Standardize `age`, `bmi` and `children` (subtract the mean, divide by the sample standard deviation with ddof = 1). The target `charges` is not scaled.
5. Convert to NumPy arrays: `X` with 9 feature columns in a fixed order (`age`, `bmi`, `children`, `sex`, `smoker`, `region_northeast`, `region_northwest`, `region_southeast`, `region_southwest`) and `y` = `charges`. Slice `X` and `y` into mini-batches of 64 rows in file order (21 batches; the last one has 58 rows).

**MovieLens-1M (C2, C6)**

1. Load `ratings.dat` (1,000,209 × 4), `users.dat` (6,040 × 5) and `movies.dat` (3,883 × 3) with the `::` separator.
2. Join ratings to users on `UserID` and to movies on `MovieID`; both joins must be many-to-one and keep all 1,000,209 ratings.
3. Check that each `(UserID, MovieID)` pair is unique; pivot `Rating` to rows = sorted `UserID`, columns = sorted rated `MovieID`, and fill unrated cells with 0, giving a 6,040 × 3,706 `float64` matrix `X`.
4. Slice `X` into batches of 64 user rows in sorted-UserID order without shuffling and sum every batch. The data-stage checksum is the `X` shape, sum, nonzero count and ordered-ID hashes.
5. `--stage full` trains the downstream model on `X`; `--stage data` stops after the checksum. There is no target `y` in this pipeline.

All three backends pass the same arrays to the shared models in [`models.py`](models.py). Insurance uses a fixed 80/20 train/test split (seed 42). SVR fits its target scaler on the training rows only, XGBoost runs on the CPU, and TabNet trains on the GPU for 20 epochs. For MovieLens-1M, C2 uses a 50-component TruncatedSVD and C6 trains NCF on the GPU for five epochs. NCF holds out part of each user's interactions and samples one unrated movie as a negative for each positive; unrated cells are not treated as observed ratings. The code and the raw session records keep the full model settings and output checks.

## 5. Comparisons

- Pandas is the baseline; Polars and Dask are compared with it.
- **Session 1:** 3 libraries × 2 datasets × 2 stages = 12 configurations.
- **Session 2:** 30 configurations (counting the three libraries), each with 1 warm-up and 10 measured runs, scheduled as in Section 7.
  - Current environment (Python 3.12), 24 configurations: `full` stage of C3–C6 (12); `data` stage of Insurance and ML-1M, re-measured so that baselines and the training estimate come from the same session (6); `full` stage of C1 and C2 as reference runs that check whether the laptop still reproduces session 1 (6).
  - Python 3.8 with the paper's versions, 6 configurations: Insurance, Random Forest, `data` and `full` stages, compared with the matching current-environment runs of the same session.
  - GPU power is sampled in every run and judged only for C6.

## 6. Metrics and how they are measured

| Metric | Unit | Tool and formula |
| --- | --- | --- |
| Runtime | s | `power/energy-pkg/` event running time from `perf stat -x,` (nanoseconds / 1e9); `/usr/bin/time -v` keeps wall-clock time for cross-checking |
| CPU package energy | J | `power/energy-pkg/` via `sudo perf stat` |
| CPU core energy | J | `power/energy-cores/` via `sudo perf stat` |
| Net CPU package energy | J | package energy − session idle package power × runtime; core energy is reported separately, not substituted for package energy |
| Training energy (derived) | J | median net package energy of `--stage full` minus that of `--stage data` for the same library and dataset; an estimate, not a separately metered phase |
| Peak memory | kB (convert to MB in analysis) | maximum resident set size from `/usr/bin/time -v` |
| GPU energy | J | Session 2 only. NVML board power (`nvmlDeviceGetPowerUsage`) sampled every 100 ms and integrated over the run window (below) |
| Net GPU energy | J | GPU energy − GPU idle power × window length |
| Disk I/O / usage | Not measured | Storage hardware is reported in Section 10, not treated as a workload metric |

**GPU energy (session 2).** A sampler logs NVML board power every 100 ms for the whole session. I do not use the cumulative NVML energy counter, because in two idle windows on this laptop its change was about 100 times the integral of the power reading. The paper sampled once per second, which is too coarse for runs of a few seconds.

- **Run window:** from 2 s before a run starts to 2 s after it ends, because NVML reports power averaged over about 1 s on this GPU generation.
- **GPU idle power:** the median of the average powers over the five 30 s idle windows of Section 7. The sampler also runs during the CPU idle baseline, so its small CPU cost is part of idle power.
- **Net GPU energy** = integral of power over the window − idle power × window length. It is recorded for every run but judged only for C6.
- **Validity:** a GPU result is accepted only if the GPU validation test (Section 7) passes. NVML board power is not the paper's V100 measurement, so GPU energy is compared by direction only.

The [session-1 runner](scripts/run_measurements.sh) and [session-2 runner](scripts/run_session2.sh) wrap each fresh pipeline process in `perf stat` and `/usr/bin/time -v` and limit BLAS and OpenMP to one thread. Pilot results are stored apart from the completed sessions, and the [session-2 analyzer](scripts/analyze_session2.py) accepts only a complete raw session.

## 7. Procedure

1. **Prepare the machine.** Use AC power and the `balanced` power profile, with Wi-Fi off and no default network route, and close avoidable apps by hand. The runners check the power and network state before each baseline and each run, and the [session-1](results/raw/full-20261025-135703-JICxLk/) and [session-2](results/raw/full-20261116-012318-MJNiIT/) raw records keep the settings they observed.
2. **Validate the measurements.** Before measuring, run the [CPU validation](scripts/validate_measurement.sh), and for session 2 also the [GPU validation](scripts/validate_gpu.py). The pass criteria and results are in [`results/validation/`](results/validation/) and [`results/validation-20261116-001345/`](results/validation-20261116-001345/). Smoke tests must also show the same shapes, feature or ID order and checksums for all three libraries. Pilot runs are not used in the analysis.
3. **Measure each session.** Five 30-second idle readings set the session's baseline. Each configuration then gets one warm-up, which is excluded, and ten measured runs, each in a fresh process. The run order is randomized with seed 42, with a 40-second pause between runs.
4. **Keep the evidence.** Each raw session directory keeps the schedule, inputs, environment, baselines, energy logs and failed attempts. A failed or incomplete session is not used. The [session-2 audit](results/analysis/session2-20261116-012318-MJNiIT/reproducibility.md) checks the completed session.

## 8. Analysis plan

For each configuration (library × dataset × stage), I report the median and interquartile range (IQR) of net energy and runtime over the 10 measured runs. I use the median because one run may be unusually slow when a background process wakes up. I also report the trimmed mean, because the paper uses it.

The exact quartile and bootstrap conventions for session 1 were formalized after that measurement; the [analysis method](results/analysis/method.md) records them. The original C2 outcome categories remain unchanged even though they do not cover the observed Pandas–Polars overlap with Dask clearly higher.

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

**Criteria for C3–C6 and the version comparison, written before session 2.** The C1 and C2 table above is unchanged. Overlapping intervals mean "no clear difference" (Section 8). A tie satisfies a "similar" condition, fails a "lowest", "highest" or "<" condition, and is never counted as a reversal. For C3–C6, runtime is reported but does not change an outcome.

For C5 and C6, the paper's order (C5: Polars < Dask < Pandas; C6: Polars < Pandas < Dask) is checked on its three library pairs. A pair *holds* if the paper's lower library is clearly lower, is *reversed* if it is clearly higher, and is *unclear* if the intervals overlap. C6 is judged separately on net CPU package energy and net GPU energy; the GPU outcome is "Not tested" if the GPU measurement cannot be validated.

| Outcome | C3 (SVR), C4 (XGBoost) | C5 (TabNet), C6 (NCF) |
| --- | --- | --- |
| Reproduced | No clear difference between Pandas and Polars, **and** Dask has the highest net energy, clearly above both | All three pairs hold |
| Partially reproduced | Only one of the two parts holds | At least one pair holds and none is reversed |
| Not reproduced | Neither part holds | A pair is reversed, or no pair holds |
| Not tested | Not run before the report is written | Not run before the report is written |

**Version comparison** (Insurance, Random Forest; Python 3.8 with the paper's versions versus the current environment). There is no paper claim to reproduce, so I apply the C1 criteria to the `full` stage of each environment in the same session and compare the two outcomes (Reproduced > Partially reproduced > Not reproduced). Python 3.8 is *closer to the paper* if its outcome is higher, *no change* if equal, *further* if lower, and *not tested* if its environment cannot complete the runs. Python, dependencies and library versions change together, so any difference is attributed to the software stack, not to one library version.

**Stop and fix first** (no conclusion is drawn until the problem is fixed):

- an energy-measurement validation test fails (the `sleep` test, the 2× CPU-loop test or, in session 2, the GPU test);
- the three libraries give different checksums or a different feature-column order;
- the coefficient of variation (standard deviation / mean) of net energy within one configuration is above 10% (net GPU energy: C6 only).

The hypotheses in Section 1 are checked separately in the report; they do not change these outcomes.

## 10. Environment

| Item | Value |
| --- | --- |
| CPU | Intel Core i5-12500H (12 cores: 4 performance + 8 efficiency; 16 threads) |
| RAM | 16 GB |
| GPU | NVIDIA GeForce RTX 3050 Laptop, 4 GB; NVIDIA kernel module 615.71.09 (from `/proc/driver/nvidia/version`, Oct 25, 2026) |
| OS / kernel | Ubuntu 26.04.1 LTS; session-1 kernel `7.0.0-38-generic`; current kernel `7.0.0-42-generic` on Nov 16, 2026; CPU measurement validation repeated and passed before the session-2 pilot |
| Storage | WD Green SN350 500 GB NVMe (`/dev/nvme1n1p2`, ext4); repository and raw data on this volume |
| perf | 7.0.14 |
| Python | 3.12.14 (via uv) |
| Library versions | Locked in `requirements.lock`: Pandas 3.0.6, Polars 2.0.0, Dask 2026.8.0, pyarrow 26.0.0, numpy 2.5.4, scikit-learn 1.9.1, XGBoost 3.4.1, PyTorch 2.15.0, pytorch-tabnet 4.1.0 and nvidia-ml-py 13.615.71 |
| Version-comparison environment | Python 3.8.12 with Pandas 1.4.2, Polars 0.10.18 and Dask 2022.2.0; exact transitive dependencies in the Python 3.8 entries of `requirements.lock` |
| RAPL domains | package, core, uncore, psys; **no DRAM** |

## 11. Known differences from the paper and threats to validity

- A laptop instead of a workstation, and current library versions instead of the 2022 versions (the version comparison isolates part of the version effect).
- Insurance has 1,338 rows, while the paper reports 1,000 records; I use all 1,338 rows and do not subsample to match.
- RAPL measures the whole CPU package, not only the pipeline process; the idle baseline and closed apps reduce this noise.
- The CPU has no DRAM energy domain, so my CPU energy is not the paper's energy-cores + energy-ram sum.
- Possible thermal throttling: temperature is recorded before each run, but clock throttling is not measured directly.
- Disk I/O is not measured.
- One-thread BLAS/OpenMP settings and the laptop's power policy may change timings relative to the paper, but they are fixed across all local configurations.
- The paper contradicts itself in places. It states both "five runs, trimmed mean and 95% CI" and "mean of four measured runs", and its Insurance row count differs from the cited dataset. Section 4.1 says TabNet requires a GPU, but Section 3.2.2 lists only ResNet, Mask R-CNN and NCF as GPU experiments. Table 1 also reports GPU energy for SVR and XGBoost without naming their device.
- The paper does not report hyperparameters, the train/test split, the CF algorithm, or the architecture and device of any model; the choices in Section 4 are mine.
- Session 2 was planned after the session-1 results were known. Its claims, hypotheses, settings and criteria were written before any session-2 measurement.

## 12. Use of AI assistance

The pipeline code was written with AI assistance one step at a time, then reviewed, run and annotated by the author. Sections 2, 4, 7, 8 and 9 of this protocol and the scripts in `scripts/` were drafted with AI assistance from the author's decisions and terminal commands, then reviewed by the author; the current structure of this document was revised the same way on Oct 28, 2026. The claims, hypotheses, data choices and all measurements are the author's own.
