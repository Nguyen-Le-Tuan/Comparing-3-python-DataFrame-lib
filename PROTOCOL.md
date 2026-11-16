# Replication Protocol: Energy Use of Pandas, Polars and Dask on a Laptop

| Field | Value |
| --- | --- |
| Author | Le Tuan Nguyen (University at Buffalo, CS) |
| Study type | Small-scale replication on a personal laptop with current library versions |
| Session 1 (C1–C2) | Registered before measurement in commit `4badf06`; status set to FROZEN in `5881ae5`; measured Oct 25, 2026 |
| Session 2 (C3–C6, version comparison) | FROZEN on Nov 16, 2026 at Git tag `session2-frozen-20261116`, before any official session-2 measurement. Model smoke tests, GPU validation and repeated CPU validation passed; excluded TabNet and NCF pilots were reviewed |
| Repository | https://github.com/Nguyen-Le-Tuan/Comparing-3-python-DataFrame-lib |

## 0. Original paper

The paper is *Energy Consumption of Dataframe Libraries for End-to-End Deep Learning Pipelines: A Comparative Analysis* by Punit Kumar, Asif Imran and Tevfik Kosar (DOI 10.48550/arXiv.2511.08644).

Its reported setup is a 16-core / 32-thread CPU at 2.10 GHz, 128 GB RAM, an NVIDIA Tesla V100 32 GB, a 1 TB NVMe SSD and Ubuntu 20.04 LTS with Linux kernel 5.4, running Python 3.8.12, Pandas 1.4.2, Polars 0.10.18 and Dask 2022.2.0. CPU energy comes from `perf stat` (energy-cores + energy-ram), and GPU energy from pynvml sampled every second. The paper uses one warm-up run followed by five measured runs, with 40 s idle between runs, a fresh process for each run and a varied run order.

## 1. Claims and hypotheses

