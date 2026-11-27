import argparse
import json
import re
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECTS = ROOT / "projects"

PROJECT_TYPES = [
    "mods",
    "datapacks",
    "resource-packs",
    "models",
    "textures",
    "ui",
   "animations",
]


TEMPLATE_DIRS = {'mods': 'mod', 'datapacks': 'datapack', 'resource-packs': 'resource-pack', 'models': '3d-models', 'textures': 'textures', 'ui': 'ui', 'animations': 'animations'}


def create_project(args):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", args.slug):
        print("ERROR: slug must use lowercase letters, numbers and hyphens.")
        return 1

    if args.type not in PROJECT_TYPES:
        print("ERROR: Unsupported project type.")
        return 1

    path = PROJECTS / args.type / args.slug

    if path.exists():
        print(f"ERROR: Project already exists: {path}")
        return 1

    path.mkdir(parents=True)

    config = {
        "projectName": args.name,
        "slug": args.slug,
        "projectType": args.type,
        "targetMinecraftVersion": args.target_version,
        "modLoader": None,
        "javaVersion": None,
        "buildSystem": None,
        "dependencies": [],
        "status": "planning",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "verification": {
            "staticInspection": False,
            "build": False,
            "runtimeTest": False
        }
    }

    (path / "project.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )

    (path / "README.md").write_text(
        f"# {args.name}\n\n"
        f"- Type: {args.type}\n"
        f"- Target Minecraft version: {args.target_version or '未指定'}\n"
        "- Status: Planning\n",
        encoding="utf-8"
    )

    for folder in ["specifications", "tasks", "reports", "assets"]:
        (path / folder).mkdir()
    (path / "assets" / ".gitkeep").touch()

    template_name = TEMPLATE_DIRS.get(args.type)
    if template_name:
        guide = ROOT / "shared" / "templates" / template_name / "WORKFLOW.md"
        if guide.is_file():
            (path / "specifications" / "WORKFLOW_GUIDE.md").write_text(
                guide.read_text(encoding="utf-8"), encoding="utf-8"
            )

    (path / "specifications" / "PROJECT_SPEC.md").write_text(
        "# Project Specification\n\n"
        "## Objectives\n\n"
        "## Requirements\n\n"
        "## Features\n\n"
        "## Technical Design\n\n"
        "## Acceptance Criteria\n",
        encoding="utf-8"
    )

    (path / "tasks" / "TASKS.md").write_text(
        "# Project Tasks\n\n"
        "## Backlog\n\n"
        "## In Progress\n\n"
        "## Review\n\n"
        "## Completed\n",
        encoding="utf-8"
    )

    (path / "reports" / "QA_REPORT.md").write_text(
        "# Quality Assurance Report\n\n"
        "- Static inspection: Not tested\n"
        "- Build: Not tested\n"
        "- Runtime test: Not tested\n"
        "- Final decision: Pending\n",
        encoding="utf-8"
    )

    print(f"PROJECT CREATED: {path.relative_to(ROOT)}")
    return 0


def list_projects(_args):
    found = sorted(PROJECTS.glob("**/project.json"))

    if not found:
        print("No projects registered.")
        return 0

    for file in found:
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
            print(
                f"{data.get('slug', '?')} | "
                f"{data.get('projectType', '?')} | "
                f"{data.get('status', '?')}"
            )
        except Exception as error:
            print(f"INVALID: {file.relative_to(ROOT)}: {error}")

    return 0


def validate_projects(_args):
    files = sorted(PROJECTS.glob("**/project.json"))
    errors = []
    checked = 0
    required_files = [
        "project.json", "README.md",
        "specifications/PROJECT_SPEC.md",
        "tasks/TASKS.md", "reports/QA_REPORT.md"
    ]
    required_dirs = ["specifications", "tasks", "reports", "assets"]
    valid_statuses = {"planning", "development", "review", "completed", "paused"}

    for file in files:
        rel = file.relative_to(ROOT)
        folder = file.parent
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except Exception as error:
            errors.append(f"{rel}: invalid JSON: {error}")
            continue

        problems = []
        for key in ("projectName", "slug", "projectType", "status",
                    "dependencies", "verification"):
            if key not in data or data[key] is None or data[key] == "":
                problems.append(f"missing or empty field: {key}")

        if data.get("projectType") not in PROJECT_TYPES:
            problems.append("unsupported projectType")
        if data.get("slug") != folder.name:
            problems.append("slug does not match directory name")
        if data.get("projectType") != folder.parent.name:
            problems.append("projectType does not match directory")
        if data.get("status") not in valid_statuses:
            problems.append("invalid status")
        if not isinstance(data.get("dependencies"), list):
            problems.append("dependencies must be a list")

        version = data.get("targetMinecraftVersion")
        if version is not None and (
            not isinstance(version, str) or not version.strip()
        ):
            problems.append("targetMinecraftVersion must be null or a non-empty string")

        verification = data.get("verification")
        if not isinstance(verification, dict):
            problems.append("verification must be an object")
        else:
            for key in ("staticInspection", "build", "runtimeTest"):
                if key not in verification or not isinstance(verification[key], bool):
                    problems.append(f"verification.{key} must be a boolean")

        for name in required_files:
            if not (folder / name).is_file():
                problems.append(f"missing required file: {name}")
        for name in required_dirs:
            if not (folder / name).is_dir():
                problems.append(f"missing required directory: {name}")

        checked += 1
        if problems:
            errors.extend(f"{rel}: {problem}" for problem in problems)
            print(f"[ERROR] {rel}")
        else:
            print(f"[OK] {rel}")

    print(f"\\nProjects checked: {checked}")
    print(f"Errors: {len(errors)}")
    for error in errors:
        print(f"[ERROR] {error}")

    if errors:
        print("VALIDATION FAILED")
        return 1

    print("VALIDATION PASSED")
    return 0



def find_project(slug):
    matches = list(PROJECTS.glob(f"**/{slug}/project.json"))
    if len(matches) != 1:
        return None
    return matches[0]


def show_project(args):
    file = find_project(args.slug)
    if file is None:
        print(f"ERROR: Project not found or ambiguous: {args.slug}")
        return 1
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except Exception as error:
        print(f"ERROR: Invalid project JSON: {error}")
        return 1
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"Project path: {file.parent.relative_to(ROOT)}")
    return 0



