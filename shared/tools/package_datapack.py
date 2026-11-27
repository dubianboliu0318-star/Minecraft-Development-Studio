import argparse
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECTS = ROOT / "projects" / "datapacks"


def package_project(slug):
    matches = list(PROJECTS.glob(f"**/{slug}/project.json"))
    if len(matches) != 1:
        raise SystemExit(f"Project not found or ambiguous: {slug}")

    folder = matches[0].parent
    metadata = folder / "pack.mcmeta"
    data_dir = folder / "data"

    if not metadata.is_file() or not data_dir.is_dir():
        raise SystemExit(
            "Packaging blocked: pack.mcmeta and data/ must exist."
        )

    check = subprocess.run(
        [sys.executable, str(ROOT / "shared/tools/validate_datapack.py"),
         "--slug", slug],
        cwd=ROOT
    )
    if check.returncode != 0:
        raise SystemExit("Packaging blocked: Datapack validation failed.")

    files = sorted(
        p for p in folder.rglob("*")
        if p.is_file() and (p == metadata or p == folder / "pack.png" or data_dir in p.parents)
    )
    if not any(data_dir in p.parents for p in files):
        raise SystemExit("Packaging blocked: data/ contains no files.")

    dist = folder / "dist"
    dist.mkdir(exist_ok=True)
    output = dist / f"{slug}.zip"

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in files:
            archive.write(file, file.relative_to(folder))

    with zipfile.ZipFile(output, "r") as archive:
        bad = archive.testzip()
        if bad:
            output.unlink(missing_ok=True)
            raise SystemExit(f"ZIP integrity check failed: {bad}")

        names = set(archive.namelist())
        if "pack.mcmeta" not in names or not any(
            name.startswith("data/") for name in names
        ):
            output.unlink(missing_ok=True)
            raise SystemExit("ZIP structure verification failed.")

    print(f"PACKAGE CREATED: {output.relative_to(ROOT)}")
    print(f"Files included: {len(files)}")
    return output


def main():
    parser = argparse.ArgumentParser(description="MDS Datapack Packager")
    parser.add_argument("--slug", required=True)
    args = parser.parse_args()
    package_project(args.slug)


if __name__ == "__main__":
    main()
