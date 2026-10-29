"""Decode a single local auditor response without truncating quoted braces."""
import json


def parse_judge_response(raw):
    if not isinstance(raw, str):
        raise ValueError('judge_response_must_be_text')
    decoder = json.JSONDecoder()
    candidates = []
    offset = 0
    while offset < len(raw):
        start = raw.find('{', offset)
        if start < 0:
            break
        try:
            value, consumed = decoder.raw_decode(raw[start:])
        except json.JSONDecodeError:
            offset = start+1
            continue
        candidates.append(value)
        offset = start+consumed
    if len(candidates) != 1:
        raise ValueError('judge_requires_one_json_object')
    value = candidates[0]
    if set(value) != {'assessment', 'reason'}:
        raise ValueError('judge_schema_mismatch')
    if not isinstance(value['assessment'], str) or value['assessment'] not in {'support', 'review', 'uncertain'}:
        raise ValueError('invalid_judge_assessment')
    if not isinstance(value['reason'], str) or not value['reason'].strip():
        raise ValueError('invalid_judge_reason')
    return value


JUDGE_PROMPT = 'You are a network intrusion evidence auditor. The detector\'s formal class is immutable.\nUse only the provided detector prediction, confidence, branch predictions and five train-only neighbours.\nNever assume ground truth. Neighbour labels are evidence, not authoritative labels for the query.\nReturn one JSON object with exactly assessment and reason. assessment must be support, review or uncertain.\nUse support when confidence is at least 0.8 and at least four neighbours agree with the detector.\nUse review when neighbours conflict with the detector or branches disagree and evidence is mixed.\nUse uncertain when confidence is below 0.5 or evidence is too weak to assess.\nDo not output commands, do not change the detector label. Keep reason under 25 English words.\nExample format: {"assessment":"review","reason":"Evidence conflicts with the detector prediction."}'
