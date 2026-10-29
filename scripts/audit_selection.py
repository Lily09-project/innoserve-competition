"""Choose complete, passed integration evidence bound to the current source."""
import json
from pathlib import Path

REQUIRED = ('summary.json', 'live_events_private.json', 'network_receipts_private.json')


def validate_audit(folder, expected_revision):
    folder = Path(folder)
    for name in REQUIRED:
        if not (folder / name).is_file():
            raise ValueError('Incomplete audit: '+name)
    summary = json.loads((folder / 'summary.json').read_text(encoding='utf-8'))
    if not isinstance(summary, dict) or summary.get('status') != 'passed':
        raise ValueError('Audit did not pass')
    if summary.get('source_revision') != expected_revision:
        raise ValueError('Audit source differs from current application')
    live = json.loads((folder / 'live_events_private.json').read_text(encoding='utf-8'))
    network = json.loads((folder / 'network_receipts_private.json').read_text(encoding='utf-8'))
    if not isinstance(live, list) or len(live) != 17 or not isinstance(network, list) or len(network) != 6:
        raise ValueError('Audit case coverage is incomplete')
    if any(not isinstance(row, dict) for row in live+network):
        raise ValueError('Invalid audit record')
    if any(type(row.get('validation_label')) is not int or not isinstance(row.get('event_id'),str)
           or not row['event_id'] or not isinstance(row.get('execution_id'),str) or not row['execution_id'] for row in live):
        raise ValueError('Audit live record identity is invalid')
    if {row.get('validation_label') for row in live} != set(range(17)) or len({row.get('event_id') for row in live}) != 17:
        raise ValueError('Audit live labels or event IDs are incomplete')
    if any(row.get('execution_mode') != 'live_local_models' for row in live):
        raise ValueError('Audit contains saved replay instead of live inference')
    if summary.get('real_live_classes') != 17 or summary.get('network_cases') != 6:
        raise ValueError('Audit summary coverage mismatch')
    by_id = {row['event_id']:row for row in live}
    expected = {row['event_id'] for row in live if row['validation_label'] in (0,1,2,7,11,13)}
    if any(not isinstance(row.get('event_id'),str) for row in network) or {row.get('event_id') for row in network} != expected:
        raise ValueError('Audit network coverage mismatch')
    if any(row.get('execution_id') != by_id[row['event_id']]['execution_id'] for row in network):
        raise ValueError('Audit network receipt belongs to another execution')
    return folder


def select_audit(validation, expected_revision, explicit=None):
    if explicit is not None:
        return validate_audit(explicit, expected_revision)
    for folder in sorted(Path(validation).glob('framework_audit_*'), reverse=True):
        try:
            return validate_audit(folder, expected_revision)
        except (ValueError, OSError, TypeError):
            continue
    raise ValueError('No complete passed audit matches current application; run audit_final_chain.py')
