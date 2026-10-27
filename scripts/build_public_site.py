"""Publish verified aggregate results only; no event fixtures or private assets."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "detection": "detection_17class.json",
    "retrieval": "retrieval_17class.json",
    "judge": "local_judge_17class.json",
    "framework": "framework_validation.json",
}


def read_results(root=ROOT):
    return {
        key: json.loads((root / "results" / name).read_text(encoding="utf-8"))
        for key, name in SOURCES.items()
    }


def validate_results(data):
    detection, retrieval, judge, framework = (data[key] for key in SOURCES)
    expected_labels = [row["label"] for row in detection["OOF Gate"]["per_class"]]
    if len(set(expected_labels)) != 17:
        raise ValueError("Expected 17 unique labels")

    def close(actual, expected):
        if not math.isclose(actual, expected, abs_tol=1e-10):
            raise ValueError("Aggregate metric does not match recorded counts")

    for model in ("CTBM", "PBCNN", "OOF Gate"):
        value = detection[model]
        matrix = value["confusion_matrix"]
        rows = value["per_class"]
        if len(matrix) != 17 or any(
            len(row) != 17 or any(type(n) is not int or n < 0 for n in row)
            for row in matrix
        ):
            raise ValueError("Invalid confusion matrix")
        total = sum(sum(row) for row in matrix)
        if value["n"] != total or [row["label"] for row in rows] != expected_labels:
            raise ValueError("Detection sample or label mismatch")
        close(value["accuracy"], sum(matrix[i][i] for i in range(17)) / total)
        scores = []
        for i, row in enumerate(rows):
            tp = matrix[i][i]
            support = sum(matrix[i])
            predicted = sum(matrix[j][i] for j in range(17))
            if row["support"] != support:
                raise ValueError("Class support mismatch")
            precision = tp / predicted if predicted else 0
            recall = tp / support if support else 0
            f1 = (
                2 * precision * recall / (precision + recall)
                if precision + recall
                else 0
            )
            close(row["precision"], precision)
            close(row["recall"], recall)
            close(row["f1"], f1)
            scores.append(f1)
        close(value["macro_f1"], sum(scores) / 17)
    if (
        sum(retrieval["query_class_counts"].values()) != retrieval["queries"]
        or sum(retrieval["train_class_counts"].values()) != retrieval["bank_rows"]
    ):
        raise ValueError("Retrieval counts mismatch")
    if (
        retrieval["label_count"] != 17
        or retrieval["train_test_id_overlap"] != 0
        or not 0 <= retrieval["mrr5"] <= retrieval["top5"] <= 1
    ):
        raise ValueError("Invalid retrieval scope")
    if (
        judge["cases"] != retrieval["queries"]
        or sum(judge["assessment_counts"].values()) != judge["cases"]
    ):
        raise ValueError("Judge count mismatch")
    if (
        judge["intercepted_error_count"] + judge["false_support_count"]
        != judge["detector_error_count"]
        or judge["support_count"] != judge["assessment_counts"]["support"]
    ):
        raise ValueError("Judge error counts mismatch")
    close(
        judge["error_interception_rate"],
        judge["intercepted_error_count"] / judge["detector_error_count"],
    )
    close(
        judge["support_precision"],
        (judge["support_count"] - judge["false_support_count"])
        / judge["support_count"],
    )
    cases = framework["cases"]
    if (
        len(cases) != framework["network_cases"]
        or framework["real_live_classes"] != 17
        or framework["real_local_llm_calls"] != 17
    ):
        raise ValueError("Framework count mismatch")
    if (
        sum(bool(row["rollback_integrity"]) for row in cases)
        != framework["rollback_passed_cases"]
        or sum(row["background_success_rate"] == 1 for row in cases)
        != framework["background_preserved_cases"]
    ):
        raise ValueError("Framework success counts mismatch")
    if (
        sum(row["rules_applied"] == 0 for row in cases)
        != framework["non_disruptive_network_cases"]
    ):
        raise ValueError("Framework deployment count mismatch")
    for row in cases:
        if (
            row["rules_applied"] > 0
            and not 30 <= row["ttl_rollback_elapsed_seconds"] < 35
        ):
            raise ValueError("Invalid expiry evidence")
    return data


def build_public_site(output, root=ROOT):
    root, output = Path(root).resolve(), Path(output).resolve()
    if (
        output == root
        or output in root.parents
        or (output.exists() and any(output.iterdir()))
    ):
        raise FileExistsError("Choose a separate empty publication directory")
    data = validate_results(read_results(root))
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    shutil.copytree(root / "public", output, dirs_exist_ok=True)
    index = output / "index.html"
    page = index.read_text(encoding="utf-8")
    for asset in ("styles.css", "site.js", "results-data.js"):
        page = page.replace(
            '"' + asset + '"', '"' + asset + "?v=" + revision[:12] + '"'
        )
    index.write_text(page, encoding="utf-8")
    (output / "results").mkdir()
    hashes = {}
    for name in SOURCES.values():
        source = root / "results" / name
        shutil.copy2(source, output / "results" / name)
        hashes["results/" + name] = hashlib.sha256(source.read_bytes()).hexdigest()
    (output / "results-data.js").write_text(
        "window.VERIFIED_RESULTS="
        + json.dumps(
            {**data, "revision": revision}, ensure_ascii=False, allow_nan=False
        )
        + ";\n",
        encoding="utf-8",
    )
    (output / "figures").mkdir()
    shutil.copy2(
        root / "deliverables/figures/fig_architecture.png",
        output / "figures/fig_architecture.png",
    )
    (output / "film").mkdir()
    for name in ("index.html", "player.mjs", "scene.mjs"):
        shutil.copy2(root / "web/film" / name, output / "film" / name)
    film = output / "film/index.html"
    film.write_text(
        film.read_text(encoding="utf-8")
        .replace("← 回事件工作台", "← 回成果首頁")
        .replace("</head>", '<link rel="stylesheet" href="../film-chrome.css"></head>'),
        encoding="utf-8",
    )
    film.write_text(
        film.read_text(encoding="utf-8")
        .replace('src="player.mjs"', 'src="player.mjs?v=' + revision[:12] + '"')
        .replace("../film-chrome.css", "../film-chrome.css?v=" + revision[:12]),
        encoding="utf-8",
    )
    player = output / "film/player.mjs"
    player.write_text(
        player.read_text(encoding="utf-8").replace(
            "'./scene.mjs'", "'./scene.mjs?v=" + revision[:12] + "'"
        ),
        encoding="utf-8",
    )
    (output / "deliverables").mkdir()
    for source, destination in (
        ("決賽簡報_AI資安框架.pptx", "finals-deck.pptx"),
        ("AI資安框架_系統展示影片_40秒快版.mp4", "method-film-40s.mp4"),
    ):
        shutil.copy2(
            root / "deliverables" / source, output / "deliverables" / destination
        )
    manifest = {
        "revision": revision,
        "data_type": "recorded_experiment_aggregates",
        "theme": "console-chrome",
        "source_files_sha256": hashes,
        "detection_samples": data["detection"]["OOF Gate"]["n"],
        "retrieval_queries": data["retrieval"]["queries"],
        "network_cases": data["framework"]["network_cases"],
        "scope": "Recorded results only; model inference and network execution run locally",
    }
    (output / "publication-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output / ".nojekyll").write_text("", encoding="utf-8")
    forbidden = ("data.js", "config.local.json", "events.json", "train_bank.npz")
    for file in output.rglob("*"):
        if file.is_file() and file.name in forbidden:
            raise ValueError("Private or event fixture payload in publication")
    print("Verified public results site:", output)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    build_public_site(parser.parse_args().output)
