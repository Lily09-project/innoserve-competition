"""Canonical event hashing shared by the pipeline and network contracts."""

import hashlib
import json


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def verify_ledger(ledger):
    if not isinstance(ledger, list) or not ledger:
        return False
    previous = "0" * 64
    for index, entry in enumerate(ledger):
        if not isinstance(entry, dict):
            return False
        value = {key: val for key, val in entry.items() if key != "sha256"}
        try:
            if (
                value.get("sequence") != index
                or value.get("previous_sha256") != previous
                or digest(value) != entry.get("sha256")
            ):
                return False
        except (TypeError, ValueError):
            return False
        previous = entry["sha256"]
    return True