- **C1:** Testing the energy consumption of Pandas, Polars and Dask on the Insurance Dataset. The paper reported that by using *Random Forest*, Pandas and Polars use similar CPU energy (146.8 J) while Dask uses more 14% (167.4 J); however, on SVR and XGBoost, Dask is even higher (20-22%).
- **C2:** Testing on the MovieLens 1M will result in energy uses: Polars < Pandas < Dask.
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
  - SVR (C3): scikit-learn `SVR` with its defaults: `kernel="rbf"`, `C=1.0`, `epsilon=0.1`, `gamma="scale"`. No tuning, and no value is chosen from test-set scores. `charges` is standardized inside the shared training function with `TransformedTargetRegressor(regressor=SVR(), transformer=StandardScaler())`: the scaler is fitted on the 1,070 training targets only, and predictions are inverse-transformed before test R² and RMSE are computed. The three dataframe backends still return the unscaled `charges`, so the data stage is identical to session 1. Features, the 80/20 split and the mini-batch step are unchanged. With `gamma="scale"`, gamma is computed from the training features (0.2278 in a check on the training rows only) and is the same for all three libraries.
  - XGBoost (C4): `xgboost.XGBRegressor(objective="reg:squarederror", booster="gbtree", n_estimators=100, max_depth=6, learning_rate=0.1, subsample=1.0, colsample_bytree=1.0, tree_method="hist", device="cpu", n_jobs=1, random_state=42)`. Other parameters use the locked package's defaults. Fit once on the same 1,070 training rows as C1 and C3, without an evaluation set, early stopping or tuning; predict the 268 held-out rows and print test R² and RMSE in the original `charges` units. `X` and `y` remain `float64` from the shared data stage. The model must report CPU execution, so a GPU fallback is not accepted.
  - TabNet (C5): `pytorch_tabnet.tab_model.TabNetRegressor` with `n_d=8`, `n_a=8`, `n_steps=3`, `gamma=1.3`, `mask_type="sparsemax"`, `lambda_sparse=0.001`, `seed=42`, `device_name="cuda"`, Adam optimizer with learning rate `0.02`, and otherwise the locked package's defaults. Convert the shared `X` to `float32` for training; standardize `charges` using the mean and standard deviation of the 1,070 training targets only, and pass a `float32` target array shaped `(1070, 1)`. Fit for exactly 20 epochs with `batch_size=256`, `virtual_batch_size=64`, `patience=0`, no evaluation set, `num_workers=0`, `drop_last=False` and `compute_importance=False`. No early stopping or tuning. Inverse-transform predictions and print held-out R² and RMSE in the original `charges` units. The model must run on the RTX 3050 (`cuda:0`); stop if CUDA is unavailable or the model uses the CPU. The data-stage `y` remains unscaled, and its existing 64-row slices are separate from TabNet's training batches.
  - NCF (C6): use the existing 6,040 × 3,706 `X` and sorted `user_ids`/`movie_ids`; `X > 0` identifies the 1,000,209 observed user–movie interactions. A rating of 1–5 means a positive interaction (`1`); the rating magnitude is not a regression target. Map each user and rated movie to its zero-based position on the sorted axes. Initialize one NumPy `default_rng(42)` and iterate users in sorted-ID order: for each user, sort the observed movie positions, shuffle them with this generator and hold out `floor(0.2 × number of that user's interactions)` for testing; the rest are training positives. Each user retains training interactions. With one separate `default_rng(43)`, sample exactly one unrated movie for every training positive and one for every test positive, uniformly from that user's movies with `X == 0`, rejecting a sampled movie if that user rated it anywhere in `X`. Negatives may repeat; generate both fixed negative sets once per fresh run and reuse them for every epoch. Sampled zeros are *assumed* negative for this implicit-feedback task; all other unrated cells are excluded. Do not train on held-out positives or use test scores to choose settings.
    - Architecture and fit: PyTorch user and movie embeddings of size 32 each (`num_embeddings=6040` and `3706`); concatenate the two vectors, then apply `Linear(64, 64)` → ReLU → `Linear(64, 32)` → ReLU → `Linear(32, 16)` → ReLU → `Linear(16, 1)` to produce one logit per pair. Train with `BCEWithLogitsLoss(reduction="mean")` and Adam (`lr=0.001`, `weight_decay=0`) for exactly 5 epochs, `batch_size=4096`, shuffled training batches, `drop_last=False`, `num_workers=0`, and no early stopping. Test with the fixed held-out positives and negatives; print test binary cross-entropy and ROC AUC. The paper does not disclose its NCF architecture, so this is my own implicit-feedback NCF with an MLP interaction function.
    - Device and repeatability: train and infer on `cuda:0` on the RTX 3050; stop if CUDA is unavailable, and synchronize CUDA before the measured process exits. For TabNet and NCF, seed Python, NumPy and PyTorch with 42 immediately before model setup, use a seeded PyTorch data-loader generator for NCF shuffling, disable cuDNN benchmarking, and require deterministic PyTorch algorithms. Set `CUBLAS_WORKSPACE_CONFIG=:4096:2` before importing PyTorch. A deterministic-kernel failure stops the pilot; devices and algorithms are never switched silently. Print the actual device, split counts and hashes of the ordered positive and sampled-negative pair arrays in every full run so that all three backends can be checked against the same workload. The 64-user-row slices in the data stage do not set the NCF training batch size.

