# Claim figures C1–C6

These are plots of measured full-stage net energy medians and 95% bootstrap confidence intervals, not simulated data or values copied from the paper. Pandas is blue, Polars green, and Dask orange. Every claim has its own labeled joule scale. C5 and both C6 panels use zoomed axes to make interval overlap visible; the dot positions must be read with the tick labels, not compared by bar length.

- C1 and C2 use session-1 [`summary.csv`](../summary.csv), CPU package energy.
- C3–C5 use the current-environment rows of session-2 [`summary.csv`](../session2-20261116-012318-MJNiIT/summary.csv), CPU package energy.
- C6 uses the current-environment NCF rows of the session-2 summary; its left panel is CPU package energy and its right panel is GPU board energy. The two panels have different scales.

The SVG files are embedded in `report/REPORT.md`; PNG copies are provided for export. Regenerate both formats from the two committed summaries with Matplotlib in an isolated environment, without changing the measurement lock files:

```bash
uv run --no-project --python 3.12.14 --with matplotlib==3.11.2 python scripts/plot_claims.py
```
