# Full-stage comparison

| Dataset | Library | Data net (J) | Full net (J, 95% CI) | Full runtime (s, 95% CI) | Data share | Training estimate (J) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| insurance | pandas | 4.107 | 16.736 [16.615, 16.910] | 0.897 [0.896, 0.899] | 24.5% | 12.628 |
| insurance | polars | 2.622 | 18.309 [18.132, 18.377] | 0.982 [0.977, 0.986] | 14.3% | 15.687 |
| insurance | dask | 15.415 | 26.061 [25.996, 26.118] | 1.405 [1.403, 1.414] | 59.1% | 10.647 |
| ml-1m | pandas | 49.147 | 76.238 [75.702, 76.723] | 3.744 [3.733, 3.752] | 64.5% | 27.092 |
| ml-1m | polars | 46.393 | 76.632 [76.419, 77.423] | 2.381 [2.376, 2.405] | 60.5% | 30.238 |
| ml-1m | dask | 173.879 | 197.827 [196.951, 198.682] | 10.031 [10.006, 10.049] | 87.9% | 23.948 |

Values are medians of 10 measured runs. CI is the percentile bootstrap interval for the median.
Data share and training estimate use the stage medians, not paired run differences.
