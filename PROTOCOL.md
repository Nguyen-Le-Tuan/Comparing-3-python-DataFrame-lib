# Replication Protocol: Energy Use of Pandas, Polars and Dask on a Laptop

| Field | Value |
| --- | --- |
| Author | Le Tuan Nguyen (University at Buffalo, CS) |
| Status | ACTIVE <!-- đổi thành: FROZEN on YYYY-MM-DD, trước khi chạy đầy đủ --> |
| Last updated | Oct 19, 2026 |
| Study type | Small-scale **replication**:personal laptop, updated library |
| Repository | https://github.com/Nguyen-Le-Tuan/Comparing-3-python-DataFrame-lib |

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
- **Where in the paper:** Table 1; Section 4.1 and Figure 5 (Insurance); Section 4.3 and Figure 3a (ML-1M)
- **My hypothesis before running:** Because the Insurance dataset is in tabular format and only has 1k rows while the MovieLens is 1M samples, I assume that Pandas will perform the best in the Insurance Dataset while the Polars will be the best in the ML-1M. I have these assumptions because I already knew that Pandas is still advantageous on small data while Polars (which written in Rust) will outperform Pandas on larger data (from several GB to hundred GB).  <!-- Bạn đoán kết quả trên laptop sẽ thế nào, và vì sao. Viết trước khi chạy, không sửa sau. -->

## 2. Scope

In this replication, I check two results from Table 1 of the paper on two datasets, Insurance and MovieLens-1M. For each library, I measure the energy consumption and the time it takes for both the **data stage alone** and **the full run (data stage + model training)**.

- **Required (C1):** Insurance with Random Forest.
- **Secondary (C2):** MovieLens-1M with Collaborative Filtering (CF), measured together with C1 (planned for Oct 22–24).
- **Deciding later:** Support Vector Regression (SVR) and XGBoost on Insurance; a small Neural Collaborative Filtering (NCF) model on the GPU.
- **Not tested:** TabNet; ResNet and Mask R-CNN on COCO, because training them needs far more GPU memory and time than my laptop (4 GB VRAM, about 14 GB of usable RAM) and my schedule allow; DRAM energy, because my CPU does not expose a DRAM energy counter.

## 3. Data

