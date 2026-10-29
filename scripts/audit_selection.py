"""Choose complete, passed integration evidence bound to the current source."""
import json
import hashlib
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from network_contract import build_network_scenario, verify_network_receipt, validate_measurement, valid_ledger
from pipeline import LABELS, probabilities, digest, guard, audit_payload, judge_context_digest
from judge_response import JUDGE_PROMPT
from provenance import identifier

REQUIRED = ('summary.json', 'live_events_private.json', 'network_receipts_private.json')


def validate_audit(folder, expected_revision, expected_assets=None):
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
    for event in live:
        result=event['result']
        ledger=result['ledger']
        if not valid_ledger(ledger) or len(ledger)!=4 or [row['stage'] for row in ledger]!=['detection','retrieval','judge','policy']:
            raise ValueError('Audit live ledger is invalid')
        if any(row['event_id']!=event['event_id'] for row in ledger) or ledger[0].get('execution_id')!=event['execution_id'] or result['event_id']!=event['event_id']:
            raise ValueError('Audit live event binding mismatch')
        p=probabilities(event['probabilities'])
        if int(p.argmax())!=event['prediction'] or ledger[0]['prediction']!=event['prediction'] or result['prediction']!=event['prediction']:
            raise ValueError('Audit prediction binding mismatch')
        for key,index in (('judge',2),('policy',3)):
            payload={k:v for k,v in ledger[index].items() if k not in {'stage','event_id','sequence','previous_sha256','sha256'}}
            if payload!=result[key]:raise ValueError('Audit decision ledger mismatch')
        if result['judge'].get('valid_json') is not True or result['judge'].get('mode')!='live_local_llm_inference':
            raise ValueError('Audit does not contain a valid live judge decision')
        judge=result['judge']
        prompt=hashlib.sha256(JUDGE_PROMPT.encode()).hexdigest()
        if judge.get('prompt_sha256')!=prompt or judge.get('model_revision')!=event.get('judge_model_revision') or judge.get('context_sha256')!=judge_context_digest(event['event_id'],audit_payload(event,event['evidence']),prompt,event.get('judge_model_revision')):
            raise ValueError('Audit judge context version mismatch')
        if ledger[0].get('mode')!='live_checkpoint_inference' or ledger[1].get('mode')!='live_vector_retrieval' or ledger[1].get('count')!=5 or len(event['evidence'])!=5:
            raise ValueError('Audit live model stage mismatch')
        if digest(event['evidence'])!=digest(result['evidence']) or result['judge']['input_sha256']!=digest({'event_id':event['event_id'],'prediction':event['prediction'],'evidence':event['evidence']}):
            raise ValueError('Audit evidence binding mismatch')
        actual=result['policy']
        expected_policy=guard(event['prediction'],result['judge']['assessment'],ttl=event.get('policy_ttl_seconds',300))
        if actual['allowed'] and (not expected_policy['allowed'] or actual['action']!=expected_policy['action']):
            raise ValueError('Audit policy disagrees with Guard')
        if actual['allowed'] and actual['action'] not in {'monitor','capture_evidence'} and (p.max()<.8 or sum(row['label_id']==event['prediction'] for row in event['evidence'])<4):
            raise ValueError('Audit policy bypasses evidence threshold')
    asset=summary.get('asset_revision')
    manifest=json.loads((folder/'asset_manifest.json').read_text(encoding='utf-8'))
    if asset!=identifier(manifest) or (expected_assets is not None and asset!=expected_assets) or any(event.get('asset_revision')!=asset for event in live):
        raise ValueError('Audit model asset version mismatch')
    for receipt in network:
        scenario=build_network_scenario(by_id[receipt['event_id']])
        if not verify_network_receipt(scenario,receipt):raise ValueError('Audit network hash or decision chain mismatch')
        validate_measurement(scenario,receipt)
    expected_labels=[LABELS[index] for index in (0,1,2,7,11,13)]
    if summary.get('network_validation_labels')!=expected_labels:
        raise ValueError('Audit validation label mapping mismatch')
    if summary.get('real_local_llm_calls')!=17 or summary.get('background_preserved_cases')!=6 or summary.get('rollback_passed_cases')!=6 or summary.get('non_disruptive_network_cases')!=sum(row['rules_applied']==0 for row in network):
        raise ValueError('Audit summary disagrees with verified receipts')
    return folder


def select_audit(validation, expected_revision, explicit=None, expected_assets=None):
    if explicit is not None:
        return validate_audit(explicit, expected_revision, expected_assets)
    for folder in sorted(Path(validation).glob('framework_audit_*'), reverse=True):
        try:
            return validate_audit(folder, expected_revision, expected_assets)
        except (ValueError, OSError, TypeError, KeyError, IndexError):
            continue
    raise ValueError('No complete passed audit matches current application; run audit_final_chain.py')
