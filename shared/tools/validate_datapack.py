import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECTS = ROOT / "projects" / "datapacks"


def validate_project(folder):
    errors = []
    warnings = []
    metadata = folder / "pack.mcmeta"
    data_dir = folder / "data"

    print(f"\n=== DATAPACK QA: {folder.name} ===")

    if not metadata.exists() and not data_dir.exists():
        print("[PENDING] pack.mcmeta and data/ are not created yet.")
        return 0

    if not metadata.is_file():
        errors.append("Missing pack.mcmeta")
    if not data_dir.is_dir():
        errors.append("Missing data/ directory")

    if metadata.is_file():
        try:
            content = json.loads(metadata.read_text(encoding="utf-8"))
            if not isinstance(content, dict):
                errors.append("pack.mcmeta must contain a JSON object")
            else:
                pack = content.get("pack")
                if not isinstance(pack, dict):
                    errors.append("pack.mcmeta requires a pack object")
                else:
                    fmt = pack.get("pack_format")
                    if not isinstance(fmt, int) or isinstance(fmt, bool) or fmt < 1:
                        errors.append("pack.pack_format must be a positive integer")
                    if "description" not in pack:
                        errors.append("pack.description is missing")
            print("[OK] pack.mcmeta JSON and required fields")
        except Exception as error:
            errors.append(f"Invalid pack.mcmeta: {error}")

    if data_dir.is_dir():
        namespaces = [p for p in data_dir.iterdir() if p.is_dir()]
        if not namespaces:
            warnings.append("No namespace directories found in data/")
        for namespace in namespaces:
            if not re.fullmatch(r"[a-z0-9_.-]+", namespace.name):
                errors.append(f"Invalid namespace name: {namespace.name}")

            for file in namespace.rglob("*.json"):
                try:
                    json.loads(file.read_text(encoding="utf-8"))
                except Exception as error:
                    errors.append(f"Invalid JSON {file.relative_to(folder)}: {error}")

            for file in namespace.rglob("*.mcfunction"):
                try:
                    lines = file.read_text(encoding="utf-8").splitlines()
                    for number, line in enumerate(lines, 1):
                        if line.startswith("/"):
                            errors.append(
                                f"{file.relative_to(folder)}:{number}: "
                                "function commands must not start with /"
                            )
                except UnicodeDecodeError as error:
                    errors.append(f"Invalid UTF-8 {file.relative_to(folder)}: {error}")

        print(f"[OK] Namespace scan: {len(namespaces)} found")

    for warning in warnings:
        print(f"[PENDING] {warning}")
    for error in errors:
        print(f"[ERROR] {error}")

    if errors:
        print(f"DATAPACK QA FAILED: {len(errors)} error(s)")
        return 1

    print("DATAPACK QA PASSED")
    return 0


def main():
    parser = argparse.ArgumentParser(description="MDS Datapack Validator")
    parser.add_argument("--slug", help="Validate one datapack project")
    args = parser.parse_args()

    if args.slug:
        matches = list(PROJECTS.glob(f"**/{args.slug}/project.json"))
        if len(matches) != 1:
            print(f"Project not found or ambiguous: {args.slug}")
            return 1
        return validate_project(matches[0].parent)

    folders = sorted(p.parent for p in PROJECTS.glob("**/project.json"))
    failed = 0
    for folder in folders:
        failed += validate_project(folder) != 0

    print(f"\nDatapack projects checked: {len(folders)}")
    print(f"Failed: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
