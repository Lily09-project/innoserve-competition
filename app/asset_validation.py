"""Validate an entire private demonstration bundle before it becomes usable."""

import json
from pathlib import Path
import numpy as np
from pipeline import TrainOnlyBank, run_event, probabilities, digest

INPUT_SHAPES = {
    "temporal": (17, 20, 4),
    "content": (17, 20, 1486, 2),
    "mask": (17, 20),
    "directions": (17, 20),
    "bytes": (17, 5, 1486),
    "byte_mask": (17, 5),
}


def validate_bundle(folder):
    folder = Path(folder)
    bank = TrainOnlyBank.load(
        folder / "train_bank.npz", folder / "train_bank_manifest.json"
    )
    events = json.loads((folder / "events.json").read_text(encoding="utf-8"))
    records = [
        json.loads(line)
        for line in (folder / "judge_records_private.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    if (
        not isinstance(events, list)
        or not events
        or any(not isinstance(row, dict) for row in events + records)
    ):
        raise ValueError("Invalid private event or judge records")
    ids = [row.get("event_id") for row in events]
    rids = [row.get("event_id") for row in records]
    if any(not isinstance(key, str) or not key for key in ids + rids):
        raise ValueError("Invalid private event identity")
    if (
        len(set(ids)) != len(ids)
        or len(set(rids)) != len(rids)
        or set(ids) != set(rids)
    ):
        raise ValueError("Private event and judge IDs must be unique and match")
    if set(ids) & set(bank.ids):
        raise ValueError("Private query/train ID overlap")
    by_id = {row["event_id"]: row for row in events}
    by_record = {row["event_id"]: row for row in records}
    for event in events:
        if (
            event.get("source_split") != "test"
            or type(event.get("validation_label")) is not int
            or not 0 <= event["validation_label"] < 17
        ):
            raise ValueError("Private query split or label mismatch")
        p = probabilities(event["probabilities"])
        if not np.isclose(event.get("confidence", float("nan")), p.max(), atol=1e-6):
            raise ValueError("Private event confidence mismatch")
        result = run_event(event, bank, by_record[event["event_id"]])
        if digest(event.get("evidence")) != digest(result["evidence"]):
            raise ValueError("Private event evidence differs from actual retrieval")
    with np.load(folder / "live_inputs_private.npz", allow_pickle=False) as inputs:
        for key, shape in INPUT_SHAPES.items():
            value = inputs[key]
            if (
                value.shape != shape
                or not np.issubdtype(value.dtype, np.number)
                or not np.isfinite(value).all()
            ):
                raise ValueError("Invalid private input tensor: " + key)
        live_ids = inputs["event_ids"].tolist()
        if (
            len(live_ids) != 17
            or len(set(live_ids)) != 17
            or not set(live_ids).issubset(by_id)
        ):
            raise ValueError("Invalid private live input identity")
        if {by_id[key]["validation_label"] for key in live_ids} != set(range(17)):
            raise ValueError("Private live inputs must cover all 17 classes")
    return {
        "train_cases": len(bank.ids),
        "events": len(events),
        "live_classes": 17,
        "judge_records": len(records),
        "representation": bank.representation_id,
    }
