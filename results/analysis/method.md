# Analysis method

Source: `results/raw/full-20261025-135703-JICxLk/`. I use only the 120 `measured` rows; warm-ups remain in the raw record. The script stops if the schedule, file set, run status, or 10-run configuration counts do not match.

- Net CPU package energy (J) = `energy_pkg_j - idle_power_w * elapsed_s`, using this session's idle baseline.
- Runtime is `elapsed_s` from the package-energy `perf` event. Peak RSS is reported in MiB (`max_rss_kb / 1024`).
- Median and IQR use the 10 measured values per configuration. Quartiles use linear interpolation at 25% and 75%.
- The 10% trimmed mean removes the lowest and highest value from each set of 10.
- A 95% percentile bootstrap interval for each median uses 10,000 resamples with replacement and seed 42. Each metric and configuration starts from the same seed.
- CV uses sample standard deviation divided by mean net energy. A configuration above 10% stops analysis, as specified in the protocol.

These conventions fill in details not specified by the frozen protocol. The script reports measurements and derived statistics; I interpret C1 and C2 separately.
