# Insurance pipeline smoke test — 2026-10-24

Environment: Pandas 3.0.6, Polars 2.0.0, Dask 2026.8.0, scikit-learn 1.9.1.

Commands run for each of `pandas`, `polars`, and `dask`:

```bash
.venv/bin/python pipeline.py --lib <library> --data insurance --stage data
.venv/bin/python pipeline.py --lib <library> --data insurance --stage full
```

Each reader saw the same raw input: `(1338, 7)`, columns `age`, `sex`, `bmi`,
`children`, `smoker`, `region`, `charges` in that order, and zero missing cells.
The CSV SHA-256 was `388eff679557d08ac19f463d025de5e0b4adc482537c8456d19934d78621fd47`.

All six commands exited successfully. All three libraries produced the same
feature order specified in `PROTOCOL.md`, `X` shape `(1338, 9)` and `y` shape
`(1338,)`, with float64 arrays. Checksums over 21 file-order mini-batches were:

| Library | X sum | y sum | Test R² (`full`) |
| --- | ---: | ---: | ---: |
| Pandas | 2288.0000000000 | 17755824.9907590002 | 0.8643208445906077 |
| Polars | 2288.0000000000 | 17755824.9907590002 | 0.8643208445906077 |
| Dask | 2288.0000000000 | 17755824.9907590002 | 0.8643208445906077 |

Dask reported one partition for this input. Compared with Pandas, the maximum
absolute elementwise difference in `X` was `4.440892098500626e-16` for Polars
and `0.0` for Dask; `y` matched exactly for both. This is a functional smoke
test, not an energy measurement.
