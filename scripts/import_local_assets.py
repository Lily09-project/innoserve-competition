"""Import private local delivery assets into Git-ignored paths."""
import argparse
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--source",type=Path,required=True)
    args=parser.parse_args();source=args.source.resolve()
    if source==ROOT:raise ValueError("Source must differ from destination")
    for name in ["train_bank.npz","train_bank_manifest.json","events.json","live_inputs_private.npz","judge_records_private.jsonl"]:
        if not (source / "evidence/fresh17" / name).is_file():raise FileNotFoundError("Missing required private asset: "+name)
    target=ROOT / "evidence/fresh17"
    if target.exists() and any(target.iterdir()):raise FileExistsError("Private assets already exist; no files were overwritten")
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(source / "evidence/fresh17",target,dirs_exist_ok=True)
    print("Private assets imported locally. They remain excluded by .gitignore.")


if __name__=="__main__":main()
