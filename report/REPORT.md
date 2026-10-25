# A laptop replication of DataFrame energy on Insurance and MovieLens-1M

Le Tuan Nguyen · Computer Science, University at Buffalo · 25 October 2026

[Repository](https://github.com/Nguyen-Le-Tuan/Comparing-3-python-DataFrame-lib)

## 1. What I replicated

I tested two CPU-energy results from [Kumar, Imran, and Kosar's GREENS '26 paper](https://arxiv.org/pdf/2511.08644) (arXiv:2511.08644). C1 is the Random Forest comparison on Insurance (Table 1, Section 4.1, Figure 5): Pandas and Polars use nearly equal energy, while Dask uses more and runs longest. C2 is the collaborative-filtering comparison on MovieLens-1M (Table 1, Section 4.3, Figure 3a): Polars < Pandas < Dask in CPU energy.

I ran the three DataFrame backends with a common downstream model for each dataset on my laptop. This is a small-scale **replication**, not an exact reproduction: I am a different researcher using different hardware, newer library versions, and model choices the paper does not specify. My full-stage Insurance result preserves Dask's disadvantage but separates Pandas from Polars, so C1 is partially reproduced. On ML-1M, Dask again uses the most energy, but Pandas and Polars have no clear energy difference; that pattern falls outside my pre-registered C2 outcome categories. I compare directions and relative gaps, not absolute joules.

## 2. Setup and differences from the paper

I used an Intel i5-12500H laptop (4 performance cores, 8 efficiency cores, 16 threads), 16 GB RAM, Ubuntu 26.04.1, Python 3.12.14, Pandas 3.0.6, Polars 2.0.0, and Dask 2026.8.0. The paper used a 16-core/32-thread workstation, 128 GB RAM, and 2022-era libraries. My Insurance file has 1,338 rows rather than the paper's reported 1,000; ML-1M has 1,000,209 ratings. The paper generated Parquet copies for Polars where applicable, while my backends read the original text inputs. All three backends produced matching checksums. Insurance used one 100-tree Random Forest with an 80/20 split; ML-1M used a 50-component TruncatedSVD. These downstream choices appear in [the protocol](../PROTOCOL.md), not in the paper.

The [full session](../results/raw/full-20261025-135703-JICxLk/) covered 12 configurations: three libraries, two datasets, and `data`/`full` stages. It kept 12 warm-ups and 120 measured runs (ten per configuration), with fresh processes, randomized order, and 40-second pauses. The runner recorded AC power, a balanced profile, and disabled Wi-Fi; I closed the other apps. For each run, `perf stat` supplied package energy and elapsed time. Net energy = measured package joules − 5.139437 W × runtime in seconds. That idle power came from this session's five 30-second baselines; I did not reuse the earlier 4.776 W validation baseline. The paper used five measured runs and summed core and DRAM energy.

The analysis computes median, IQR, and 10% trimmed mean per configuration. Median intervals use 10,000 bootstrap resamples (seed 42); non-overlap is the decision rule. Validation passed (0.38% sleep-test error; 1.854 doubled-loop energy ratio), and the largest energy CV was 1.50%, below the 10% stop threshold. The method and outcome rules were committed before the run in `4badf06`, but I changed the protocol status from `ACTIVE` to `FROZEN` only afterward, in `5881ae5`. That status step was late; Sections 8 and 9 did not change between those commits.

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

For collaborative filtering on ML-1M, the paper reports Polars < Pandas < Dask in CPU energy (1,437.00, 3,328.32, and 3,748.08 J). My full-stage medians are Pandas 76.238 J, Polars 76.632 J, and Dask 197.827 J. The Pandas–Polars gap is 0.52% and their energy intervals overlap: **no clear difference** under my rule. Dask is clearly higher than both.

I choose reading **D**: **not covered by the pre-registered criteria**. “Reproduced” requires Polars clearly below Pandas. “Partially reproduced” requires Polars lowest and Pandas–Dask unclear or reversed, but Pandas is clearly below Dask. “Not reproduced” based only on the 0.52% point-median reversal would disregard the overlapping intervals. I leave the rule intact and log the gap in Protocol Section 13. Polars is faster than Pandas (2.381 versus 3.744 s, non-overlapping runtime intervals), but C2's outcome rule concerns energy.

### 3.3 Not tested

I did not run SVR, XGBoost, or TabNet on Insurance; NCF on ML-1M; or ResNet and Mask R-CNN on COCO. The scope was one model per dataset within a laptop and time budget. I did not measure GPU or DRAM energy: the chosen pipelines run on the CPU, and this laptop has no DRAM RAPL counter. I assign no verdict to omitted cases.

### 3.4 My pre-registered hypothesis

Before measuring, I predicted that Pandas would perform best on small Insurance data and Polars would perform best on ML-1M (Protocol Section 1). Pandas has the lowest full-stage median energy and runtime on Insurance. On ML-1M, Polars has the shortest runtime, but it does not have a clear energy advantage over Pandas. My phrase “perform the best” did not define whether I meant energy, runtime, or both; these results should be read by metric rather than as a single win or loss for the hypothesis.

## 4. Mismatches with the paper

On Insurance, Dask's local energy gap from Pandas is 55.7%, versus about 14% in the paper. Pandas uses 9.4% less than Polars locally, rather than nearly the same amount. The paper's large Polars energy advantage on ML-1M is also absent, although Polars remains faster.

Dask's data-stage share is 59.1% on Insurance and 87.9% on ML-1M, higher than either other library. This makes data processing a useful place to investigate, but it does not prove scheduling caused the gap: `data` and `full` are separate runs, not a within-run phase measurement.

Possible causes and tests are specific. An older-stack run on this laptop would probe version effects; controlled row counts would probe fixed Dask overhead and the Insurance size mismatch. Running Polars with both text and Parquet inputs would probe the paper's different input format. CPU-affinity runs would probe hybrid-core scheduling. A machine with both core and DRAM counters would probe the energy-domain difference. I have run none of these follow-ups.

## 5. Limitations

RAPL package energy includes activity outside Python. The idle subtraction and closed apps reduce but cannot eliminate that influence. Without a DRAM counter, my joules cannot be compared directly with the paper's core-plus-DRAM values. Software versions, input format and size, and my selected downstream models also differ. I recorded CPU temperature but did not directly measure throttling.

Ten runs per configuration give a local estimate. The protocol committed median/IQR reporting, a 10,000-resample bootstrap decision rule, and a 10% CV stop threshold before measurement. The exact percentile, quartile, trimmed-mean, and sample-SD conventions were set afterward and logged in Protocol Section 13. Overlapping intervals mean “no clear difference” under my rule, not equal energy. The late `FROZEN` status change is disclosed in Section 2.

The C2 categories omit the pattern of unclear Pandas–Polars energy and clearly higher Dask. Reading D preserves the original categories without forcing a verdict. Nothing here establishes outcomes for the paper's other models, COCO, another machine, or the older stack.

## 6. Next experiment

I would test whether Dask's high data-stage energy on small inputs is mostly fixed startup and scheduling cost. I would run the same Insurance `data` pipeline at controlled row counts (1,338, 13,380, and 133,800) by repeating the original rows, keeping the columns and preprocessing fixed. A new measurement session would use its own idle baseline, randomized order across configurations, fresh processes, one warm-up, and ten measured runs per configuration. If Dask's energy ratio to Pandas shrinks as the data grows, that would support a fixed-cost explanation. If the ratio stays high or grows, it would weaken that explanation. I have not run this experiment; it is a concrete question to raise with the paper's authors.

## 7. Reproducibility and use of AI

The full run used code commit `4badf06`. Its [raw session](../results/raw/full-20261025-135703-JICxLk/) retains the schedule, all warm-ups and measured runs, the session-specific idle baseline, system-state records, and [input SHA-256 values](../results/raw/full-20261025-135703-JICxLk/input_sha256.txt). The [protocol](../PROTOCOL.md), [locked dependencies](../requirements.lock), measurement runner, and analysis script are in the repository. A reader can obtain the datasets from the sources in Protocol Section 3, verify their hashes, recreate the environment, then run `sudo ./scripts/run_measurements.sh` and `.venv/bin/python scripts/analyze_results.py <new-session-directory>`. The MovieLens data are not redistributed. A top-level README, download helper, and clean-clone test are still missing from this draft's reproducibility package.

I chose the claims, datasets, measurement constraints, and manual median check, and I operated the full benchmark. AI assisted with the backend code, analysis script, choice of how to handle the C2 criterion gap, and this report's draft prose. I will review the wording and calculations before sharing the report. The raw measurements are from my machine, not generated by AI.
