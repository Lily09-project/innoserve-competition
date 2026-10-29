"""Fixed supplementary experiment protocol; no deployment or production mutation."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from pipeline import LABELS,TrainOnlyBank,task_vector,guard,digest

ARMS=('confidence_rule','evidence_rule529','llm_none','llm_512','llm_529')
PROMPT='''You are a network intrusion evidence auditor. The detector's formal class is immutable.
Use only the supplied detector class, confidence, branch predictions and any train-only neighbours.
Never assume ground truth. Neighbours are evidence, not authoritative labels for the query.
Return exactly one JSON object with assessment and reason. assessment is support, review or uncertain.
With neighbours present, use support when confidence is at least 0.8 and at least four neighbours agree with the detector.
With no neighbours provided, use support when confidence is at least 0.8 and both branches agree with the detector.
Use review when available evidence conflicts with the detector or the branches disagree and evidence is mixed.
Use uncertain when confidence is below 0.5 or available information is too weak to assess.
Do not output commands or change the detector label. Keep reason under 25 English words.'''


def sha(path):return hashlib.sha256(Path(path).read_bytes().replace(b'\r\n',b'\n') if Path(path).suffix in {'.py','.json','.md'} else Path(path).read_bytes()).hexdigest()


def load_data(root=ROOT):
    data=Path(root)/'evidence/fresh17'
    bank=TrainOnlyBank.load(data/'train_bank.npz',data/'train_bank_manifest.json')
    events=json.loads((data/'events.json').read_text(encoding='utf-8'))
    if len({e['event_id'] for e in events})!=len(events):raise ValueError('duplicate_query_ids')
    return bank,events


def retrieve(bank,event,dimensions=529,indices=None):
    if dimensions not in (512,529):raise ValueError('invalid_representation')
    if event['event_id'] in bank.ids:raise ValueError('query_train_overlap')
    if event['representation_id']!=bank.representation_id or event['model_sha256']!=bank.model_sha256:raise ValueError('representation_mismatch')
    indices=np.arange(len(bank.ids)) if indices is None else np.asarray(indices)
    if len(indices)<5 or len(set(indices.tolist()))!=len(indices):raise ValueError('invalid_bank_subset')
    vectors=bank.vectors[indices,:dimensions]
    vectors=vectors/np.linalg.norm(vectors,axis=1)[:,None]
    query=np.asarray(event['embedding']) if dimensions==512 else task_vector(event['embedding'],event['probabilities'])
    scores=vectors@(query/np.linalg.norm(query))
    order=sorted(range(len(indices)),key=lambda i:(-scores[i],bank.ids[indices[i]]))[:5]
    return [{'rank':rank+1,'case_id':bank.ids[indices[i]],'label_id':bank.labels[indices[i]],
             'label':LABELS[bank.labels[indices[i]]],'similarity':float(scores[i])} for rank,i in enumerate(order)]


def payload(event,evidence):
    return {'detector_class':LABELS[event['prediction']],'confidence':round(float(max(event['probabilities'])),6),
        'branch_predictions':[LABELS[event['pred_ctbm']],LABELS[event['pred_pbcnn']]],
        'train_only_neighbours':[{'rank':r['rank'],'class':r['label'],'similarity':round(r['similarity'],6)} for r in evidence]}


def rule(event,evidence=None):
    confidence=max(event['probabilities'])
    agreement=(event['pred_ctbm']==event['prediction']==event['pred_pbcnn']) if evidence is None else sum(r['label_id']==event['prediction'] for r in evidence)>=4
    return 'support' if confidence>=.8 and agreement else 'uncertain' if confidence<.5 else 'review'


def common_guard(event,assessment,production_evidence):
    policy=guard(event['prediction'],assessment)
    if assessment=='support' and (max(event['probabilities'])<.8 or sum(r['label_id']==event['prediction'] for r in production_evidence)<4):return False
    return bool(policy['allowed'] and policy['action'] not in {'monitor','capture_evidence'})


def summarize(events,assessments,production):
    wrong=[e['prediction']!=e['validation_label'] for e in events]
    support=[a=='support' for a in assessments]
    false=sum(w and s for w,s in zip(wrong,support));n=len(events);correct=n-sum(wrong)
    return {'cases':n,'detector_errors':sum(wrong),'support':sum(support),'review':assessments.count('review'),
        'uncertain':assessments.count('uncertain'),'wrong_support':false,'correct_support':sum(support)-false,
        'support_precision':(sum(support)-false)/sum(support) if any(support) else None,
        'support_coverage':sum(support)/n,'correct_not_supported_rate':sum(not w and not s for w,s in zip(wrong,support))/correct if correct else None,
        'error_interception_rate':(sum(wrong)-false)/sum(wrong) if any(wrong) else None,
        'wrong_disruptive_authorized_common_guard':sum(w and common_guard(e,a,production[e['event_id']]) for e,w,a in zip(events,wrong,assessments)),
        'classification_changed_count':0,'network_actions_executed':0}
