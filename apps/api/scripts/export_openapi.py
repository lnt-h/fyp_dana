import argparse
import json
from pathlib import Path

from app.main import create_app

OUTPUT = Path(__file__).resolve().parents[1] / "openapi.json"


def serialized_schema() -> str:
    return json.dumps(create_app().openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = serialized_schema()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != expected:
            print("openapi.json is stale; run: uv run python scripts/export_openapi.py")
            return 1
        return 0
    OUTPUT.write_text(expected)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
