"""Actual offline Llama-3-8B-Instruct audit of new 17-class retrieval events."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
from settings import optional_asset_path

sys.path.insert(0, str(optional_asset_path("judge_packages_dir", ROOT / "runtime/judge_packages")))
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from pipeline import LABELS, TrainOnlyBank, digest, run_event
from judge_response import parse_judge_response

from settings import asset_path

MODEL = asset_path("llama_model_dir")
PROMPT = """You are a network intrusion evidence auditor. The detector's formal class is immutable.
Use only the provided detector prediction, confidence, branch predictions and five train-only neighbours.
Never assume ground truth. Neighbour labels are evidence, not authoritative labels for the query.
Return one JSON object with exactly assessment and reason. assessment must be support, review or uncertain.
Use support when confidence is at least 0.8 and at least four neighbours agree with the detector.
Use review when neighbours conflict with the detector or branches disagree and evidence is mixed.
Use uncertain when confidence is below 0.5 or evidence is too weak to assess.
Do not output commands, do not change the detector label. Keep reason under 25 English words.
Example format: {"assessment":"review","reason":"Evidence conflicts with the detector prediction."}"""


def dump(path, value):
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
    )


def payload_for(event):
    return {
        "detector_class": LABELS[event["prediction"]],
        "confidence": round(event["confidence"], 6),
        "branch_predictions": [LABELS[event["pred_ctbm"]], LABELS[event["pred_pbcnn"]]],
        "train_only_neighbours": [
            {"rank": e["rank"], "class": e["label"], "similarity": round(e["similarity"], 6)}
            for e in event["evidence"]
        ],
    }


def main():
    out = ROOT / "evidence/fresh17"
    events = json.loads((out / "events.json").read_text(encoding="utf-8"))
    bank = TrainOnlyBank.load(out / "train_bank.npz", out / "train_bank_manifest.json")
    prompt_hash = hashlib.sha256(PROMPT.encode()).hexdigest()
    tokenizer = AutoTokenizer.from_pretrained(str(MODEL), local_files_only=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    model = (
        AutoModelForCausalLM.from_pretrained(
            str(MODEL), torch_dtype=torch.float16, local_files_only=True, attn_implementation="sdpa"
        )
        .to("cuda")
        .eval()
    )
    print("LOCAL_JUDGE_READY", MODEL.name, len(events), flush=True)
    torch.manual_seed(42)
    output_path = out / "judge_records_private.jsonl"
    existing = {}
    if output_path.exists():
        for line in output_path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row["prompt_sha256"] != prompt_hash:
                raise RuntimeError("prompt_changed_use_new_output")
            existing[row["event_id"]] = row
    pending = [e for e in events if e["event_id"] not in existing]
    with output_path.open("a", encoding="utf-8") as f:
        for start in range(0, len(pending), 4):
            chunk = pending[start : start + 4]
            prompts = [
                tokenizer.apply_chat_template(
                    [
                        {"role": "system", "content": PROMPT},
                        {"role": "user", "content": json.dumps(payload_for(e), ensure_ascii=False)},
                    ],
                    tokenize=False,
                    add_generation_prompt=True,
                )
                for e in chunk
            ]
            tokens = tokenizer(prompts, return_tensors="pt", padding=True).to("cuda")
            torch.cuda.synchronize()
            began = time.perf_counter()
            with torch.inference_mode():
                result = model.generate(
                    **tokens,
                    max_new_tokens=112,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=[
                        tokenizer.eos_token_id,
                        tokenizer.convert_tokens_to_ids("<|eot_id|>"),
                    ],
                )
            torch.cuda.synchronize()
            batch_ms = (time.perf_counter() - began) * 1000
            texts = tokenizer.batch_decode(
                result[:, tokens.input_ids.shape[1] :], skip_special_tokens=True
            )
            for event, text in zip(chunk, texts):
                valid = False
                try:
                    value = parse_judge_response(text)
                    valid = True
                except Exception:
                    value = {
                        "assessment": "uncertain",
                        "reason": "Local model returned an invalid structured response; manual review required.",
                    }
                record = {
                    "event_id": event["event_id"],
                    "input_sha256": digest(
                        {
                            "event_id": event["event_id"],
                            "prediction": event["prediction"],
                            "evidence": event["evidence"],
                        }
                    ),
                    "assessment": value["assessment"],
                    "reason": value["reason"],
                    "model": "Meta-Llama-3-8B-Instruct",
                    "model_revision": MODEL.name,
                    "prompt_sha256": prompt_hash,
                    "store": False,
                    "classification_changed": False,
                    "mode": "fresh_local_llm_inference",
                    "raw_response": text,
                    "valid_json": valid,
                    "batch_ms": batch_ms,
                    "batch_size": len(chunk),
                    "payload": payload_for(event),
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                f.flush()
                existing[event["event_id"]] = record
            print("JUDGE", len(existing), "/", len(events), flush=True)
    for event in events:
        record = existing[event["event_id"]]
        event["result"] = run_event(
            event, bank, {**record, "execution_mode": "fresh_local_llm_saved_replay"}
        )
    dump(out / "events.json", events)
    wrong = [e for e in events if e["prediction"] != e["validation_label"]]
    supported = [e for e in events if existing[e["event_id"]]["assessment"] == "support"]
    intercepted = sum(existing[e["event_id"]]["assessment"] != "support" for e in wrong)
    false_pass = sum(e["prediction"] != e["validation_label"] for e in supported)
    summary = {
        "mode": "fresh_local_llm_inference",
        "model": "Meta-Llama-3-8B-Instruct",
        "model_revision": MODEL.name,
        "cases": len(events),
        "prompt_sha256": prompt_hash,
        "assessment_counts": dict(Counter(existing[e["event_id"]]["assessment"] for e in events)),
        "valid_json_count": sum(existing[e["event_id"]]["valid_json"] for e in events),
        "detector_error_count": len(wrong),
        "intercepted_error_count": intercepted,
        "error_interception_rate": intercepted / len(wrong) if wrong else None,
        "false_support_count": false_pass,
        "support_count": len(supported),
        "support_precision": 1 - false_pass / len(supported) if supported else None,
        "classification_changed_count": 0,
        "ground_truth_in_payload": False,
        "external_api_calls": 0,
        "scope": "new 463-query 17-class evidence audit; distinct from historical Fine-11 FE-Net LLM experiment",
        "system_prompt": PROMPT,
    }
    dump(out / "judge_summary.json", summary)
    print(
        json.dumps({k: v for k, v in summary.items() if k != "system_prompt"}, ensure_ascii=False),
        flush=True,
    )


if __name__ == "__main__":
    main()
