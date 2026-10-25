<!--
Skeleton only: headings and guiding questions. Delete each comment once the section is written.
Target length: 2–4 pages. Suggested writing order: 3 → 4 → 5 → 6 → 1 → 2 → 7, then read aloud.
Check every sentence with a number: does it state the condition (this laptop, these versions, full stage, n = 10)?
-->

# A laptop replication of DataFrame energy on Insurance and MovieLens-1M

Le Tuan Nguyen · Computer Science, University at Buffalo · 25 October 2026

[Repository](https://github.com/Nguyen-Le-Tuan/Comparing-3-python-DataFrame-lib)

## 1. What I replicated

I tested two CPU-energy results from [Kumar, Imran, and Kosar's GREENS '26 paper](https://arxiv.org/pdf/2511.08644) (arXiv:2511.08644). C1 is the Random Forest comparison on Insurance (Table 1, Section 4.1, Figure 5): Pandas and Polars use nearly equal energy, while Dask uses more and runs longest. C2 is the collaborative-filtering comparison on MovieLens-1M (Table 1, Section 4.3, Figure 3a): Polars < Pandas < Dask in CPU energy.

I ran the three DataFrame backends with a common downstream model for each dataset on my laptop. This is a small-scale **replication**, not an exact reproduction: I am a different researcher using different hardware, newer library versions, and model choices the paper does not specify. My full-stage Insurance result preserves Dask's disadvantage but separates Pandas from Polars, so C1 is partially reproduced. On ML-1M, Dask again uses the most energy, but Pandas and Polars have no clear energy difference; that pattern falls outside my pre-registered C2 outcome categories. I compare directions and relative gaps, not absolute joules.

## 2. Setup and differences from the paper

I used an Intel i5-12500H laptop (4 performance cores, 8 efficiency cores, 16 threads) with 16 GB RAM and Ubuntu 26.04.1. The environment used Python 3.12.14, Pandas 3.0.6, Polars 2.0.0, and Dask 2026.8.0. The paper used a 16-core/32-thread workstation with 128 GB RAM and 2022-era library versions. My Insurance file has 1,338 rows rather than the paper's reported 1,000. The ML-1M input has 1,000,209 ratings. The paper says it generated Parquet copies for Polars where applicable, while my backends read the original text inputs. Each backend produced matching pipeline checksums before measurement. Insurance used the same 100-tree Random Forest and 80/20 split across backends; ML-1M used the same 50-component TruncatedSVD. Those downstream choices are specified in [the protocol](../PROTOCOL.md), not in the paper.

The [full session](../results/raw/full-20261025-135703-JICxLk/) covered 12 configurations: three libraries, two datasets, and `data`/`full` stages. It retained 12 warm-ups and 120 measured runs (ten per configuration), each in a fresh process, with randomized order and 40-second pauses. The runner recorded AC power, a balanced profile, and disabled Wi-Fi; my session note records that I closed the other apps. This differs from the paper's five measured runs. I measured package energy with `perf stat` and used its elapsed time as runtime. For each run, net energy = measured package joules − 5.139437 W × runtime in seconds. The 5.139437 W value is the median idle power from this session's five 30-second baselines. The earlier 4.776 W validation baseline was not reused. The paper summed core and DRAM energy, which my laptop cannot measure in the same way.

The analysis computes medians, IQRs, and 10% trimmed means across each set of ten runs. The 95% intervals around medians use 10,000 bootstrap resamples with seed 42. Two libraries count as different only when those intervals do not overlap. Measurement validation passed (0.38% sleep-test error; 1.854 energy ratio for a doubled CPU loop), and the largest observed energy CV was 1.50%, below the 10% stop threshold. The method and outcome rules were committed before the full run in `4badf06`, but I did not change the protocol's status from `ACTIVE` to `FROZEN` until the post-run commit `5881ae5`. That status step was late; the committed rules in Sections 8 and 9 did not change between those commits.

## 3. Results

I use the `full` stage for the comparison with the paper's end-to-end results. Table 1 gives the local medians from ten measured runs per configuration; the figure shows the energy intervals on separate scales for the two datasets. All energy values below are net CPU *package* energy, not the paper's sum of core and DRAM energy.

| Dataset | Library | Net energy, median [95% CI] (J) | Runtime, median [95% CI] (s) | Data/full energy share |
| --- | --- | ---: | ---: | ---: |
| Insurance | Pandas | 16.736 [16.615, 16.910] | 0.897 [0.896, 0.899] | 24.5% |
| Insurance | Polars | 18.309 [18.132, 18.377] | 0.982 [0.977, 0.986] | 14.3% |
| Insurance | Dask | 26.061 [25.996, 26.118] | 1.405 [1.403, 1.414] | 59.1% |
| ML-1M | Pandas | 76.238 [75.702, 76.723] | 3.744 [3.733, 3.752] | 64.5% |
| ML-1M | Polars | 76.632 [76.419, 77.423] | 2.381 [2.376, 2.405] | 60.5% |
| ML-1M | Dask | 197.827 [196.951, 198.682] | 10.031 [10.006, 10.049] | 87.9% |

*Table 1. Local full-stage results. The share divides the data-stage median by the full-stage median; the runs are separate, so it is not a directly metered phase breakdown. Source: [`summary.csv`](../results/analysis/summary.csv).*

![Full-stage net CPU package energy and bootstrap intervals](../results/analysis/full_stage_energy.svg)

*Figure 1. Full-stage median net package energy with 95% bootstrap intervals. Each dataset has its own joule scale.*

### 3.1 C1: Insurance + Random Forest

For Random Forest on Insurance, the paper's Table 1 reports almost equal CPU energy for Pandas and Polars (146.760 and 146.776 J), with Dask about 14% higher (167.436 J). My laptop gives Pandas < Polars < Dask. Polars uses 9.4% more net package energy than Pandas, and their 95% intervals do not overlap. Dask uses 55.7% more than Pandas and is clearly above both libraries. It also has the longest runtime, with non-overlapping runtime intervals. Under the two-part rule in Protocol Section 9, C1 is **partially reproduced**: the Dask result holds, but the expected lack of a clear Pandas–Polars difference does not.

### 3.2 C2: MovieLens-1M + TruncatedSVD

For collaborative filtering on ML-1M, the paper reports Polars < Pandas < Dask in CPU energy (1,437.00, 3,328.32, and 3,748.08 J). My full-stage point medians are Pandas 76.238 J, Polars 76.632 J, and Dask 197.827 J. Pandas and Polars differ by only 0.52%, and their energy intervals overlap. Under the pre-registered decision rule, there is **no clear energy difference** between them; Dask is clearly higher than both.

I use reading **D** of the C2 outcome rule: **not covered by the pre-registered criteria**. The result is not “Reproduced,” because Polars is not clearly below Pandas. “Partially reproduced” requires Polars to be lowest *and* Pandas–Dask to be unclear or reversed, but Pandas is clearly below Dask. Calling it “Not reproduced” from the 0.52% point-median reversal would ignore the overlapping intervals. I retain the original rule and record this gap in Protocol Section 13 and Section 5 below.

Polars is clearly faster than Pandas here: 2.381 s versus 3.744 s, with non-overlapping runtime intervals. That speed advantage does not establish an energy advantage. The C2 outcome rule concerns energy, not runtime.

### 3.3 Not tested

I did not run the paper's SVR, XGBoost, or TabNet models on Insurance; NCF on ML-1M; or ResNet and Mask R-CNN on COCO. This study was limited to one classical model on Insurance and one matrix-factorization model on ML-1M so the full set of measurements would fit a laptop and the project schedule. I also did not measure GPU or DRAM energy, because these two chosen pipelines run on the CPU and this laptop does not expose a DRAM RAPL counter. None of those omitted cases receives a replication verdict.

### 3.4 My pre-registered hypothesis

Before measuring, I predicted that Pandas would perform best on small Insurance data and Polars would perform best on ML-1M (Protocol Section 1). Pandas has the lowest full-stage median energy and runtime on Insurance. On ML-1M, Polars has the shortest runtime, but it does not have a clear energy advantage over Pandas. My phrase “perform the best” did not define whether I meant energy, runtime, or both; these results should be read by metric rather than as a single win or loss for the hypothesis.

## 4. Mismatches with the paper

The direction of Dask's Insurance result matches the paper, but its local energy gap from Pandas is 55.7%, not about 14%. Pandas and Polars are nearly tied in the paper's Random Forest row, while Pandas uses 9.4% less energy here. On ML-1M, the paper's large Polars advantage over Pandas is absent in my energy measurements, even though Polars remains faster.

The data-stage share is higher for Dask than for the other two libraries on both datasets: 59.1% on Insurance and 87.9% on ML-1M. This points to data processing as a place to investigate Dask's extra full-stage energy. It does not prove that scheduling is the cause. The `data` and `full` stages were measured in separate processes, and their median ratio is not a within-run phase measurement.

Several differences may contribute. Current library versions could behave differently from the paper's 2022 versions; a same-laptop comparison with the older stack would test that. The 1,338-row Insurance file may change fixed overhead relative to the paper's reported 1,000 rows; repeating the data stage at controlled row counts would test whether Dask's relative cost shrinks with size. CPU scheduling across performance and efficiency cores could matter; CPU-affinity runs would test it. Finally, a machine exposing both core and DRAM energy could test how much the different energy domains change the ranking. I have not run these follow-up experiments.

## 5. Limitations

This is a comparison of three pipelines on one laptop, not a measurement of each library in isolation. RAPL package energy includes activity outside the Python process. Subtracting an idle baseline and closing other apps reduce that influence but cannot remove it completely. The laptop has no DRAM energy counter, so its net package-energy values cannot be compared directly with the paper's core-plus-DRAM joules. Different library versions, the larger Insurance file, and my chosen Random Forest and TruncatedSVD implementations also limit the comparison with the original workloads. CPU temperature was recorded, but clock throttling was not measured directly.

Ten runs per configuration give a local estimate, not a general performance guarantee. The protocol fixed median/IQR reporting, the 10,000-resample bootstrap decision rule, and the 10% CV stop threshold before the full run. The exact percentile interval, quartile interpolation, trimmed-mean convention, and sample-SD convention for CV were specified after the run and logged in Protocol Section 13. Overlapping intervals mean “no clear difference” under my rule, not proof that two libraries consume identical energy.

The C2 outcome categories have a gap when Pandas and Polars are indistinguishable by that rule while Dask is clearly higher. I therefore report “not covered by the pre-registered criteria,” rather than changing Section 9 after seeing the data. These measurements do not establish what would happen for the paper's other models, COCO, another machine, or the older software stack.

## 6. Next experiment

I would test whether Dask's high data-stage energy on small inputs is mostly fixed startup and scheduling cost. I would run the same Insurance `data` pipeline at controlled row counts (1,338, 13,380, and 133,800) by repeating the original rows, keeping the columns and preprocessing fixed. A new measurement session would use its own idle baseline, randomized order across configurations, fresh processes, one warm-up, and ten measured runs per configuration. If Dask's energy ratio to Pandas shrinks as the data grows, that would support a fixed-cost explanation. If the ratio stays high or grows, it would weaken that explanation. I have not run this experiment; it is a concrete question to raise with the paper's authors.

## 7. Reproducibility and use of AI

<!--
- How can a reader re-run this (README, data download + SHA-256, commands)?
- Which commit and raw session directory are the results from?
- What did AI assist with, and what was mine (PROTOCOL.md Section 12)? Who wrote this report's text?
-->
