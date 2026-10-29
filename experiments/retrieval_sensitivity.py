"""Frozen queries and stratified subsets of the existing training bank only."""
import argparse
import json
from pathlib import Path
import numpy as np
from common import ROOT, load_data, sha
from pipeline import task_vector


def metrics(bank, events, indices, dimensions):
    vectors = bank.vectors[indices, :dimensions]
    vectors = vectors / np.linalg.norm(vectors, axis=1)[:, None]
    query = np.asarray([e['embedding'] if dimensions == 512 else task_vector(e['embedding'], e['probabilities']) for e in events])
    query = query / np.linalg.norm(query, axis=1)[:, None]
    scores = query @ vectors.T
    labels = np.asarray(bank.labels)[indices]
    ids = np.asarray(bank.ids)[indices]
    hit, rr, precision = [], [], []
    for e, row in zip(events, scores):
        order = np.lexsort((ids, -row))[:5]
        matching = labels[order] == e['validation_label']
        hit.append(bool(matching.any()))
        rr.append(1 / (int(np.flatnonzero(matching)[0]) + 1) if matching.any() else 0)
        precision.append(float(matching.mean()))
    return {'queries': len(events), 'bank_cases': len(indices), 'hit_at_5': float(np.mean(hit)),
            'mrr_at_5': float(np.mean(rr)), 'precision_at_5': float(np.mean(precision))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('sensitivity_output_exists')
    bank, events = load_data()
    if set(bank.ids).intersection(e['event_id'] for e in events):
        raise ValueError('train_query_overlap')
    trials = []
    for fraction in (.5, .75, 1.):
        for seed in range(42, 47):
            rng = np.random.default_rng(seed)
            indices = []
            for label in range(17):
                candidates = np.flatnonzero(np.asarray(bank.labels) == label)
                indices.extend(rng.choice(candidates, max(5, int(len(candidates) * fraction)), replace=False).tolist())
            indices = np.asarray(sorted(indices))
            for dim in (512, 529):
                trials.append({'fraction': fraction, 'seed': seed, 'dimensions': dim, **metrics(bank, events, indices, dim)})
    report = {'status': 'completed', 'protocol': {'seeds': list(range(42, 47)), 'fractions': [.5, .75, 1.],
              'sampling': 'Within-class without replacement; floor(fraction*n), minimum 5 per class.',
              'queries': len(events), 'bank': len(bank.ids), 'train_query_id_overlap': 0,
              'query_sha256': sha(ROOT / 'evidence/fresh17/events.json'), 'bank_sha256': sha(ROOT / 'evidence/fresh17/train_bank.npz'),
              'script_sha256': sha(Path(__file__)), 'common_sha256': sha(ROOT / 'experiments/common.py')},
              'trials': trials, 'scope': 'Training-bank subset sensitivity with frozen queries, weights and split. No new-query, cross-dataset, AI-audit or network-effectiveness claim.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('SENSITIVITY_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
