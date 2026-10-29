"""Validate recorded results and publish one data snapshot for all media builders."""
import argparse
import hashlib
import json
from pathlib import Path

from validate_results import SOURCES, read_results, validate_results

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = Path('media/film/metrics.json')


def snapshot(root=ROOT):
    root = Path(root)
    data = validate_results(read_results(root))
    d, r, j, f = (data[key] for key in SOURCES)
    gate = d['OOF Gate']
    values = {
        'detection_n': gate['n'], 'accuracy': gate['accuracy'],
        'macro_f1': {name: d[name]['macro_f1'] for name in ('PBCNN', 'CTBM', 'OOF Gate')},
        'gain_pbcnn': (gate['macro_f1']-d['PBCNN']['macro_f1'])*100,
        'gain_ctbm': (gate['macro_f1']-d['CTBM']['macro_f1'])*100,
        'bank_rows': r['bank_rows'], 'queries': r['queries'],
        'top5': r['top5'], 'mrr5': r['mrr5'], 'overlap': r['train_test_id_overlap'],
        'support': j['assessment_counts']['support'], 'review': j['assessment_counts']['review'],
        'uncertain': j['assessment_counts']['uncertain'], 'support_precision': j['support_precision'],
        'errors': j['detector_error_count'], 'intercepted': j['intercepted_error_count'],
        'false_support': j['false_support_count'], 'external_api_calls': j['external_api_calls'],
        'live_classes': f['real_live_classes'], 'network_cases': f['network_cases'],
        'rules_cases': sum(row['rules_applied'] > 0 for row in f['cases']),
        'passive_cases': f['non_disruptive_network_cases'],
        'background': f['background_preserved_cases'], 'rollback': f['rollback_passed_cases'],
    }
    return {'schema_version': 1, 'sources': {
        'results/'+name: hashlib.sha256((root/'results'/name).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
        for name in SOURCES.values()
    }, 'values': values}


def load_metrics(root=ROOT):
    expected = snapshot(root)
    path = Path(root)/SNAPSHOT
    if not path.is_file() or json.loads(path.read_text(encoding='utf-8')) != expected:
        raise ValueError('Media metrics are stale; run python scripts/media_results.py after validating results')
    return expected['values']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.check:
        load_metrics()
        print('Media results: validated snapshot matches all four result files')
    else:
        path = ROOT/SNAPSHOT
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(snapshot(), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print('Media results: rebuilt from validated recorded results')


if __name__ == '__main__':
    main()
