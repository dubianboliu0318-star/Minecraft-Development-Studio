import argparse
import json
import re
import sys
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

    for file in files:
        try:
            data = json.loads(file.read_text(encoding="utf-8"))

            required = ["projectName", "slug", "projectType", "status"]
            for key in required:
                if not data.get(key):
                    errors.append(f"{file}: missing {key}")

            if data.get("projectType") not in PROJECT_TYPES:
                errors.append(f"{file}: unsupported projectType")

            if not isinstance(data.get("dependencies", []), list):
                errors.append(f"{file}: dependencies must be a list")

            print(f"[OK] {file.relative_to(ROOT)}")

        except Exception as error:
            errors.append(f"{file}: {error}")

    print(f"\nProjects checked: {len(files)}")
    print(f"Errors: {len(errors)}")

    for error in errors:
        print(f"[ERROR] {error}")

    if errors:
        print("VALIDATION FAILED")
        return 1

    print("VALIDATION PASSED")
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

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
