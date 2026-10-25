## Pandas + Insurance + full
I use this command to find and sort the results:
```
IDLE_W=$(cat "$RUN_DIR/idle/idle_power_w.txt")

awk -F, -v idle="$IDLE_W" '
  NR > 1 && $2 == "measured" &&
  $4 == "pandas" && $5 == "insurance" && $6 == "full" {
    printf "%s,%.6f,%.6f,%.6f\n", $7, $12, $14, $12-idle*$14
  }
' "$RUN_DIR/runs.csv" | sort -t, -k4,4n
```

The results it returned:

```
101_measured_r08_pandas_insurance_full,21.200000,0.899701,16.576045
059_measured_r04_pandas_insurance_full,21.280000,0.914033,16.582385
121_measured_r10_pandas_insurance_full,21.220000,0.895948,16.615333
079_measured_r06_pandas_insurance_full,21.230000,0.897280,16.618489
071_measured_r05_pandas_insurance_full,21.290000,0.897253,16.678626
088_measured_r07_pandas_insurance_full,21.390000,0.894545,16.792541
115_measured_r09_pandas_insurance_full,21.420000,0.892743,16.831802
046_measured_r03_pandas_insurance_full,21.520000,0.896925,16.910312
030_measured_r02_pandas_insurance_full,21.540000,0.898646,16.921466
022_measured_r01_pandas_insurance_full,21.580000,0.897264,16.968568

```

The 10 net energy values (J), sorted in ascending order:

```
16.576045
16.582385
16.615333
16.618489
16.678626
16.792541
16.831802
16.910312
16.921466
16.968568
```

Idle power:

```
idle_power = 5.139437 W
```

Because there are 10 values, the median is the average of the 5th and 6th values:

```
median = (16.678626 + 16.792541) / 2
       = 16.7355835 J
```