| Dataset | Source | License | Rows × columns | SHA-256 of downloaded file |
| --- | --- | --- | --- | --- |
| Insurance | Medical Cost Personal Datasets ([Kaggle](https://www.kaggle.com/datasets/mirichoi0218/insurance)) | [Database: Open Database, Contents: Database Contents](https://opendatacommons.org/licenses/dbcl/1-0/) | 1,338 rows x 7 columns <!-- paper ghi 1.000 dòng; đếm lại, lệch thì ghi vào mục 11 --> | 388eff679557d08ac19f463d025de5e0b4adc482537c8456d19934d78621fd47|
| MovieLens-1M | [GroupLens](https://grouplens.org/datasets/movielens/1m/) (paper cited) | Custom Non-Commercial / Academic Use | `users.dat`: 6,040 rows × 5 columns; `movies.dat`: 3,883 rows × 3 columns; `ratings.dat`: 1,000,209 rows × 4 columns  | a6898adb50b9ca05aa231689da44c217cb524e7ebd39d264c56e2832f2c54e20 |


## 4. Pipeline definition

Based on *Algorithm 1: Unified Data Processing Pipeline* (Section 3.1 of the paper). All three libraries must do exactly these steps.

**Insurance (C1)**

1. Load `insurance.csv` into a dataframe (expect 1,338 rows × 7 columns: `age`, `sex`, `bmi`, `children`, `smoker`, `region`, `charges`).
2. Take the raw dataframe and impute missing values (numeric columns: the column mean; text columns: the most frequent value), producing a complete dataframe. Insurance has no missing cells, so this step changes nothing, but it still runs so that every library does the same work as in the paper. I use the mean instead of the median because Dask only computes an approximate median.
3. Take the complete dataframe and encode the categorical columns (`sex`: male = 1, female = 0; `smoker`: yes = 1, no = 0; `region`: one-hot, one column per region in alphabetical order), producing a numeric dataframe.
4. Take the numeric dataframe and standardize `age`, `bmi` and `children` (subtract the mean, divide by the sample standard deviation with ddof = 1), producing a scaled dataframe. The target `charges` is not scaled.
5. Take the scaled dataframe and convert it to NumPy arrays: `X` with 9 feature columns in a fixed order (`age`, `bmi`, `children`, `sex`, `smoker`, `region_northeast`, `region_northwest`, `region_southeast`, `region_southwest`) and `y` = `charges`. Then slice `X` and `y` into mini-batches of 64 rows in file order (21 batches; the last one has 58 rows).

**MovieLens-1M (C2)**, to be written in full before the first C2 run (Step 5):

1. Load `ratings.dat` (1,000,209 × 4), `users.dat` (6,040 × 5) and `movies.dat` (3,883 × 3), using the `::` separator → three dataframes.
2. Join ratings to users on `UserID` and to movies on `MovieID`, validating many-to-one joins and preserving all 1,000,209 ratings → one joined dataframe.
3. Check that each `(UserID, MovieID)` pair is unique; pivot `Rating` to rows = sorted `UserID`, columns = sorted rated `MovieID`, and fill unrated cells with 0 → a 6,040 × 3,706 `float64` matrix `X`.
4. Slice `X` into sorted-UserID-order batches of 64 user rows without shuffling and sum every batch → the data-stage checksum (`X` shape, sum, nonzero count, and ordered-ID hashes).
5. For `--stage full`, fit `TruncatedSVD(n_components=50, random_state=42)` to the whole `X` matrix → a 6,040 × 50 user-factor matrix. For `--stage data`, stop after the checksum; there is no target `y` or train/test split in this C2 pipeline.

**Rules for both datasets**

- **Output checksum:** at the end, the program prints the shapes of the output arrays and the sum of all their elements. The sum is computed over the mini-batches, so every batch is actually used. All three libraries must give the same shapes, the same feature-column order and sums that differ by less than 1e-6 before any energy comparison.
- **Library-specific choices** (fixed for all runs):
  - Pandas: eager, `pd.read_csv` with default settings.
  - Polars: lazy, `pl.scan_csv` and expressions, with a single `.collect()` before the NumPy conversion, because the paper credits Polars' lazy expressions for its efficiency.
  - Dask: `dd.read_csv` with the default block size and the default threaded scheduler; the number of partitions is printed at runtime. Categorical columns are made "known" with `.categorize()` before one-hot encoding, because Dask needs every category in advance.
- **Randomness:** mini-batches are taken in file order without shuffling, so the data stage has no randomness. The only random parts are the train/test split and the model, both with seed 42.
- **Two stages per configuration:** `--stage data` runs only the dataframe part; `--stage full` runs the dataframe part and then trains the downstream model. Training energy is estimated as *full* − *data*.
- **Downstream models** (the paper does not report its hyperparameters, so these are my choices):
  - Insurance: scikit-learn `RandomForestRegressor` with default hyperparameters (100 trees, one CPU core) and `random_state=42`, trained on 80% of the rows (`train_test_split` with `test_size=0.2`, `random_state=42`: 1,070 training rows, 268 test rows). Random Forest trains on the whole training array; the mini-batch step is kept only to follow the paper. The test R² is printed as a sanity check.
  - MovieLens-1M: CF as a factorization of the user × movie matrix with `TruncatedSVD(n_components=50, random_state=42)`.
  - NCF (optional, GPU): defined later, only if Step 7 is done.

## 5. Comparisons

- **Baseline:** Pandas.
- **Compared:** Polars, Dask.
- **Configurations:** 3 libraries × 2 datasets × 2 stages = 12 configurations.

## 6. Metrics and how they are measured

| Metric | Unit | Tool and formula |
| --- | --- | --- |
| Runtime | s | Wall-clock time reported by `perf stat` |
| CPU package energy | J | `power/energy-pkg/` via `sudo perf stat` |
| CPU core energy | J | `power/energy-cores/` via `sudo perf stat` |
| Net energy | J | measured energy − idle power × runtime |
| Training energy (derived) | J | net energy of `--stage full` and net energy of `--stage data` |
| Peak memory | MB | maximum resident set size from `/usr/bin/time -v` |
| GPU energy | J | pynvml power samples every 1 s, integrated over time |
| Disk usage | TODO | TODO <!-- paper có đo disk I/O; đo hoặc ghi not tested --> |

Measurement command (one run):

```
sudo perf stat -e power/energy-pkg/,power/energy-cores/ -x, -o results/raw/<config>_<run>.csv -- .venv/bin/python pipeline.py --lib <lib> --data <dataset> --stage <data|full>
```

## 7. Procedure

1. **Before measuring:** AC power connected for the whole session; browser and IDE closed; network: TODO. CPU settings stay at the laptop defaults and are the same for every run: governor `powersave` on all 16 CPUs (`intel_pstate`, active mode), EPP `balance_performance`, power profile `balanced`, Turbo Boost on. They are recorded before and after each session.
2. **Idle baseline:** `sudo perf stat -e power/energy-pkg/ -- sleep 30`, 5 runs with a 40 s pause after each; idle power = median of the five average powers.
3. **Measurement validation tests** (pass limits written in `results/validation/criteria.txt` before the first measurement; both must pass before any pipeline is measured):
   - Test 1: the energy of `sleep 10` is within 15% of idle power × elapsed time.
   - Test 2: a single-threaded Python loop, `sum(i*i for i in range(N))` with N = 400,000,000 (about 15 s), is run with N and 2N iterations; the 2N/N ratio of net energy must be between 1.8 and 2.2.
   - Scripts: `scripts/validate_measurement.sh` (measures) and `scripts/analyze_validation.sh` (computes).
   - Result on Oct 19, 2026: idle power 4.776 W (five runs, 4.755 to 4.814 W); Test 1 error 0.38% (pass); Test 2 ratio 1.854 (pass). Files and notes: `results/validation/`.
   - The tests are repeated if the kernel, BIOS or power settings change.
4. **Data-pipeline smoke test** (before the first energy run of the pipelines):
   - Run the same Insurance input through Pandas, Polars, and Dask.
   - Check the expected input shape, column names, and missing-value counts.
   - After the defined preprocessing, check that all libraries produce the same output shape, feature-column order, and checksum.
   - Save the test output under `results/smoke_test/`.
5. **Runs per configuration:** 1 warm-up (discarded) + 10 measured runs; a fresh process per run; 40 s idle between runs; the CPU package temperature is recorded before each run; configuration order randomized with seed TODO.
6. **Raw data:** every run, including failed ones, is saved under `results/raw/`. No run is discarded after the fact.

## 8. Analysis plan

For each configuration (library × dataset × stage), I report the median and the interquartile range (IQR) of net energy and runtime over the 10 measured runs. I use the median because one run may be unusually slow when a background process wakes up. I also report the trimmed mean, because the paper uses it.

- **Decision rule:** two libraries "differ" only if the 95% bootstrap confidence intervals of their median net energy do not overlap (10,000 resamples, seed 42); otherwise I report "no clear difference". The same rule is used for runtime.
- **Comparison with the paper:** my laptop and library versions differ from the paper's, so I compare the **direction** of the results (which library uses more energy, and by roughly what percentage), not the absolute joules. Table 1 reports end-to-end numbers, so this comparison uses `--stage full`.
- **Ranking on my laptop:** I also rank Pandas, Polars and Dask by median net energy and report my ranking next to the paper's.
- **Decomposition:** the share of the data stage in the end-to-end energy, *data* / *full*.

## 9. Outcome criteria

Written before any measurement. Each claim is judged on `--stage full` with the decision rule in Section 8.

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

My hypothesis in Section 1 is checked separately in the report; it does not change these outcomes.

## 10. Environment

| Item | Value |
| --- | --- |
| CPU | Intel Core i5-12500H (12 cores: 4 performance + 8 efficient, 16 threads) |
| RAM | 16 GB |
| GPU | NVIDIA GeForce RTX 3050 Laptop, 4 GB (driver TODO) |
| OS / kernel | Ubuntu 26.04.1 LTS, kernel 7.0.0-38-generic |
| perf | 7.0.14 |
| Python | 3.12.14 (via uv) |
| Library versions | Locked in `requirements.lock`; summary: Pandas 3.0.6, Polars 2.0.0, Dask 2026.8.0, pyarrow 26.0.0, numpy 2.5.4, scikit-learn 1.9.1. |
| RAPL domains available | package, core, uncore, psys; **no DRAM** |

## 11. Known differences from the paper and threats to validity

- Laptop instead of workstation.
- Current library versions instead of the 2022 versions.
- My *Insurance* dataset has 1338 rows but on Section *Experimental Setup* reports 1000 records.



- RAPL measures the whole CPU package, not only our process; other processes add noise (mitigated by the idle baseline and closing apps).
- No DRAM energy domain, so CPU energy is not the paper's energy-cores + energy-ram sum.
- Possible thermal throttling on a laptop: TODO (how you check or limit it).
- Inconsistencies in the paper: it states both "five runs, trimmed mean and 95% CI" and "mean of four measured runs"; the Insurance row count differs from the cited dataset (TODO: confirm).
- The paper does not report hyperparameters, the train/test split or the CF algorithm; the choices in Section 4 are ours.

## 12. Use of AI assistance

Pipeline code is written with AI assistance, one step at a time, then reviewed, run and annotated by the author. Sections 2, 4, 7, 8 and 9 of this protocol and the scripts in scripts/ were drafted with AI assistance from the author’s decisions and terminal commands, then reviewed by the author. The claims, hypothesis, data choices and all measurements are the author’s own.

## 13. Deviations log

<!-- Sau khi FROZEN, mọi thay đổi ghi ở đây: ngày, thay đổi gì, vì sao. Không sửa ngầm các mục trên. -->

| Date | Change | Reason |
| --- | --- | --- |
| | | |
