# Session 2 full-stage results

| Environment | Dataset | Model | Library | Net CPU J | Net GPU J | Data share | Training estimate J |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| current | insurance | rf | dask | 26.669 | 0.170 | 59.1% | 10.902 |
| current | insurance | svr | dask | 23.834 | 0.179 | 66.2% | 8.067 |
| current | insurance | tabnet | dask | 83.075 | 18.828 | 19.0% | 67.309 |
| current | insurance | xgboost | dask | 25.504 | 7.596 | 61.8% | 9.737 |
| current | ml-1m | ncf | dask | 866.208 | 231.111 | 21.4% | 680.790 |
| current | ml-1m | svd | dask | 211.108 | 0.991 | 87.8% | 25.689 |
| current | insurance | rf | pandas | 17.045 | 0.142 | 25.0% | 12.792 |
| current | insurance | svr | pandas | 14.314 | 0.078 | 29.7% | 10.061 |
| current | insurance | tabnet | pandas | 73.181 | 18.535 | 5.8% | 68.929 |
| current | insurance | xgboost | pandas | 15.988 | 7.383 | 26.6% | 11.735 |
| current | ml-1m | ncf | pandas | 740.193 | 229.634 | 6.7% | 690.968 |
| current | ml-1m | svd | pandas | 76.503 | 0.392 | 64.3% | 27.277 |
| current | insurance | rf | polars | 18.800 | 0.060 | 14.3% | 16.106 |
| current | insurance | svr | polars | 15.612 | 0.112 | 17.3% | 12.917 |
| current | insurance | tabnet | polars | 75.424 | 18.672 | 3.6% | 72.729 |
| current | insurance | xgboost | polars | 17.600 | 7.147 | 15.3% | 14.906 |
| current | ml-1m | ncf | polars | 737.516 | 227.870 | 6.2% | 691.728 |
| current | ml-1m | svd | polars | 76.734 | 0.263 | 59.7% | 30.946 |
| legacy | insurance | rf | dask | 14.169 | 0.086 | 58.5% | 5.874 |
| legacy | insurance | rf | pandas | 10.446 | 0.112 | 36.6% | 6.618 |
| legacy | insurance | rf | polars | 11.159 | 0.096 | 40.6% | 6.628 |
