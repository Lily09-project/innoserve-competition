"""Recompute policy authorization on saved real events; never deploy a rule."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from pipeline import LABELS, TrainOnlyBank, run_event, verify_ledger
from provenance import code_revision, file_hash
from validate_results import read_results,validate_results


def analyze(events, bank, records, detector):
    counts=Counter()
    groups=Counter()
    private=[]
    per_class={label:Counter() for label in LABELS}
    for event in events:
        result=run_event(event,bank,records[event['event_id']])
        if not verify_ledger(result['ledger']):raise ValueError('invalid_analysis_ledger')
        wrong=event['prediction']!=event['validation_label']
        support=result['judge']['assessment']=='support'
        disruptive=result['policy']['allowed'] and result['policy']['action'] not in {'monitor','capture_evidence'}
        counts.update(total=1,wrong=int(wrong),support=int(support),wrong_support=int(wrong and support),
                      wrong_support_disruptive_allowed=int(wrong and support and disruptive),
                      wrong_support_non_disruptive_or_blocked=int(wrong and support and not disruptive))
        row=per_class[LABELS[event['validation_label']]]
        row.update(queries=1,detector_errors=int(wrong),support=int(support),
                   wrong_support=int(wrong and support),wrong_disruptive_allowed=int(wrong and disruptive))
        if wrong and support:
            groups[(LABELS[event['validation_label']],LABELS[event['prediction']],result['policy']['action'],bool(disruptive))]+=1
            private.append({'event_id':event['event_id'],'prediction':event['prediction'],
                'validation_label':event['validation_label'],'confidence':event['confidence'],
                'policy':result['policy'],'ledger_sha256':result['ledger'][-1]['sha256']})
    weak=[]
    for label in ('Web-BruteForce','Web-XSS'):
        i=LABELS.index(label)
        confusion=detector['confusion_matrix'][i]
        weak.append({'label':label,**detector['per_class'][i],
            'largest_confusions':[{'predicted_label':LABELS[j],'count':confusion[j]} for j in
                sorted((j for j in range(17) if j!=i and confusion[j]),key=lambda j:(-confusion[j],j))[:3]],
            'saved_query_analysis':dict(per_class[label])})
    public={'schema_version':1,'analysis_mode':'saved_detection_and_judge_retrieval_and_guard_recomputed',
        'counts':dict(counts),'network_actions_executed':0,
        'wrong_support_groups':[{'validation_label':a,'prediction_label':b,'policy_action':c,
            'disruptive_allowed':d,'count':n} for (a,b,c,d),n in sorted(groups.items())],
        'weak_class_analysis':weak,
        'scope':'Policy authorization on recorded queries, not actual false blocks, new detector accuracy, native attack prevention or a new LLM experiment. Ground truth is used only for analysis.'}
    return public,private


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish',action='store_true')
    args=parser.parse_args()
    data=ROOT/'evidence/fresh17'
    bank=TrainOnlyBank.load(data/'train_bank.npz',data/'train_bank_manifest.json')
    events=json.loads((data/'events.json').read_text(encoding='utf-8'))
    rows=[json.loads(line) for line in (data/'judge_records_private.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    records={row['event_id']:row for row in rows}
    if len(records)!=len(rows) or set(records)!={e['event_id'] for e in events}:raise ValueError('analysis_event_records_mismatch')
    detector=validate_results(read_results())['detection']['OOF Gate']
    public,private=analyze(events,bank,records,detector)
    public['source_revision']=code_revision()
    public['source_hashes']={name:file_hash(data/name) for name in ('events.json','train_bank.npz','train_bank_manifest.json','judge_records_private.jsonl')}
    public['created_utc']=datetime.now(timezone.utc).isoformat()
    folder=ROOT/'validation'/('policy-risk-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(parents=True)
    (folder/'private-events.json').write_text(json.dumps(private,ensure_ascii=False,indent=2),encoding='utf-8')
    (folder/'summary.json').write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if args.publish:
        (ROOT/'results/policy_risk_analysis.json').write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(public['counts'],ensure_ascii=False))


if __name__=='__main__':main()
