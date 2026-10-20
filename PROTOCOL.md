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

<!-- Hai claim, viết lại bằng lời của mình. C1 bắt buộc (trước email 29/10). C2 là phần thêm: chưa xong trước 21/10 thì ghi "not tested".
Gợi ý C1: Insurance + Random Forest: Pandas ≈ Polars về CPU energy (146,8 J so với 146,8 J), Dask cao hơn khoảng 14% (167,4 J) và chạy lâu nhất. Với SVR và XGBoost, Dask cao hơn khoảng 20–22%; ngoại lệ là TabNet.
Gợi ý C2: ML-1M + CF: Polars < Pandas < Dask (1.437 / 3.328 / 3.748 J). -->

- **Claim C1:** Testing the energy consumption of Pandas, Polars and Dask on the Insurance Dataset. The paper reported that by using *Random Forest*, Pandas and Polars use similar CPU energy (146.8 J) while Dask uses more 14% (167.4 J); however, on SVR and XGBoost, Dask is even higher (20-22%).
- **Claim C2:** Testing on the MovieLens 1M will result in energy uses: Polars < Pandas < Dask.
- **Where in the paper:** Table 1; Section 4.1 and Figure 5 (Insurance); Section 4.3 and Figure 3a (ML-1M)
- **My hypothesis before running:** Because the Insurance dataset is in tabular format and only has 1k rows while the MovieLens is 1M samples, I assume that Pandas will perform the best in the Insurance Dataset while the Polars will be the best in the ML-1M. I have these assumptions because I already knew that Pandas is still advantageous on small data while Polars (which written in Rust) will outperform Pandas on larger data (from several GB to hundred GB).  <!-- Bạn đoán kết quả trên laptop sẽ thế nào, và vì sao. Viết trước khi chạy, không sửa sau. -->

## 2. Scope
In this reproduction repository, I check two results from Table 1: The energy consumption of each Python DataFrame library when using model: Random Forest, Support Vector Regression (SVR), TabNet, XGBoost, Collaborative Filtering (CF) and Neural Collabroative Filtering (NCF) on two datasets Insurance and MovieLens-1M. I measure the energy consumption and the time it taken for both the **data stage alone** and **the full run (including the training stage)**.
I don't test ResNet, Mask R-CNN and the dataset COCO because these it will absolutely exceed my laptop GPU 4GB VRAM and 16GB RAM.   


## 3. Data

| Dataset | Source | License | Rows × columns | SHA-256 of downloaded file |
| --- | --- | --- | --- | --- |
| Insurance | Medical Cost Personal Datasets ([Kaggle](https://www.kaggle.com/datasets/mirichoi0218/insurance)) | [Database: Open Database, Contents: Database Contents](https://opendatacommons.org/licenses/dbcl/1-0/) | 1339 rows x 7 columns <!-- paper ghi 1.000 dòng; đếm lại, lệch thì ghi vào mục 11 --> | 388eff679557d08ac19f463d025de5e0b4adc482537c8456d19934d78621fd47|
| MovieLens-1M | [GroupLens](https://grouplens.org/datasets/movielens/1m/) (paper cited) | Custom Non-Commercial / Academic Use | `users.dat`: 6,040 rows × 5 columns; `movies.dat`: 3,883 rows × 3 columns; `ratings.dat`: 1,000,209 rows × 4 columns (1,010,132 **total records**) | a6898adb50b9ca05aa231689da44c217cb524e7ebd39d264c56e2832f2c54e20 |


## 4. Pipeline definition

<!-- Viết pseudocode bằng lời của mình: mỗi bước một dòng, vào gì / ra gì. Ba thư viện phải làm đúng các bước này. -->
Based on the section: "*Algorithm 1: Unified Data Processing Pipeline*", section 3.1.
1. Load insurance.csv into a dataframe (expect from the dataset description: 1,338 rows × 7 columns).
2. Take the raw dataframe, impute missing values, and then producing a complete dataframe
3. Take the complete dataframe, encode categorical column, produce a numeric-feature dataframe.
4. Take the numeric-feature dataframe, normalize the numerical features, and then producing a scaled dataframe.
5. Take the scaled dataframe, convert to NumPy arrays / dataset object => slices the processed data into mini-batches suitable for training.

- **The numerical NumPy shape output:**: All three libraries must produce the same checksum before any comparison.
- **Library-specific choices:** Polars TODO (eager `read_csv` or lazy `scan_csv` + `.collect()`); Dask TODO (number of partitions, scheduler). <!-- chọn một lần, ghi lý do, giữ cố định -->
- **Randomness:** TODO (batch shuffling on/off; seed if on).
- **Two stages per configuration:** `--stage data` runs only the dataframe part; `--stage full` runs the dataframe part and then trains the downstream model. Training energy is estimated as *full* - *data*.

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

1. **Before measuring:** AC power connected; browser and IDE closed; CPU governor fixed to TODO and recorded; network TODO.
2. **Idle baseline:** `sudo perf stat -e power/energy-pkg/ -- sleep 30`, repeated 5 times → idle power (W).
3. **Validation tests (must pass before any real measurement):**
   - `sleep 10` energy ≈ idle power × 10 s (tolerance: TODO %).
   - A CPU loop with twice the iterations uses ≈ twice the net energy (tolerance: TODO %).
4. **Runs per configuration:** 1 warm-up (discarded) + 10 measured runs; a fresh process per run; 40 s idle between runs; configuration order randomized with seed TODO.
5. **Raw data:** every run, including failed ones, is saved under `results/raw/`. No run is discarded after the fact.

## 8. Analysis system
For each library, dataset and model, I will report the median energy and runtime across the measured runs. I use the median because one run may be unusually slow due to different background activities.
As my personal laptop is different from the computational system set up in the paper, I will try to re-rank Pandas, Polars and Dask base on their efficiency after the experiement rather than trying to replicate the similar result reported in the paper.

## 9. Outcome criteria

| Outcome | Condition |
| --- | --- |
| Reproduced | The best choice for small and tabular dataset is Pandas, while best use for the larger dataset is Polars while Dask will show the biggest different when in comparison to two libraries above when experimenting on *Insurance* and *MovieLens-1M* datasets. |
| Partially reproduced | Cannot show that Dask is not totally suitable for small to medium datasets.|
| Not reproduced | The ranking is totally different from the paper or the results cannot be easily forseen before doing the experiment.|

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
- TODO: anything else you notice.

## 12. Use of AI assistance

Pipeline code was written with AI assistance, one step at a time, then reviewed, run and annotated by the author; the Pandas version was retyped by the author from pseudocode. The protocol, measurement procedure, validation tests and analysis are the author's own. TODO: adjust to what actually happened.

## 13. Deviations log

<!-- Sau khi FROZEN, mọi thay đổi ghi ở đây: ngày, thay đổi gì, vì sao. Không sửa ngầm các mục trên. -->

| Date | Change | Reason |
| --- | --- | --- |
| | | |
