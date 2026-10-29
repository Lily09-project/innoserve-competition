"""Verify the finals story, planned timing, artifact claims and offline runbook."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from media_results import load_metrics
from provenance import code_revision
from package_finals import ASSETS
from audit_final_chain import scan_delivery_anonymity

PLAN = 'deliverables/source/finals-runbook.json'
REPORT = 'deliverables/source/finals-readiness.json'
NS = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'}
BOUND_FILES = list(dict.fromkeys(ASSETS + [PLAN, 'scripts/check_finals_readiness.py',
    'scripts/package_finals.py', 'deliverables/決賽離線展示包.zip', 'README.md',
    'media/film/metrics.json', 'design-system/palette.json',
    'scripts/presentation/recolor_roundtrip.py', 'scripts/presentation/restore_alignment.py',
    'tests/offline-exhibit.cjs', 'deliverables/interactive/README.md']))


def sha(path):
    data = Path(path).read_bytes()
    if Path(path).suffix in {'.py', '.md', '.json', '.html', '.cjs'}:
        data = data.replace(b'\r\n', b'\n')
    return hashlib.sha256(data).hexdigest()


def validate_plan(plan):
    expected = list(range(1, 10))
    if plan['slides'] != 12 or plan['report_slides'] != expected or [r['slide'] for r in plan['segments']] != expected:
        raise ValueError('invalid_report_roster')
    if any(type(r['seconds']) is not int or r['seconds'] <= 0 for r in plan['segments']):
        raise ValueError('invalid_planned_duration')
    spoken = sum(r['seconds'] for r in plan['segments'] if r['mode'] == 'spoken')
    if spoken != 260 or sum(r['seconds'] for r in plan['segments']) + plan['operation_seconds'] != 300:
        raise ValueError('five_minute_plan_mismatch')
    video = plan['video']
    if video != {'slide': 2, 'seconds': 30, 'speed_factor': 2, 'audio_tracks': 0} or plan['segments'][1]['mode'] != 'video' or plan['segments'][1]['seconds'] != 30:
        raise ValueError('opening_video_plan_mismatch')
    if plan['target_seconds'] != 300 or plan['buffer_seconds'] != 60 or plan['report_limit_seconds'] != 360 or plan['operation_seconds'] != 10:
        raise ValueError('buffer_plan_mismatch')
    if [(q['question'], q['slide']) for q in plan['qa']] != [(i, 10 + (i - 1) // 2) for i in range(1, 7)]:
        raise ValueError('six_question_roster_mismatch')
    if plan['native_playback'] != 'excluded_by_user' or len(plan['human_checks']) != 3:
        raise ValueError('verification_scope_mismatch')
    return {'planned_spoken_seconds': spoken, 'planned_total_seconds': 300, 'buffer_seconds': 60,
            'timing_is_human_measured': False, 'qa_questions': 6}


def require_tokens(text, tokens, label):
    compact = lambda value: re.sub(r'[\s,，]', '', value)
    missing = [token for token in tokens if compact(token) not in compact(text)]
    if missing:
        raise ValueError('artifact_claim_mismatch:' + label + ':' + ','.join(missing))


def slide_text(archive, number):
    return ' '.join(node.text or '' for node in ET.fromstring(archive.read(f'ppt/slides/slide{number}.xml')).findall('.//a:t', NS))


def check_claims(root=ROOT):
    root = Path(root)
    metrics = load_metrics(root)
    f1 = [f'{metrics["macro_f1"][name] * 100:.2f}%' for name in ('PBCNN', 'CTBM', 'OOF Gate')]
    detector = f1 + [f'{metrics["accuracy"] * 100:.2f}%', str(metrics['detection_n'])]
    retrieval = [f'{metrics[key] * 100:.2f}%' for key in ('top5', 'mrr5')]
    judge = [str(metrics[key]) for key in ('support', 'review', 'uncertain', 'queries')]
    with zipfile.ZipFile(root / 'deliverables/決賽簡報_AI資安框架.pptx') as archive:
        require_tokens(slide_text(archive, 7), detector, 'slide7')
        require_tokens(slide_text(archive, 8), retrieval + judge + [f'{metrics["support_precision"] * 100:.2f}%'], 'slide8')
        require_tokens(slide_text(archive, 6), ['隔離', '6/6'], 'slide6-scope')
        presentation = ET.fromstring(archive.read('ppt/presentation.xml'))
        if len(presentation.findall('p:sldIdLst/p:sldId', NS)) != 12:
            raise ValueError('native_slide_count_mismatch')
        movie = archive.read('ppt/media/opening-film.mp4')
        if movie != (root / 'deliverables/AI資安框架_系統展示影片_30秒快版.mp4').read_bytes():
            raise ValueError('embedded_movie_mismatch')
        for number in range(1, 13):
            slide = ET.fromstring(archive.read(f'ppt/slides/slide{number}.xml'))
            if slide.find('p:transition', NS) is not None:
                raise ValueError('unexpected_transition')
    with zipfile.ZipFile(root / 'deliverables/決賽海報_AI資安框架_A2.pptx') as archive:
        text = slide_text(archive, 1)
        require_tokens(text, detector + retrieval + judge + ['來源限速', '非原生攻擊防禦率'], 'poster')
        if '上游清洗' in text:
            raise ValueError('unsupported_service_claim')
    require_tokens((root / 'README.md').read_text(encoding='utf-8'), detector + retrieval + judge, 'README')
    scan_delivery_anonymity(root)
    return {'native_deck_pages': 12, 'poster_pages': 1, 'embedded_movie_matches': True,
            'metric_surfaces': ['README', 'PPT7', 'PPT8', 'A2'], 'anonymity': 'passed',
            'native_playback_executed': False}


def check_bundle(root=ROOT):
    root = Path(root)
    with zipfile.ZipFile(root / 'deliverables/決賽離線展示包.zip') as archive:
        if len(archive.namelist()) != len(set(archive.namelist())) or set(archive.namelist()) != set(ASSETS) | {'使用說明.txt', 'SHA256SUMS.txt'}:
            raise ValueError('offline_bundle_inventory_mismatch')
        sums = archive.read('SHA256SUMS.txt').decode('utf-8').splitlines()
        expected = []
        for name in ASSETS:
            content = (root / name).read_bytes()
            if name.endswith(('.md', '.json', '.html')):
                content = content.replace(b'\r\n', b'\n')
            if archive.read(name) != content:
                raise ValueError('offline_bundle_stale:' + name)
            expected.append(hashlib.sha256(content).hexdigest() + '  ' + name)
        if sums != expected:
            raise ValueError('offline_bundle_digest_mismatch')
    return {'offline_assets': len(ASSETS), 'private_assets_included': False}


def audit(root=ROOT):
    root = Path(root)
    plan = json.loads((root / PLAN).read_text(encoding='utf-8'))
    return {'status': 'passed', 'source_revision': code_revision(root),
            'plan': validate_plan(plan), 'claims': check_claims(root), 'offline': check_bundle(root),
            'human_checks': plan['human_checks'], 'human_checks_verified_by_this_script': False,
            'bindings': {name: sha(root / name) for name in BOUND_FILES}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--publish-report', action='store_true')
    args = parser.parse_args()
    value = audit()
    path = ROOT / REPORT
    if args.publish_report:
        value['created_utc'] = datetime.now(timezone.utc).isoformat()
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    else:
        saved = json.loads(path.read_text(encoding='utf-8'))
        if any(saved.get(key) != val for key, val in value.items()):
            raise ValueError('readiness_report_stale')
    print('Finals readiness: claims, five-minute plan, six questions and offline bundle verified; human rehearsal excluded.')
