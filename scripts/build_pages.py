"""Build a public-only static site from deterministic synthetic fixtures."""

import argparse
import json
from pathlib import Path
import shutil
import tempfile
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "app"), str(ROOT / "scripts")]
from make_demo_assets import make_demo_assets
from pipeline import task_vector


def build_pages(output):
    output = Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Pages destination must be empty")
    with tempfile.TemporaryDirectory(prefix="innoserve-pages-") as temporary:
        demo = make_demo_assets(Path(temporary) / "synthetic")
        shutil.copytree(demo / "web", output, dirs_exist_ok=True)
        data_file = output / "data.js"
        text = data_file.read_text(encoding="utf-8")
        data = json.loads(text[len("window.FINAL_DATA=") :].strip().removesuffix(";"))
        data["summary"]["static_site"] = True
        private = json.loads((demo / "evidence/fresh17/events.json").read_text(encoding="utf-8"))
        with np.load(demo / "evidence/fresh17/train_bank.npz", allow_pickle=False) as bank:
            cases = [
                {"id": str(key), "vector": vector.tolist()}
                for key, vector in zip(bank["ids"], bank["vectors"], strict=True)
            ]
        fixtures = {
            "cases": cases,
            "queries": {
                event["event_id"]: task_vector(event["embedding"], event["probabilities"]).tolist()
                for event in private
            },
            "exports": {
                event["event_id"]: json.dumps(event, ensure_ascii=False, allow_nan=False)
                for event in data["events"]
            },
        }
        data_file.write_text(
            "window.FINAL_DATA="
            + json.dumps(data, ensure_ascii=False, allow_nan=False)
            + ";\nwindow.STATIC_FIXTURES="
            + json.dumps(fixtures, ensure_ascii=False, allow_nan=False)
            + ";\n",
            encoding="utf-8",
        )
        (output / ".nojekyll").write_text("", encoding="utf-8")
        (output / "site-manifest.json").write_text(
            json.dumps(
                {
                    "synthetic": True,
                    "static_site": True,
                    "classes": 17,
                    "events": 17,
                    "cases": 85,
                    "video_seconds": 45,
                }
            ),
            encoding="utf-8",
        )
    assert not (output / "evidence").exists()
    print("Built synthetic-only Pages site:", output)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    build_pages(parser.parse_args().output)
