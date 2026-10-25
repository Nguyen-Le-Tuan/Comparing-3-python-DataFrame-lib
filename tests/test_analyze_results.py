"""Check the measured-run audit against the manual calculation."""

import sys
import unittest
from pathlib import Path
from statistics import median


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_results import DEFAULT_SESSION, audit_session  # noqa: E402


class AnalyzeResultsTest(unittest.TestCase):
    def test_manual_median(self) -> None:
        _, measured = audit_session(DEFAULT_SESSION)
        values = [
            run.net_energy_j for run in measured
            if (run.library, run.dataset, run.stage) == ("pandas", "insurance", "full")
        ]
        self.assertEqual(len(values), 10)
        self.assertAlmostEqual(median(values), 16.7355835, delta=1e-6)


if __name__ == "__main__":
    unittest.main()
