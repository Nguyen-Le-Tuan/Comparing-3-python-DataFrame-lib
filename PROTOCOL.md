# Replication Protocol: Energy Use of Pandas, Polars and Dask on a Laptop

| Field | Value |
| --- | --- |
| Author | Le Tuan Nguyen (University at Buffalo, CS) |
| Status | **v1 FROZEN** (C1–C2): content committed before the first session in `4badf06`, status set in `5881ae5` · **v2 DRAFT** (C3–C6 and version comparison): to be FROZEN before the second session |
| Last updated | Oct 28, 2026 |
| Study type | Small-scale **replication**:personal laptop, updated library |
| Repository | https://github.com/Nguyen-Le-Tuan/Comparing-3-python-DataFrame-lib |

**How to read this document.** Version 1 (Oct 25, 2026) covers C1 and C2. Version 2 (Oct 28, 2026) extends the same study to the remaining Insurance and ML-1M models and adds a version comparison. Text added in v2 is marked **[v2]**; v1 text that v2 replaces is struck through, not deleted. Section 13 lists every change made after the v1 freeze.

## 0. Original Paper information

- **Paper:** *Energy Consumption of Dataframe Libraries for End-to-End Deep Learning Pipelines: A Comparative Analysis*.
- **Full author list:** Punit Kumar, Asif Imran, and Tevfik Kosar
- **DOI:** 10.48550/arXiv.2511.08644
- **Reported Setup:** 16-core / 32-thread CPU at 2.10 GHz, 128 GB RAM, NVIDIA Tesla V100 32 GB, 1TB NVMe SSD, Ubuntu 20.04 LTS with Linux kernel 5.4; Python 3.8.12, Pandas 1.4.2, Polars 0.10.18, Dask 2022.2.0. CPU energy from `perf stat` (energy-cores + energy-ram); GPU energy from pynvml sampled every second. One warm-up run, then five measured runs; 40s idle between runs; a fresh process per run; various run order.

## 1. My claim before testing

<!-- Hai claim, viết lại bằng lời của mình. C1 bắt buộc (trước email 29/10). C2 làm cùng C1 trong tuần 19–25/10 (quyết định 19/10).
Gợi ý C1: Insurance + Random Forest: Pandas ≈ Polars về CPU energy (146,8 J so với 146,8 J), Dask cao hơn khoảng 14% (167,4 J) và chạy lâu nhất. Với SVR và XGBoost, Dask cao hơn khoảng 20–22%; ngoại lệ là TabNet.
Gợi ý C2: ML-1M + CF: Polars < Pandas < Dask (1.437 / 3.328 / 3.748 J). -->

- **Claim C1:** Testing the energy consumption of Pandas, Polars and Dask on the Insurance Dataset. The paper reported that by using *Random Forest*, Pandas and Polars use similar CPU energy (146.8 J) while Dask uses more 14% (167.4 J); however, on SVR and XGBoost, Dask is even higher (20-22%).
- **Claim C2:** Testing on the MovieLens 1M will result in energy uses: Polars < Pandas < Dask.
- **Claim C3 [v2] (Insurance, SVR):** _To be written by the author before measurement._
- **Claim C4 [v2] (Insurance, XGBoost):** _To be written by the author before measurement._
- **Claim C5 [v2] (Insurance, TabNet):** _To be written by the author before measurement._
- **Claim C6 [v2] (ML-1M, NCF):** _To be written by the author before measurement._
- **Where in the paper:** Table 1; Section 4.1 and Figure 5 (Insurance); Section 4.3 and Figure 3a (ML-1M)
- **My hypothesis before running:** Because the Insurance dataset is in tabular format and only has 1k rows while the MovieLens is 1M samples, I assume that Pandas will perform the best in the Insurance Dataset while the Polars will be the best in the ML-1M. I have these assumptions because I already knew that Pandas is still advantageous on small data while Polars (which written in Rust) will outperform Pandas on larger data (from several GB to hundred GB).  <!-- Bạn đoán kết quả trên laptop sẽ thế nào, và vì sao. Viết trước khi chạy, không sửa sau. -->
- **My hypothesis for C3–C6 and the version comparison [v2]:** _To be written by the author before the second session; not edited after it starts._

