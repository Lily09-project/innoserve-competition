"""Explicit code and runtime-asset lineage, with no private paths in identifiers."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = (
    "app/server.py",
    "app/live_engine.py",
    "app/judge_response.py",
    "app/pipeline.py",
    "app/network_contract.py",
    "app/settings.py",
    "app/provenance.py",
    "app/asset_validation.py",
    "scripts/live_network_test.py",
    "scripts/rebuild_retrieval.py",
    "scripts/run_local_judge.py",
    "scripts/audit_selection.py",
    "scripts/audit_final_chain.py",
    "scripts/audit_alignment_assets.py",
    "scripts/preflight.py",
    "scripts/import_local_assets.py",
    "scripts/export_framework_validation.py",
    "scripts/validate_results.py",
    "scripts/release_inventory.py",
    "scripts/demo_walkthrough.py",
    "sources/paper_code/scripts/run_active_defense_shadow_experiment.py",
    "sources/paper_code/sim/active_defense_mininet_replay.py",
    "sources/paper_code/sim/mininet_traffic_endpoint.py",
)


def file_hash(path):
    path = Path(path)
    digest = hashlib.sha256()
    if path.suffix in (".py", ".json", ".csv", ".md", ".txt"):
        digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
    else:
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
                digest.update(block)
    return digest.hexdigest()


def identifier(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def code_manifest(root=ROOT):
    return {name: file_hash(Path(root) / name) for name in SOURCE_FILES}


def code_revision(root=ROOT):
    return identifier(code_manifest(root))


def runtime_assets(root=ROOT):
    from settings import asset_path, optional_asset_path, execution_settings

    root = Path(root)
    ref = asset_path("ids_reference_root")
    model = asset_path("llama_model_dir")
    files = {
        "gate/implementation": optional_asset_path(
            "gate_impl_path", ref.parent / "gate_soft_oof_search.py"
        ),
        "gate/settings": ref / "gate_results/augmented/seed_42/gate_summary.json",
        "gate/ctbm_validation": ref
        / "gate_exports/augmented/seed_42/ctbm_validation_predictions.csv",
        "gate/pbcnn_validation": ref
        / "gate_exports/augmented/seed_42/pbcnn_validation_predictions.csv",
        "runtime/ctbm": ref / "runtime_sources/ctbm_full_none_real_only_seed_42.py",
        "runtime/pbcnn": ref
        / "runtime_sources/SMOTE_校準式類別感知Gate動態融合訓練_nofilm.py",
    }
    for name in ("CTBM_Full", "PBCNN_M1", "PBCNN_M2"):
        files["checkpoint/" + name] = (
            ref / "models/augmented/seed_42" / name / "best_model.pt"
        )
    for name in (
        "train_bank.npz",
        "train_bank_manifest.json",
        "events.json",
        "live_inputs_private.npz",
    ):
        files["input/" + name] = root / "evidence/fresh17" / name
    weights = sorted(model.glob("*.safetensors"))
    if not weights:
        raise ValueError("Missing local LLM weight shards")
    for path in weights:
        files["llm/" + path.name] = path
    for name in (
        "config.json",
        "generation_config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "model.safetensors.index.json",
    ):
        path = model / name
        if (
            name in ("config.json", "tokenizer.json", "tokenizer_config.json")
            or path.exists()
        ):
            files["llm/" + name] = path
    return {
        "files": {key: file_hash(path) for key, path in sorted(files.items())},
        "execution": execution_settings(),
    }
