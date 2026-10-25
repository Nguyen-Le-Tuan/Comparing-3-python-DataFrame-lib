"""Check the measured-run audit against the manual calculation."""

import sys
import unittest
from pathlib import Path
from statistics import median


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_results import (  # noqa: E402
    DEFAULT_SESSION,
    audit_session,
    bootstrap_median_ci,
    quartiles,
    summarize_measured_runs,
    trimmed_mean_10pct,
)


class AnalyzeResultsTest(unittest.TestCase):
    def test_manual_median(self) -> None:
        _, measured = audit_session(DEFAULT_SESSION)
        values = [
            run.net_energy_j for run in measured
            if (run.library, run.dataset, run.stage) == ("pandas", "insurance", "full")
        ]
        self.assertEqual(len(values), 10)
        self.assertAlmostEqual(median(values), 16.7355835, delta=1e-6)

    def test_all_configurations(self) -> None:
        _, measured = audit_session(DEFAULT_SESSION)
        summary = summarize_measured_runs(measured)
        self.assertEqual(len(summary), 12)
        self.assertTrue(all(row["n"] == 10 for row in summary))
        self.assertTrue(all(row["cv_net_pct"] < 10 for row in summary))
        for row in summary:
            self.assertLessEqual(row["q1_net_j"], row["median_net_j"])
            self.assertLessEqual(row["median_net_j"], row["q3_net_j"])
            self.assertLessEqual(row["ci95_low_net_j"], row["median_net_j"])
            self.assertLessEqual(row["median_net_j"], row["ci95_high_net_j"])

    def test_statistical_conventions(self) -> None:
        values = list(range(1, 11))
        self.assertEqual(quartiles(values), (3.25, 7.75))
        self.assertEqual(trimmed_mean_10pct(values), 5.5)
        self.assertEqual(bootstrap_median_ci(values), bootstrap_median_ci(values))


if __name__ == "__main__":
    unittest.main()
