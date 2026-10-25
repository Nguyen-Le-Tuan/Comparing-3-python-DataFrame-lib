# Step 8 interpretation

I compare the `full` stage with the paper's end-to-end results. I compare rankings and relative gaps, not absolute joules, because the hardware, library versions, and energy domains differ. The local medians and 95% bootstrap CIs come from [summary.csv](summary.csv); data-stage shares are in [full_stage_table.md](full_stage_table.md).

For Insurance (C1), the paper reports Pandas ≈ Polars < Dask, with Dask about 14% above Pandas. My full-stage medians rank Pandas (16.736 J) < Polars (18.309 J) < Dask (26.061 J). Polars is 9.4% above Pandas and Dask is 55.7% above Pandas. None of the three energy CIs overlap, so Pandas and Polars count as different under the decision rule in the protocol. Dask also has the longest runtime (1.405 s versus 0.897 s for Pandas and 0.982 s for Polars), with non-overlapping runtime CIs.

For MovieLens-1M (C2), the paper reports Polars < Pandas < Dask, with Pandas using about 2.3 times the energy of Polars. My point medians rank Pandas (76.238 J) < Polars (76.632 J) < Dask (197.827 J). The Pandas–Polars gap is only 0.52%, and their energy CIs overlap, so I report no clear difference between them. Dask is clearly higher than both because its CI does not overlap either one.

The largest net-energy CV among the 12 configurations is 1.50%, below the protocol's 10% stop threshold. The data-stage share of full-stage energy is 24.5%, 14.3%, and 59.1% for Pandas, Polars, and Dask on Insurance; on MovieLens-1M it is 64.5%, 60.5%, and 87.9%. Each share divides the data-stage median by the full-stage median; it is not a separately measured phase within a full run.
