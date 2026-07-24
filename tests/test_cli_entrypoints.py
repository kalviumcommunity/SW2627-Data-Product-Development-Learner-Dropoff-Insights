from __future__ import annotations

import subprocess
import sys
import unittest


class TestCliEntrypoints(unittest.TestCase):
    def test_documented_python_modules_expose_help(self) -> None:
        modules = [
            "src.ingestion.run_data_pipeline",
            "src.ingestion.validate_data_quality",
            "src.database.build_aggregates",
            "src.analysis.run_analysis_pipeline",
        ]

        for module in modules:
            with self.subTest(module=module):
                result = subprocess.run(
                    [sys.executable, "-m", module, "--help"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(
                    result.returncode,
                    0,
                    msg=f"{module} failed:\n{result.stderr}",
                )
                self.assertIn("usage:", result.stdout.lower())
