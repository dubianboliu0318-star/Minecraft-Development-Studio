import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MDS = ROOT / "shared/tools/mds.py"

class MDSCommandTests(unittest.TestCase):
    def run_cmd(self, *args):
        return subprocess.run(
            [sys.executable, str(MDS), *args],
            cwd=ROOT, capture_output=True, text=True
        )

    def test_help(self):
        result = self.run_cmd("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("set-status", result.stdout)

    def test_list(self):
        result = self.run_cmd("list")
        self.assertEqual(result.returncode, 0)

    def test_validate(self):
        result = self.run_cmd("validate")
        self.assertEqual(result.returncode, 0)
        self.assertIn("VALIDATION PASSED", result.stdout)

    def test_show_mining_challenge(self):
        result = self.run_cmd("show", "--slug", "mining-challenge")
        self.assertEqual(result.returncode, 0)
        self.assertIn('"targetMinecraftVersion": "1.21.11"', result.stdout)

    def test_unknown_project(self):
        result = self.run_cmd("show", "--slug", "not-existing-project")
        self.assertNotEqual(result.returncode, 0)

if __name__ == "__main__":
    unittest.main(verbosity=2)