The [XGBoost Python API](https://xgboost.readthedocs.io/en/stable/python/python_api.html), [pytorch-tabnet parameters](https://github.com/dreamquark-ai/tabnet#model-parameters), [NCF paper](https://arxiv.org/abs/1708.05031) and [PyTorch reproducibility guidance](https://docs.pytorch.org/docs/stable/notes/randomness.html) document the APIs and the model family. Exact package builds for both Python environments are recorded in `requirements.lock` with Python-version markers; the two original lock snapshots remain with the session-2 raw results.

## 5. Comparisons

- Pandas is the baseline; Polars and Dask are compared with it.
- **Session 1:** 3 libraries × 2 datasets × 2 stages = 12 configurations.
- **Session 2:** 30 configurations (counting the three libraries), each with 1 warm-up and 10 measured runs, scheduled as in Section 7.
  - Current environment (Python 3.12), 24 configurations: `full` stage of C3–C6 (12); `data` stage of Insurance and ML-1M, re-measured so that baselines and the training estimate come from the same session (6); `full` stage of C1 and C2 as reference runs that check whether the laptop still reproduces session 1 (6).
  - Python 3.8 with the paper's versions, 6 configurations: Insurance, Random Forest, `data` and `full` stages, compared with the matching current-environment runs of the same session.
  - GPU power is sampled in every run and judged only for C6.

**Implementation checklist, updated Nov 16, 2026.** Session 2 is FROZEN at tag `session2-frozen-20261116`. Model settings, claims, hypotheses, measurement methods and criteria were recorded before any official comparative energy results. Pilot output is excluded from final analysis.

- [x] **Define C3 (Nov 15):** write the author's SVR hypothesis and the paper claim in Section 1; fix kernel, `C`, `epsilon`, `gamma` and target scaling in Section 4. If target scaling is used, fit its statistics on training targets only and inverse-transform predictions for evaluation. Keep the existing Insurance preprocessing and 80/20 split.
- [x] **Implement SVR (Nov 15):** add `--model` selection with dataset/model validation and keep existing commands working. Use one shared training function after the three backends produce their arrays. Fit the same model on the same training rows, report test R² and RMSE, and save smoke-test evidence for all three libraries. Completion means matching input checksums and split indices, finite predictions and metrics, and successful `data` and `full` runs; this is not an energy verdict.
- [x] **Implement XGBoost, then TabNet and NCF (Nov 15):** record each model's settings before its pilot; for NCF, define observed interactions, ID mapping, train/test split, loss and any negative sampling. Unrated cells are not automatically training targets of zero. Lock new dependencies and record actual CPU/GPU execution. Functional smoke evidence is in `results/smoke_test/session2/`.
- [x] **Validate measurement and analysis before official use:** `scripts/run_session2.sh`, `scripts/gpu_power.py` and `scripts/analyze_session2.py` identify configurations by session, software environment, library, dataset, model and stage; record both Python executable paths, copy each dependency lock and schedule data-stage baselines in the same session/environment. Static and synthetic checks, GPU validation and repeated CPU validation for kernel `7.0.0-42-generic` passed. Excluded TabNet and NCF pilots completed and were reviewed. No official session-2 benchmark has been run.
- [x] **Prepare version comparison (Nov 15):** use a separate Python 3.8 environment, record all resolved dependencies, and verify matching preprocessing outputs. Fix the Insurance model(s), parameters and run schedule in advance; differences cannot be attributed to a single library version when Python and other dependencies also change. Functional evidence is in `results/smoke_test/session2_legacy/`.
- [x] **Before official measurement:** finish Sections 1, 4–7 and 9, pass the functional checks and measurement validation, review the excluded pilots, then freeze the protocol/code at tag `session2-frozen-20261116`. The runner and analyzer write session-2 raw and analysis outputs to separate directories. The official measurement itself remains pending.

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

The session-1 measurement runner is `scripts/run_measurements.sh`; session 2 uses the separate `scripts/run_session2.sh`. They call `perf stat` and `/usr/bin/time -v` around each fresh pipeline process, record both RAPL domains, and check the pipeline output. They set `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1` and `PYTHONDONTWRITEBYTECODE=1` for every run. The command below is for the completed session-1 method only:

```bash
sudo ./scripts/run_measurements.sh
```

A session-1 pilot uses `sudo ./scripts/run_measurements.sh --pilot pandas insurance data`; its results are stored separately and never analyzed. The session-2 runner requires `--full --gpu-validation <passing-file>` for an official run, or `--pilot <environment> <library> <dataset> <model> <stage>` for an excluded pilot. Excluded session-2 pilots have run; the official session-2 measurement has not. `scripts/analyze_session2.py` audits only a complete session-2 raw directory.

## 7. Procedure

Before each session, review the pilot output and this protocol, then freeze and commit the protocol and runner before the first measured run. If a pilot reveals a problem, fix and document it before freezing.

1. **Before measuring:** AC power for the whole session; browser, IDE and other avoidable apps closed; Airplane mode on. The runner requires Wi-Fi disabled and no IPv4/IPv6 default route. CPU settings stay fixed: governor `powersave` on all 16 logical CPUs (`intel_pstate`, active mode), CPU0 EPP `balance_performance`, power profile `balanced`, Turbo Boost enabled (`no_turbo=0`). The runner checks these before every baseline and pipeline run and records system state before and after the session. Closing apps is manual and cannot be verified by the script.
2. **Idle baseline:** the runner measures `power/energy-pkg/` during `sleep 30` five times with a 40 s pause after each; idle power is the median of the five average powers. Each session has its own baseline.
3. **Measurement validation** (pass limits in `results/validation/criteria.txt`, written before the first measurement; both must pass before any pipeline is measured):
   - Test 1: the energy of `sleep 10` is within 15% of idle power × elapsed time.
   - Test 2: a single-threaded loop, `sum(i*i for i in range(N))` with N = 400,000,000 (about 15 s), run with N and 2N iterations; the 2N/N ratio of net energy must be between 1.8 and 2.2.
   - Scripts: `scripts/validate_measurement.sh` and `scripts/analyze_validation.sh`. Result on Oct 19, 2026: idle 4.776 W (4.755–4.814 W); Test 1 error 0.38%; Test 2 ratio 1.854; both pass (`results/validation/`). The tests are repeated if the kernel, BIOS or power settings change.
   - Repeated CPU validation on Nov 16, 2026, with kernel `7.0.0-42-generic` (`results/validation-20261116-001345/`): idle 5.612 W; Test 1 error 1.673%; Test 2 net-energy ratio 2.108; both pass. AC power, `balanced` profile and CPU settings were recorded before and after. This is measurement validation, not a session-2 benchmark.
   - Session 2 adds `scripts/validate_gpu.py`, run manually before measuring. It samples NVML power at 100 ms during two 5 s idle windows and two 10 s GPU matrix-multiply loads, with 40 s between loads and before the final idle window so the GPU can return to its idle power state. It passes only if the idle powers differ by at most 10% of their median, each load has at least 100 J net GPU energy over its ±2 s window, and the larger/smaller net-load-energy ratio is at most 1.30. A failure stops the session; validation output is kept separately from benchmark results.
   - GPU validation on Nov 15, 2026: the first attempt (`results/validation/gpu-20261115-caF93U/`) failed the idle check (90.3% gap), because its 3 s cooldown left the board near 9 W after the load versus 3.4 W before it. The cooldown was changed to 40 s without changing the pass limits. The second attempt (`results/validation/gpu-20261115-BYr5YB/`) passed: idle gap 1.68%, load net energies 589.45 J and 576.17 J, ratio 1.023. These are validation loads, not session-2 benchmark results.
   - Excluded session-2 pilots on Nov 16, 2026: `results/raw/pilot-20261116-004141-G12aZ5/` (TabNet) and `results/raw/pilot-20261116-005404-xMveRU/` (NCF) each completed one warm-up and one measured attempt with `status=OK`, identical model outputs across the two attempts, and CUDA execution. The first TabNet pilot had a single 30 s CPU idle baseline of 15.282 W, versus 5.612 W in the repeated CPU validation and 5.510 W in the NCF pilot. Its cause was not established. The offline repeat `results/raw/pilot-20261116-010439-89kBvK/` completed with AC power, balanced profile, no default route, all 16 governors set to `powersave`, and a 5.688 W CPU idle baseline. Its warm-up and measured runtimes were 4.272 s and 4.240 s, with identical model outputs and 18.659 J and 18.173 J net GPU energy. NCF warm-up and measured runtimes were 42.067 s and 41.689 s, with 224.246 J and 230.255 J net GPU energy. These pilots support keeping the predeclared model settings; neither their energy values nor their one measured attempt per configuration are used for a library outcome. The first two pilots were online, which pilot mode permits; the official runner requires networking disabled.
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

**Criteria for C3–C6 and the version comparison, written before session 2.** The C1 and C2 table above is unchanged. Overlapping intervals mean "no clear difference" (Section 8). A tie satisfies a "similar" condition, fails a "lowest", "highest" or "<" condition, and is never counted as a reversal; this closes the gap the C2 criteria left (Section 13). For C3–C6, runtime is reported but does not change an outcome.

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
| CPU | Intel Core i5-12500H (12 cores: 4 performance + 8 efficient, 16 threads) |
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

- Laptop instead of workstation; current library versions instead of the 2022 versions (the version comparison isolates part of this).
- Insurance has 1,338 rows, while the paper reports 1,000 records; I use all 1,338 rows and do not subsample to match.
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