**Paper values for C3–C6 [v2]** (Table 1, checked against the arXiv HTML version; compared by direction and relative gap, not absolute joules):

| Model | Dataset | Backend | Runtime (s) | CPU energy (J) | GPU energy (J) |
| --- | --- | --- | ---: | ---: | ---: |
| SVR | Insurance | Pandas | 0.160 | 87.706 | 8.65 |
| SVR | Insurance | Polars | 0.168 | 87.712 | 7.50 |
| SVR | Insurance | Dask | 0.364 | 106.572 | 12.14 |
| XGBoost | Insurance | Pandas | 0.204 | 96.336 | 8.67 |
| XGBoost | Insurance | Polars | 0.192 | 96.218 | 8.65 |
| XGBoost | Insurance | Dask | 0.410 | 115.654 | 15.02 |
| TabNet | Insurance | Pandas | 1.688 | 447.914 | 106.42 |
| TabNet | Insurance | Polars | 1.826 | 245.066 | 113.21 |
| TabNet | Insurance | Dask | 1.844 | 334.002 | 109.98 |
| NCF | ML-1M | Pandas | 17.916 | 1,801.422 | 339.39 |
| NCF | ML-1M | Polars | 2.526 | 497.992 | 142.76 |
| NCF | ML-1M | Dask | 64.871 | 6,313.152 | 2,139.67 |

## 2. Scope

In this replication, I check two results from Table 1 of the paper on two datasets, Insurance and MovieLens-1M. For each library, I measure the energy consumption and the time it takes for both the **data stage alone** and **the full run (data stage + model training)**.

- **Required (C1):** Insurance with Random Forest.
- **Secondary (C2):** MovieLens-1M with Collaborative Filtering (CF), measured in the same full session as C1.
- ~~**Deciding later:** Support Vector Regression (SVR) and XGBoost on Insurance; a small Neural Collaborative Filtering (NCF) model on the GPU.~~
- ~~**Not tested:** TabNet; ResNet and Mask R-CNN on COCO, because training them needs far more GPU memory and time than my laptop (4 GB VRAM, about 14 GB of usable RAM) and my schedule allow; DRAM energy, because my CPU does not expose a DRAM energy counter.~~
- **Required [v2] (C3–C5):** Insurance with SVR, XGBoost and TabNet.
- **Required [v2] (C6):** MovieLens-1M with Neural Collaborative Filtering (NCF), with GPU energy measured.
- **Required [v2] (version comparison):** Insurance run in a Python 3.8 environment with the paper's library versions (Pandas 1.4.2, Polars 0.10.18, Dask 2022.2.0), to separate the effect of library versions from that of hardware. Configurations to be fixed in Section 5 before measurement.
- **Not tested [v2]:** ResNet and Mask R-CNN on COCO, because training them exceeds this laptop's 4 GB of GPU memory and about 14 GB of usable RAM; DRAM energy, because my CPU does not expose a DRAM energy counter.

## 3. Data

