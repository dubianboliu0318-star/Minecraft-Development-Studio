import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
errors = []
checked = 0

print("=== MDS PROJECT VALIDATOR ===")

for path in ROOT.rglob("*.json"):
    if ".git" in path.parts:
        continue
    try:
        with path.open(encoding="utf-8") as f:
            json.load(f)
        checked += 1
        print(f"[OK] JSON: {path.relative_to(ROOT)}")
    except Exception as e:
        errors.append(f"{path.relative_to(ROOT)}: {e}")
        print(f"[ERROR] JSON: {path.relative_to(ROOT)}")

print(f"\nJSON checked: {checked}")

if errors:
    print("\nVALIDATION FAILED")
    for error in errors:
        print(error)
    sys.exit(1)

print("VALIDATION PASSED")
