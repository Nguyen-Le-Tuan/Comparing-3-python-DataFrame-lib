<!--
Skeleton only: headings and guiding questions. Delete each comment once the section is written.
Target length: 2–4 pages. Suggested writing order: 3 → 4 → 5 → 6 → 1 → 2 → 7, then read aloud.
Check every sentence with a number: does it state the condition (this laptop, these versions, full stage, n = 10)?
-->

# <!-- Title: what was replicated, on what, at what scale? -->

<!-- Author, affiliation, date, repository link. -->

## 1. What I replicated

<!--
- Which paper (authors, venue, arXiv ID)?
- Which two claims (C1, C2), and where in the paper (table, section, figure)?
- Why is this a "small-scale replication" and not a reproduction? (team, hardware, versions)
- What is the main result, in one sentence?
- Budget: about half a page. Write this section near the end.
-->

## 2. Setup and differences from the paper

<!--
- Hardware and software: which rows of PROTOCOL.md Section 10 does a reader need?
- What did I measure (net CPU package energy, runtime), and how is "net" computed? Which idle baseline: 5.139 W (session) vs 4.776 W (validation, Oct 19)?
- How many runs, warm-ups, order, pauses? (PROTOCOL.md Section 7)
- How does this differ from the paper's method (energy-cores + energy-ram vs energy-pkg; 5 runs vs 10; 2022 vs 2026 versions; 1,000 vs 1,338 rows)?
- Decision rule: when do two libraries "differ"? (PROTOCOL.md Section 8)
- Was the protocol frozen before the full run? Where is it?
-->

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

<!--
- What is the largest gap (Dask +55.7% vs ~14%)? What is the second (Pandas < Polars on Insurance)?
- What does the data-stage share (data / full) suggest about where Dask's extra energy goes?
- Which explanations are possible (versions, data size, Dask overhead, P/E cores, pkg vs cores+ram)?
- For each explanation: what experiment would test it? Have I run it? (If not: "may", not "because".)
-->

## 5. Limitations

<!--
- Which items from PROTOCOL.md Section 11 actually change how the results should be read?
- What does the C2 criterion gap mean for the verdict?
- What do these results NOT tell us (other datasets, models, machines, versions)?
- Which analysis conventions were set after the run (PROTOCOL.md Section 13)?
-->

## 6. Next experiment

<!--
- If I could run only one more experiment, which one, and which explanation from Section 4 would it test?
- What result would support that explanation, and what result would reject it?
- Could this become the specific question for the email?
-->

## 7. Reproducibility and use of AI

<!--
- How can a reader re-run this (README, data download + SHA-256, commands)?
- Which commit and raw session directory are the results from?
- What did AI assist with, and what was mine (PROTOCOL.md Section 12)? Who wrote this report's text?
-->