def set_project_status(args):
    file = find_project(args.slug)
    if file is None:
        print(f"ERROR: Project not found or ambiguous: {args.slug}")
        return 1
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
        data["status"] = args.status
        file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8"
        )
    except Exception as error:
        print(f"ERROR: Could not update project: {error}")
        return 1

    readme = file.parent / "README.md"
    if readme.is_file():
        content = readme.read_text(encoding="utf-8")
        content, count = re.subn(
            r"(?m)^- Status:.*$",
            f"- Status: {args.status}",
            content
        )
        if count:
            readme.write_text(content, encoding="utf-8")
    print(f"STATUS UPDATED: {args.slug} -> {args.status}")
    return 0


def set_project_version(args):
    file = find_project(args.slug)
    if file is None:
        print(f"ERROR: Project not found or ambiguous: {args.slug}")
        return 1
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
        data["targetMinecraftVersion"] = args.version
        file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8"
        )
    except Exception as error:
        print(f"ERROR: Could not update project: {error}")
        return 1

    readme = file.parent / "README.md"
    if readme.is_file():
        content = readme.read_text(encoding="utf-8")
        content, count = re.subn(
            r"(?m)^- Target Minecraft version:.*$",
            f"- Target Minecraft version: {args.version}",
            content
        )
        if count:
            readme.write_text(content, encoding="utf-8")
    print(f"VERSION UPDATED: {args.slug} -> {args.version}")
    return 0


def run_qa(_args):
    commands = [
        [sys.executable, "-m", "py_compile",
         "shared/tools/mds.py", "tests/test_mds.py"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        [sys.executable, "shared/tools/mds.py", "validate"],
    ]
    for command in commands:
        print("\\n>>>", " ".join(command))
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode != 0:
            print("QA FAILED. Changes must not be committed.")
            return result.returncode
    print("\\nQA PASSED")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Minecraft Development Studio project manager"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="Create a new project")
    create.add_argument("--name", required=True)
    create.add_argument("--slug", required=True)
    create.add_argument("--type", required=True, choices=PROJECT_TYPES)
    create.add_argument("--target-version", default=None)
    create.set_defaults(func=create_project)

    listing = sub.add_parser("list", help="List registered projects")
    listing.set_defaults(func=list_projects)

    validate = sub.add_parser("validate", help="Validate project configs")
    validate.set_defaults(func=validate_projects)

    show = sub.add_parser("show", help="Show project details")
    show.add_argument("--slug", required=True)
    show.set_defaults(func=show_project)

    status = sub.add_parser("set-status", help="Change project status")
    status.add_argument("--slug", required=True)
    status.add_argument("--status", required=True,
                        choices=["planning", "development", "review", "completed", "paused"])
    status.set_defaults(func=set_project_status)

    version = sub.add_parser("set-version", help="Change target Minecraft version")
    version.add_argument("--slug", required=True)
    version.add_argument("--version", required=True)
    version.set_defaults(func=set_project_version)

    qa = sub.add_parser("qa", help="Run syntax checks, tests and project validation")
    qa.set_defaults(func=run_qa)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