| Dataset | Source | License | Rows × columns | SHA-256 of downloaded file |
| --- | --- | --- | --- | --- |
| Insurance | Medical Cost Personal Datasets ([Kaggle](https://www.kaggle.com/datasets/mirichoi0218/insurance)) | [Database: Open Database, Contents: Database Contents](https://opendatacommons.org/licenses/dbcl/1-0/) | 1,338 rows x 7 columns <!-- paper ghi 1.000 dòng; đếm lại, lệch thì ghi vào mục 11 --> | 388eff679557d08ac19f463d025de5e0b4adc482537c8456d19934d78621fd47|
| MovieLens-1M | [GroupLens](https://grouplens.org/datasets/movielens/1m/) (paper cited) | Custom Non-Commercial / Academic Use | `users.dat`: 6,040 rows × 5 columns; `movies.dat`: 3,883 rows × 3 columns; `ratings.dat`: 1,000,209 rows × 4 columns  | a6898adb50b9ca05aa231689da44c217cb524e7ebd39d264c56e2832f2c54e20 |


## 4. Pipeline definition

Based on *Algorithm 1: Unified Data Processing Pipeline* (Section 3.1 of the paper). All three libraries must do exactly these steps.

**Insurance (C1; C3–C5 [v2])**

1. Load `insurance.csv` into a dataframe (expect 1,338 rows × 7 columns: `age`, `sex`, `bmi`, `children`, `smoker`, `region`, `charges`).
2. Take the raw dataframe and impute missing values (numeric columns: the column mean; text columns: the most frequent value), producing a complete dataframe. Insurance has no missing cells, so this step changes nothing, but it still runs so that every library does the same work as in the paper. I use the mean instead of the median because Dask only computes an approximate median.
3. Take the complete dataframe and encode the categorical columns (`sex`: male = 1, female = 0; `smoker`: yes = 1, no = 0; `region`: one-hot, one column per region in alphabetical order), producing a numeric dataframe.
4. Take the numeric dataframe and standardize `age`, `bmi` and `children` (subtract the mean, divide by the sample standard deviation with ddof = 1), producing a scaled dataframe. The target `charges` is not scaled.
5. Take the scaled dataframe and convert it to NumPy arrays: `X` with 9 feature columns in a fixed order (`age`, `bmi`, `children`, `sex`, `smoker`, `region_northeast`, `region_northwest`, `region_southeast`, `region_southwest`) and `y` = `charges`. Then slice `X` and `y` into mini-batches of 64 rows in file order (21 batches; the last one has 58 rows).

**MovieLens-1M (C2; C6 [v2])**:

1. Load `ratings.dat` (1,000,209 × 4), `users.dat` (6,040 × 5) and `movies.dat` (3,883 × 3), using the `::` separator → three dataframes.
2. Join ratings to users on `UserID` and to movies on `MovieID`, validating many-to-one joins and preserving all 1,000,209 ratings → one joined dataframe.
3. Check that each `(UserID, MovieID)` pair is unique; pivot `Rating` to rows = sorted `UserID`, columns = sorted rated `MovieID`, and fill unrated cells with 0 → a 6,040 × 3,706 `float64` matrix `X`.
4. Slice `X` into sorted-UserID-order batches of 64 user rows without shuffling and sum every batch → the data-stage checksum (`X` shape, sum, nonzero count, and ordered-ID hashes).
5. For `--stage full`, fit `TruncatedSVD(n_components=50, random_state=42)` to the whole `X` matrix → a 6,040 × 50 user-factor matrix. For `--stage data`, stop after the checksum; there is no target `y` or train/test split in this C2 pipeline.

**Rules for both datasets**

- **Output checksum:** at the end, the program prints the shapes of the output arrays and the sum of all their elements. The sum is computed over the mini-batches, so every batch is actually used. All three libraries must give the same shapes, the same feature-column order and sums that differ by less than 1e-6 before any energy comparison.
- "For ML-1M, compare the ordered UserID and MovieID axes as well as the matrix checksum; unlike Insurance, this pipeline has no y array".
- **Library-specific choices** (fixed for all runs):
  - Pandas: eager, `pd.read_csv` with default settings. 
  - Polars: lazy, `pl.scan_csv` and expressions, with a single `.collect()` before the NumPy conversion, because the paper credits Polars' lazy expressions for its efficiency. 
  For ML-1M, Polars scans and joins lazily, collects the joined rows once, then performs the dynamic user–movie pivot eagerly in Polars before NumPy conversion. The rated MovieID columns are not known before scanning, so this is not a fully lazy pivot.
  - Dask: `dd.read_csv` with the default block size and the default threaded scheduler; the number of partitions is printed at runtime. Categorical columns are made "known" with `.categorize()` before one-hot encoding, because Dask needs every category in advance.
For ML-1M, Dask reads :: with the Python CSV engine and default block size, joins the three tables, checks joined-row and unique user–movie-pair counts, categorizes MovieID, then uses pivot_table(aggfunc="first"). Because pairs are unique, this produces the same rating matrix as the Pandas pivot. The computed matrix is sorted by numeric UserID and MovieID before NumPy conversion.
- **Randomness:** mini-batches are taken in file order without shuffling, so the data stage has no randomness. Insurance uses seed 42 for its train/test split and Random Forest; MovieLens-1M uses seed 42 for TruncatedSVD and has no train/test split. The measurement schedule is independently randomized with seed 42 (Section 7).
- **Two stages per configuration:** `--stage data` runs only the dataframe part; `--stage full` runs the dataframe part and then trains the downstream model. Training energy is estimated as *full* − *data*.
- **Downstream models** (the paper does not report its hyperparameters, so these are my choices):
  - Insurance: scikit-learn `RandomForestRegressor` with default hyperparameters (100 trees, one CPU core) and `random_state=42`, trained on 80% of the rows (`train_test_split` with `test_size=0.2`, `random_state=42`: 1,070 training rows, 268 test rows). Random Forest trains on the whole training array; the mini-batch step is kept only to follow the paper. The test R² is printed as a sanity check.
  - MovieLens-1M: CF as a factorization of the user × movie matrix with `TruncatedSVD(n_components=50, random_state=42)`.
  - ~~NCF (optional, GPU): defined later, only if Step 7 is done.~~
  - **[v2]** The data stage above is unchanged for C3–C6. Insurance models use the same 80/20 split with `random_state=42` as Random Forest. Settings to be fixed by the author before the pilot:
    - SVR (C3): kernel and other hyperparameters; whether the target `charges` is scaled.
    - XGBoost (C4): hyperparameters, number of threads, `random_state`.
    - TabNet (C5): hyperparameters, number of epochs, batch size, device (CPU or GPU).
    - NCF (C6): input derived from the rating matrix `X` above; architecture, embedding size, loss, epochs, batch size, device.

## 5. Comparisons

- **Baseline:** Pandas.
- **Compared:** Polars, Dask.
- **Configurations (session 1, v1):** 3 libraries × 2 datasets × 2 stages = 12 configurations.
- **Configurations (session 2) [v2]:** _To be decided by the author before measurement:_ the new `--stage full` configurations for C3–C6; which `--stage data` configurations are re-measured in the same session; whether Random Forest and TruncatedSVD are re-run as within-session reference points; the version-comparison configurations; and the resulting numbers of warm-ups and measured runs (one warm-up and ten measured runs per configuration, as in Section 7).

## 6. Metrics and how they are measured

| Metric | Unit | Tool and formula |
| --- | --- | --- |
| Runtime | s | `power/energy-pkg/` event running time from `perf stat -x,` (nanoseconds divided by 1e9); `/usr/bin/time -v` also retains elapsed wall-clock time for cross-checking |
| CPU package energy | J | `power/energy-pkg/` via `sudo perf stat` |
| CPU core energy | J | `power/energy-cores/` via `sudo perf stat` |
| Net CPU package energy | J | package energy − session idle package power × runtime; core energy is reported separately and is not substituted for package energy |
| Training energy (derived) | J | median net package energy of `--stage full` minus median net package energy of `--stage data` for the same library and dataset; this is an estimate, not a separately metered training phase |
| Peak memory | kB (convert to MB in analysis) | maximum resident set size from `/usr/bin/time -v` |
| GPU energy | J | ~~Not measured in C1/C2. A GPU measurement method must be defined before any optional NCF experiment; the Step 6 script does not sample GPU power~~ **[v2]** Measured in session 2 with NVML: method (cumulative energy counter or fixed-interval power sampling) and GPU idle baseline to be fixed by the author before measurement; CPU energy stays net `power/energy-pkg/` |
| Disk I/O / usage | Not measured | The Step 6 script does not record per-run disk I/O or disk footprint; storage hardware is reported in Section 10, not treated as a workload metric |

The pre-registered measurement runner is `scripts/run_measurements.sh`. It calls `perf stat` and `/usr/bin/time -v` around each fresh pipeline process, records both RAPL domains, and checks the pipeline output. It sets `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, and `PYTHONDONTWRITEBYTECODE=1` for every run. The script is launched once for the full session:

```bash
sudo ./scripts/run_measurements.sh
```

An optional preflight pilot uses `sudo ./scripts/run_measurements.sh --pilot pandas insurance data`. Its results are stored separately and excluded from the final analysis. No pilot or full run had been performed when this protocol update was written.

**[v2]** For session 2, the runner, pipeline and analysis script are extended for C3–C6, GPU energy and the version comparison. The changes are listed here before the v2 freeze.

## 7. Procedure

Before the full session, review the optional pilot output and this protocol. If no method change is needed, change the status above to `FROZEN on 2026-10-25` and commit the protocol and measurement runner before starting the 120 measured runs. If the pilot reveals a problem, fix and document it before freezing; pilot results never enter the final analysis.

1. **Before measuring:** Connect AC power for the whole full session; close browser, IDE, and other avoidable foreground/background apps; enable Airplane mode. The full runner requires Wi-Fi disabled and no IPv4/IPv6 default route. Keep the CPU settings fixed for every run: governor `powersave` on all 16 logical CPUs (`intel_pstate`, active mode), CPU0 EPP `balance_performance`, power profile `balanced` (laptop Balanced Mode), and Turbo Boost enabled (`no_turbo=0`). The runner checks these settings before each full-session baseline and pipeline run and records system state before and after the session. Closing apps is a manual action, not something the script can verify. Do not present the current app-open state as the full-session state.
2. **Idle baseline:** For each full session, the runner measures `power/energy-pkg/` during `sleep 30` five times with a 40 s pause after each; idle power is the median of the five average package powers. The earlier Step 2 validation baseline is evidence that the meter worked, not a substitute for this new session baseline. The optional pilot uses only one baseline and is not included in final analysis.
3. **Measurement validation tests** (pass limits written in `results/validation/criteria.txt` before the first measurement; both must pass before any pipeline is measured):
   - Test 1: the energy of `sleep 10` is within 15% of idle power × elapsed time.
   - Test 2: a single-threaded Python loop, `sum(i*i for i in range(N))` with N = 400,000,000 (about 15 s), is run with N and 2N iterations; the 2N/N ratio of net energy must be between 1.8 and 2.2.
   - Scripts: `scripts/validate_measurement.sh` (measures) and `scripts/analyze_validation.sh` (computes).
   - Result on Oct 19, 2026: idle power 4.776 W (five runs, 4.755 to 4.814 W); Test 1 error 0.38% (pass); Test 2 ratio 1.854 (pass). Files and notes: `results/validation/`.
   - The tests are repeated if the kernel, BIOS or power settings change.
4. **Data-pipeline smoke test** (before the first full energy session):
   - Run both Insurance and MovieLens-1M in `data` and `full` stages through Pandas, Polars, and Dask.
   - Check input shape, columns, and missing values where applicable; then compare output shapes, feature or ID order, and checksums across libraries. For MovieLens-1M also check the nonzero rating count and 6,040 × 50 SVD output in `full` mode.
   - Smoke-test evidence is retained under `results/smoke_test/`: the Insurance three-library, two-stage comparison is summarized in `insurance_backends_2026-10-24.md`, and all six MovieLens-1M logs agree on matrix shape, sum, nonzero count, and ordered-ID hashes. The full runner rechecks key output checksums during measurement.
5. **Runs per configuration:** The runner creates 12 configurations (3 libraries × 2 datasets × 2 stages). It first executes one warm-up of each configuration (12 warm-ups, excluded from analysis), then 10 rounds in which each configuration appears once (120 measured runs). Order within warm-ups and each round is pseudorandomized with schedule seed 42, which is separate from model seed 42. Each run starts a fresh Python process. There is a 40 s pause between pipeline runs; the CPU package temperature is recorded before each run.
6. **Raw data and failures:** A unique directory under `results/raw/full-.../` stores the schedule, input SHA-256 values, Git state, pre/post CPU/network/power state, idle baseline, `runs.csv`, and each run's `perf.csv`, `time.txt`, stdout, and stderr. Warm-ups and failed attempts remain in the raw data. The script stops on a failed run and marks the session `INCOMPLETE`; such a session is not used as the final 120-run dataset. A pilot is stored under `results/raw/pilot-.../` and excluded from final analysis. No result is selectively deleted after inspection.
7. **Session-specific report (after the full run):** Add a brief `session_notes.md` inside that `results/raw/full-.../` directory. Manually state whether the browser, IDE, and other avoidable apps were closed; whether AC and Airplane mode were maintained; and any interruptions, updates, thermal concerns, or reruns. Refer to `cpu_state_before.txt`, `cpu_state_after.txt`, `idle/`, and `runs.csv` for observed machine settings and readings instead of copying the current app-open state into this protocol.

**Session 2 [v2].** The second session follows steps 1–7 above with its own idle baseline. Before it starts: the new models pass the smoke test in step 4 (same checksums across libraries, every model runs in `--stage full`); the version-comparison environment passes the same smoke test; a GPU measurement validation test, to be defined by the author with its pass limit, passes; and a pilot of the new configurations is run and excluded from analysis. Then the v2 status above is set to FROZEN and committed.

## 8. Analysis plan

For each configuration (library × dataset × stage), I report the median and the interquartile range (IQR) of net energy and runtime over the 10 measured runs. I use the median because one run may be unusually slow when a background process wakes up. I also report the trimmed mean, because the paper uses it.

- **Decision rule:** two libraries "differ" only if the 95% bootstrap confidence intervals of their median net energy do not overlap (10,000 resamples, seed 42); otherwise I report "no clear difference". The same rule is used for runtime.
- **Comparison with the paper:** my laptop and library versions differ from the paper's, so I compare the **direction** of the results (which library uses more energy, and by roughly what percentage), not the absolute joules. Table 1 reports end-to-end numbers, so this comparison uses `--stage full`.
- **Ranking on my laptop:** I also rank Pandas, Polars and Dask by median net energy and report my ranking next to the paper's.
- **Decomposition:** the share of the data stage in the end-to-end energy, *data* / *full*.
- **[v2]** The same rules apply to C3–C6 and to the version comparison. Results from different sessions are compared only by direction and ratio, because each session has its own idle baseline.

## 9. Outcome criteria

Written before the comparative pipeline measurements. Each claim is judged on `--stage full` with the decision rule in Section 8.

| Outcome | C1: Insurance, Random Forest | C2: MovieLens-1M, CF |
| --- | --- | --- |
| Reproduced | No clear difference between Pandas and Polars in net energy, **and** Dask has the highest net energy and the longest runtime, clearly different from both | Polars < Pandas < Dask in net energy, with each difference clear |
| Partially reproduced | Only one of the two parts holds | Polars is the lowest, but the order of Pandas and Dask is unclear or reversed |
| Not reproduced | Neither part holds | Polars is not the lowest |
| Not tested | — | Not run before the report is written |

**Stop and fix first** (no conclusion is drawn until the problem is fixed):

- an energy-measurement validation test fails (the `sleep` test or the 2× CPU-loop test);
- the three libraries give different checksums or a different feature-column order (smoke test in Section 7);
- the coefficient of variation (standard deviation / mean) of net energy within one configuration is above 10%.

**Outcome criteria for C3–C6 and the version comparison [v2]:** _To be written by the author before the second session,_ using the decision rule in Section 8. Each criterion must state the outcome when the 95% intervals of two libraries overlap (the case left open for C2; see Section 13). The stop-and-fix rules above also apply to session 2, together with the GPU validation test in Section 7.

My hypothesis in Section 1 is checked separately in the report; it does not change these outcomes.

## 10. Environment

| Item | Value |
| --- | --- |
| CPU | Intel Core i5-12500H (12 cores: 4 performance + 8 efficient, 16 threads) |
| RAM | 16 GB |
| GPU | NVIDIA GeForce RTX 3050 Laptop, 4 GB; NVIDIA kernel module 615.71.09 (verified from `/proc/driver/nvidia/version` on Oct 25, 2026); CUDA UMD 13.4 reported by the author, not independently verified in this app session |
| OS / kernel | Ubuntu 26.04.1 LTS, kernel 7.0.0-38-generic |
| Data/results storage | WD Green SN350 500GB NVMe (`/dev/nvme1n1p2`, ext4); repository and raw data reside on this volume |
| perf | 7.0.14 |
| Python | 3.12.14 (via uv) |
| Library versions | Locked in `requirements.lock`; summary: Pandas 3.0.6, Polars 2.0.0, Dask 2026.8.0, pyarrow 26.0.0, numpy 2.5.4, scikit-learn 1.9.1. |
| RAPL domains available | package, core, uncore, psys; **no DRAM** |
| Version-comparison environment [v2] | Python 3.8 with Pandas 1.4.2, Polars 0.10.18, Dask 2022.2.0; exact versions recorded once installed |

## 11. Known differences from the paper and threats to validity

- Laptop instead of workstation.
- Current library versions instead of the 2022 versions.
- My *Insurance* dataset has 1,338 rows, while the paper's *Experimental Setup* reports 1,000 records; this difference is retained rather than silently subsampling.
- RAPL measures the whole CPU package, not only our process; other processes add noise (mitigated by the idle baseline and closing apps).
- No DRAM energy domain, so CPU energy is not the paper's energy-cores + energy-ram sum.
- Possible thermal throttling on a laptop: the runner records package temperature before each run, but does not directly measure clock throttling. High temperature or drift must therefore be discussed as a limitation, not treated as ruled out.
- Disk I/O and GPU energy are outside the measured C1/C2 metrics; filesystem free space and GPU model are hardware context, not substitutes for those workload measurements.
- The one-thread BLAS/OpenMP settings and this laptop's power policy may change timings relative to the paper, but they remain fixed across all local configurations.
- Inconsistencies in the paper: it states both "five runs, trimmed mean and 95% CI" and "mean of four measured runs"; the Insurance row count differs from the cited dataset.
- The paper does not report hyperparameters, the train/test split or the CF algorithm; the choices in Section 4 are ours.
- **[v2]** The paper does not state hyperparameters, epochs, batch size, architecture or training device for SVR, XGBoost, TabNet or NCF. Section 4.1 says TabNet requires a GPU, but Section 3.2.2 lists only ResNet, Mask R-CNN and NCF as GPU experiments; Table 1 also reports GPU energy for SVR and XGBoost without naming their device.
- **[v2]** The decision to add C3–C6 and the version comparison was made after the C1/C2 results were known. The new claims, hypotheses and criteria are written before any measurement of the new models.

## 12. Use of AI assistance

Pipeline code is written with AI assistance, one step at a time, then reviewed, run and annotated by the author. Sections 2, 4, 7, 8 and 9 of this protocol and the scripts in scripts/ were drafted with AI assistance from the author’s decisions and terminal commands, then reviewed by the author. The claims, hypothesis, data choices and all measurements are the author’s own. **[v2]** The v2 structure of this document (merging the extension into Sections 1–12) was drafted with AI assistance at the author's direction; the v2 claims, hypotheses, settings and criteria are written by the author.

## 13. Version history and changes after the v1 freeze

Every change after the v1 freeze is listed here with its date and reason. Earlier versions remain in the Git history.

| Date | Change | Reason |
| --- | --- | --- |
| 2026-10-25 | Analysis conventions set in `scripts/analyze_results.py` (described in `results/analysis/method.md`), after the full run: percentile bootstrap interval for the median; quartiles with linear interpolation; 10% trimmed mean drops the lowest and highest of the 10 values; CV = sample standard deviation / mean net energy; data share and training estimate use stage medians, not paired run differences; peak memory reported in MiB (kB / 1024) instead of MB. | These conventions fill in details not specified by the frozen protocol. The script reports measurements and derived statistics; I interpret C1 and C2 separately. |
| 2026-10-25 | For C2, I report the outcome as "not covered by the pre-registered criteria" when Pandas and Polars have overlapping energy CIs while Dask is clearly higher. I leave the original Section 9 categories unchanged. | Section 9 does not specify what "Polars is the lowest" means when the Pandas–Polars difference is unclear. Its partial-outcome row also requires Pandas–Dask to be unclear or reversed, which is not observed. Assigning a standard label would force this result into a row whose conditions do not fit. |
| 2026-10-28 | v2 started: scope extended to SVR, XGBoost and TabNet on Insurance (C3–C5), NCF on ML-1M (C6), GPU energy and a version comparison with the paper's library versions. TabNet, listed as "Not tested" in v1, is now in scope; NCF and the optional GPU work are now required. C1, C2 and their reported outcomes are unchanged. First recorded as a separate Section 14 (commit `7fde5a3`). | Author's decision on Oct 28, 2026 to prioritize a complete comparison over the original email date. The new claims, hypotheses, model settings and outcome criteria are written before any measurement of these models. |
| 2026-10-28 | Document restructured: the former Section 14 was merged into Sections 1–12 with **[v2]** marks; superseded v1 text is struck through, not deleted. | So the protocol reads in one linear order. |
