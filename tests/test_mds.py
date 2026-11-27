import json
import shutil
import uuid
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MDS = ROOT / "shared/tools/mds.py"
DATAPACKS = ROOT / "projects/datapacks"


class MDSCommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(
            prefix="mds-test-", dir=DATAPACKS
        )
        self.project = Path(self.temp.name)
        self.slug = self.project.name
        config = {
            "projectName": "Temporary Test",
            "slug": self.slug,
            "projectType": "datapacks",
            "targetMinecraftVersion": "1.21.1",
            "dependencies": [],
            "status": "planning",
            "verification": {
                "staticInspection": False,
                "build": False,
                "runtimeTest": False
            }
        }
        (self.project / "project.json").write_text(
            json.dumps(config, indent=2), encoding="utf-8"
        )
        (self.project / "README.md").write_text(
            "# Temporary Test\n\n- Target Minecraft version: 1.21.1\n- Status: Planning\n",
            encoding="utf-8"
        )
        for folder in ("specifications", "tasks", "reports", "assets"):
            (self.project / folder).mkdir()
        (self.project / "specifications/PROJECT_SPEC.md").write_text("# Spec\n")
        (self.project / "tasks/TASKS.md").write_text("# Tasks\n")
        (self.project / "reports/QA_REPORT.md").write_text("# QA\n")

    def tearDown(self):
        self.temp.cleanup()

    def run_cmd(self, *args):
        return subprocess.run(
            [sys.executable, str(MDS), *args],
            cwd=ROOT, capture_output=True, text=True
        )

    def test_help(self):
        result = self.run_cmd("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("qa", result.stdout)
        self.assertIn("doctor", result.stdout)

    def test_list(self):
        self.assertEqual(self.run_cmd("list").returncode, 0)

    def test_validate(self):
        result = self.run_cmd("validate")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("VALIDATION PASSED", result.stdout)

    def test_show_mining_challenge(self):
        result = self.run_cmd("show", "--slug", "mining-challenge")
        self.assertEqual(result.returncode, 0)
        self.assertIn('"targetMinecraftVersion": "1.21.11"', result.stdout)

    def test_unknown_project(self):
        result = self.run_cmd("show", "--slug", "not-existing-project")
        self.assertNotEqual(result.returncode, 0)

    def test_set_status_updates_valid_json_and_readme(self):
        result = self.run_cmd(
            "set-status", "--slug", self.slug, "--status", "development"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        data = json.loads((self.project / "project.json").read_text())
        self.assertEqual(data["status"], "development")
        self.assertIn("- Status: development",
                      (self.project / "README.md").read_text())

    def test_set_version_updates_json_and_readme(self):
        result = self.run_cmd(
            "set-version", "--slug", self.slug, "--version", "1.21.11"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        data = json.loads((self.project / "project.json").read_text())
        self.assertEqual(data["targetMinecraftVersion"], "1.21.11")
        self.assertIn("- Target Minecraft version: 1.21.11",
                      (self.project / "README.md").read_text())


    def test_create_project_copies_workflow_guide(self):
        slug = "test-workflow-" + uuid.uuid4().hex[:8]
        project = DATAPACKS / slug
        try:
            result = self.run_cmd(
                "create", "--name", "Workflow Test",
                "--slug", slug, "--type", "datapacks",
                "--target-version", "1.21.11"
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            guide = project / "specifications/WORKFLOW_GUIDE.md"
            self.assertTrue(guide.is_file())
            self.assertIn("exact target version",
                          guide.read_text(encoding="utf-8"))
        finally:
            if project.exists():
                shutil.rmtree(project)



    def test_workflow_shows_next_unverified_stage(self):
        result = self.run_cmd("workflow", "--slug", self.slug)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("1. Static inspection", result.stdout)
        self.assertIn("[TODO]", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
