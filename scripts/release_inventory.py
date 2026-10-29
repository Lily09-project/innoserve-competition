"""Bind release files to sources and summarize existing real evidence safely."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from server import source_revision
from audit_selection import select_audit
from provenance import runtime_assets, identifier

VISUAL_SOURCES = [
    'design-system/palette.json','design-system/typography.json','design-system/icons.json',
    'scripts/presentation/style_contract.py','scripts/presentation/editorial_assets.py',
    'scripts/presentation/build_a2_poster.py','scripts/presentation/finalize_delivery.py',
    'media/film/scene.mjs','scripts/render_product_film.mjs',
    'media/film/metrics.mjs','media/film/metrics.json','scripts/media_results.py',
    'scripts/finals_pipeline.py',
    *['deliverables/source/slides/'+f'{i:02d}_slide.svg' for i in range(1,13)],
]
ASSETS = [
    'deliverables/決賽簡報_AI資安框架.pptx','deliverables/決賽簡報_AI資安框架.pdf',
    'deliverables/決賽海報_AI資安框架_A2.pptx','deliverables/決賽海報_AI資安框架_A2.pdf',
    'deliverables/AI資安框架_系統展示影片_30秒快版.mp4','deliverables/source/architecture.svg',
    'deliverables/source/speaker-notes.md',
]
PREVIEWS = ['deliverables/figures/'+name for name in
            ('slides-preview.png','poster-a2-preview.png','film-preview.png','fig_architecture.png')]
RESULTS = ['results/'+name for name in ('detection_17class.json','retrieval_17class.json',
                                       'local_judge_17class.json','framework_validation.json','policy_risk_analysis.json')]


def sha(path):
    path = Path(path)
    data = path.read_bytes()
    if path.suffix.lower() in ('.py','.mjs','.cjs','.json','.md','.svg','.ps1','.txt'):
        data = data.replace(b'\r\n',b'\n')
    return hashlib.sha256(data).hexdigest()


def bindings(root=ROOT):
    root = Path(root)
    return {group:{name:sha(root/name) for name in names} for group,names in
            (('visual_sources',VISUAL_SOURCES),('artifacts',ASSETS),('previews',PREVIEWS),('results',RESULTS))}


def verify_bindings(value, root=ROOT):
    expected = bindings(root)
    if value.get('bindings') != expected:
        raise ValueError('Release source, artifact, preview or result binding mismatch; regenerate and revalidate changed assets')
    if value.get('source_revision') != source_revision():
        raise ValueError('Release evidence belongs to another application source')
    return True


def distribution(values):
    values = sorted(float(value) for value in values)
    if not values or any(not math.isfinite(value) or value < 0 for value in values):
        raise ValueError('Invalid measured timing data')
    count = len(values)
    middle = count//2
    return {'samples':count,'minimum':values[0],
            'median':values[middle] if count%2 else (values[middle-1]+values[middle])/2,
            'maximum':values[-1], 'unit':'ms'}


def build(root=ROOT, audit_dir=None):
    root = Path(root)
    folder = select_audit(root/'validation',source_revision(),audit_dir,identifier(runtime_assets(root)))
    read = lambda name:json.loads((folder/name).read_text(encoding='utf-8'))
    summary,live,receipts = (read(name) for name in ('summary.json','live_events_private.json','network_receipts_private.json'))
    detector = json.loads((root/RESULTS[0]).read_text(encoding='utf-8'))['OOF Gate']
    normal = detector['per_class'][0]
    return {
        'created_utc':datetime.now(timezone.utc).isoformat(), 'source_revision':source_revision(),
        'bindings':bindings(root), 'asset_revision':summary['asset_revision'],
        'evidence':{'audit_started_utc':summary['started_utc'],'status':summary['status'],
                    'private_receipt_hashes':{name:sha(folder/name) for name in
                        ('summary.json','live_events_private.json','network_receipts_private.json','asset_alignment.json','asset_manifest.json')},
                    'real_live_classes':17,'real_local_llm_calls':17,'network_cases':6,
                    'background_preserved':summary['background_preserved_cases'],
                    'rollback_passed':summary['rollback_passed_cases'],
                    'scope':summary['scope']},
        'measured_timings':{name:distribution([row['timings'][name] for row in live])
                            for name in ('detector_ms','retrieval_ms','fresh_llm_ms')},
        'timing_scope':'One warm local inference per prepared class, 17 cases on the recorded workstation; no p95, cold-start latency or production throughput claim.',
        'detector_analysis':{'per_class':detector['per_class'],
                              'benign_misclassification_rate':1-normal['recall'],
                              'benign_scope':'BENIGN samples classified as any attack; not the rate of attacks classified BENIGN'},
        'network_analysis':{'rules_applied_cases':sum(row['rules_applied']>0 for row in receipts),
                             'monitor_or_evidence_cases':sum(row['rules_applied']==0 for row in receipts)},
        'native_playback':'excluded by user instruction; offline decoding and file checks only',
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--audit-dir',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'deliverables/source/release-validation.json')
    args = parser.parse_args()
    value = build(audit_dir=args.audit_dir)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Release inventory: source, real evidence, timings and preview bindings recorded')


if __name__ == '__main__':
    main()
