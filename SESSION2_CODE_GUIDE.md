# Session 2 code map

This note explains the code added before any session-2 benchmark. Functional smoke tests train models to check behavior, but they do not call `perf`, sample energy, or produce an energy verdict.

## One run through the pipeline

```text
insurance.csv -> Pandas / Polars / Dask -> identical X, y -> models.py -> test R², RMSE
ML-1M files  -> Pandas / Polars / Dask -> identical X, IDs -> models.py -> SVD or NCF
```

`pipeline.py` does loading, preprocessing, checksums and `--model` selection. It rejects an Insurance model on ML-1M or an ML-1M model on Insurance. If `--model` is omitted, the old Random Forest and TruncatedSVD commands still work. Its Polars Insurance branch uses the older expression syntax only inside the Python 3.8 environment; both branches produce the same arrays.

`models.py` receives arrays after dataframe work. Insurance models share one seeded 80/20 split. SVR scales the target inside its estimator, XGBoost uses one CPU thread, and TabNet converts the data to `float32`, scales training targets and trains on CUDA. For NCF, only observed ratings are positives; it splits them per user, samples one missing movie per positive as an assumed negative, and trains user/movie embeddings plus an MLP on CUDA. All models print sanity metrics, not benchmark scores.

The exact settings and the meaning of sampled negatives are in [Protocol Section 4](PROTOCOL.md#4-pipeline-definition). Changes to those choices need a protocol edit before a pilot.

## Files and commands

| File | Purpose |
| --- | --- |
| `requirements.in`, `requirements.lock` | Current Python 3.12 dependencies, including XGBoost, PyTorch, pytorch-tabnet and NVML bindings. |
| `requirements-legacy.in`, `requirements-legacy.lock` | Separate Python 3.8 stack with the three dataframe versions from the paper. |
| `scripts/smoke_session2.py` | Runs data and full stages for SVR, XGBoost, TabNet and NCF on all three backends; compares checksums, split hashes, devices and finite metrics. Logs go to a new timestamped directory. |
| `scripts/smoke_legacy.py` | Runs Insurance data and Random Forest in both environments; verifies matching inputs and split indices. |
| `scripts/gpu_power.py` | Samples NVML board watts every 100 ms; later integrates each run's ±2 s window and subtracts idle GPU power. |
| `scripts/validate_gpu.py` | Controlled two-load GPU meter check with pass limits fixed in Section 7. It passed on Nov 15 after adding a 40 s cooldown. |
| `scripts/run_session2.sh` | Separate draft runner for 30 configurations, 30 warm-ups and 300 measured runs. It requires an explicit `--full` and a passing GPU validation file. **Not run.** |
| `scripts/analyze_session2.py` | Audits a complete session-2 directory, joins CPU and GPU raw values, and computes medians and confidence intervals within each environment/model. Never reads session-1 runs by default. |

To repeat functional checks without measuring energy:

```bash
.venv/bin/python scripts/smoke_session2.py --models svr xgboost tabnet ncf
.venv/bin/python scripts/smoke_legacy.py
```

The first smoke-test evidence is in `results/smoke_test/session2/`, and the first version-comparison evidence is in `results/smoke_test/session2_legacy/`. Each includes separate stdout and stderr files, so a failed command can be inspected. Repeated smoke tests create new timestamped directories instead of replacing that evidence.

## What is still pending

The new GPU meter passed its controlled validation on Nov 15; the failed first attempt and passing second attempt are both retained under `results/validation/`. The repeated CPU validation passed on Nov 16 with kernel `7.0.0-42-generic`; its evidence is in `results/validation-20261116-001345/`. The session-2 runner and analysis have passed syntax checks, a schedule-count check, and a synthetic raw-session audit. Excluded TabNet and NCF pilots ran on Nov 16; an offline TabNet repeat resolved the anomalous idle baseline, although the cause of the first reading is unknown. No official session-2 benchmark has run. Freeze the protocol/code commit before any official measurement.
