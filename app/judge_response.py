"""Decode one unambiguous JSON object; malformed output always routes to review."""

import json


def parse_judge_response(raw):
    decoder = json.JSONDecoder()
    candidates = []
    position = 0
    while position < len(raw):
        start = raw.find("{", position)
        if start < 0:
            break
        try:
            value, length = decoder.raw_decode(raw[start:])
            position = start + length
        except json.JSONDecodeError:
            position = start + 1
            continue
        if isinstance(value, dict):
            candidates.append(value)
    if len(candidates) != 1:
        raise ValueError("ambiguous_or_missing_judge_json")
    value = candidates[0]
    if (
        value.get("assessment") not in {"support", "review", "uncertain"}
        or not isinstance(value.get("reason"), str)
        or not value["reason"].strip()
    ):
        raise ValueError("invalid_judge_schema")
    return {"assessment": value["assessment"], "reason": value["reason"]}
