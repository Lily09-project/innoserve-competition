"""Import the required private assets without overwriting existing files."""

import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "train_bank.npz",
    "train_bank_manifest.json",
    "events.json",
    "live_inputs_private.npz",
    "judge_records_private.jsonl",
)


def import_assets(source, destination=ROOT):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if source == destination or source in destination.parents or destination in source.parents:
        raise ValueError("Source and destination must be separate directories")
    origin = source / "evidence/fresh17"
    for name in REQUIRED:
        if not (origin / name).is_file():
            raise FileNotFoundError("Missing required private asset: " + name)
    target = destination / "evidence/fresh17"
    if target.exists():
        raise FileExistsError("Private asset destination exists; no files were overwritten")
    web = destination / "web/data.js"
    payload = source / "web/data.js"
    if payload.exists() and web.exists():
        raise FileExistsError("Web payload exists; no files were overwritten")
    target.mkdir(parents=True)
    for name in REQUIRED:
        shutil.copy2(origin / name, target / name)
    if payload.is_file():
        web.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(payload, web)
    return target


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    import_assets(args.source)
    print("Private assets imported locally. They remain excluded by .gitignore.")


if __name__ == "__main__":
    main()
