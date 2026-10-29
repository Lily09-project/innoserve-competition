"""Check first-party Markdown links, delivery hashes and actual MP4 timing."""
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def delivery_digest(content, normalization=None):
    if normalization not in (None,'LF'):
        raise ValueError('Unsupported delivery hash normalization')
    if normalization == 'LF':
        content = content.replace(b'\r\n',b'\n')
    return hashlib.sha256(content).hexdigest()


def mp4_duration(path):
    data = Path(path).read_bytes()

    def boxes(start, end):
        while start + 8 <= end:
            size, kind = struct.unpack_from('>I4s', data, start)
            header = 8
            if size == 1:
                size = struct.unpack_from('>Q', data, start + 8)[0]
                header = 16
            elif size == 0:
                size = end - start
            if size < header or start + size > end:
                raise ValueError('Invalid MP4 atom')
            yield kind, start + header, start + size
            start += size

    for kind, start, end in boxes(0, len(data)):
        if kind == b'moov':
            for child, payload, _ in boxes(start, end):
                if child == b'mvhd':
                    if data[payload] == 1:
                        scale = struct.unpack_from('>I', data, payload + 20)[0]
                        ticks = struct.unpack_from('>Q', data, payload + 24)[0]
                    else:
                        scale, ticks = struct.unpack_from('>II', data, payload + 12)
                    return ticks / scale
    raise ValueError('Missing MP4 movie timing')


def audit(root=ROOT):
    root = Path(root)
    listed = subprocess.check_output(
        ['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=root
    ).decode('utf-8').split('\0')
    docs = sorted({name for name in listed if name.endswith('.md') and not name.startswith('sources/') and (root / name).is_file()})
    errors, links = [], 0
    for name in docs:
        text = (root / name).read_text(encoding='utf-8')
        for target in re.findall(r'!?\[[^\]]*\]\(([^\n)]+)\)', text):
            target = target.strip().strip('<>')
            if re.match(r'^[a-z]+://|^mailto:|^#', target):
                continue
            local = unquote(target.split('#', 1)[0])
            if local and not (root / name).parent.joinpath(local).exists():
                errors.append(f'{name}: missing link {local}')
            links += 1
        if re.search(r'_40秒快版\.mp4|_60秒\.mp4', text):
            errors.append(f'{name}: superseded film filename')
        if 'lily09-project.github.io/innoserve-competition' in text:
            errors.append(f'{name}: retired website URL')
    manifest = json.loads((root / 'deliverables/source/delivery-manifest.json').read_text(encoding='utf-8'))
    for name, entry in manifest['files'].items():
        path = root / name
        if not path.is_file() or delivery_digest(path.read_bytes(),entry.get('hash_normalization')) != entry['sha256']:
            errors.append(f'{name}: delivery digest mismatch')
    from release_inventory import verify_bindings
    try:
        verify_bindings(json.loads((root/'deliverables/source/release-validation.json').read_text(encoding='utf-8')),root)
    except (ValueError,OSError):
        errors.append('Release source/artifact/preview evidence binding mismatch')
    recovery_path=root/'deliverables/source/recovery-validation.json'
    supplementary_path=root/'results/supplementary_validation.json'
    if supplementary_path.exists():
        try:
            import sys
            sys.path.insert(0,str(root/'experiments'))
            from export_results import verify as verify_supplementary
            verify_supplementary(root)
        except (ValueError,OSError,KeyError,TypeError):
            errors.append('Supplementary experiment evidence differs from current sources or counts')
    if recovery_path.exists():
        try:
            recovery=json.loads(recovery_path.read_text(encoding='utf-8'))
            release=json.loads((root/'deliverables/source/release-validation.json').read_text(encoding='utf-8'))
            probe=root/'scripts/network_fault_probe.py'
            if recovery['status']!='passed' or recovery['source_revision']!=release['source_revision'] or recovery['probe_script_sha256']!=delivery_digest(probe.read_bytes(),'LF') or recovery['owned_links_remaining']!=[] or any(recovery.get(k) is not True for k in ('deadline_cleanup','signal_cleanup','concurrent_rejected','retry_with_rules_and_expiry')):
                raise ValueError('invalid_recovery_binding')
        except (ValueError,OSError,KeyError,TypeError):
            errors.append('Recovery proof differs from current sources or cleanup did not pass')
    films = list((root / 'deliverables').rglob('*.mp4'))
    if len(films) != 1:
        errors.append('Exactly one current presentation film must be delivered')
    measured = {}
    for path in films:
        seconds = mp4_duration(path)
        measured[path.relative_to(root).as_posix()] = seconds
        if seconds > 40 or abs(seconds - 30) > 1 / 24:
            errors.append(f'{path.name}: invalid duration {seconds}')
    return {'documents': docs, 'document_count': len(docs), 'local_links_checked': links, 'video_seconds': measured, 'errors': errors}


if __name__ == '__main__':
    result = audit()
    print(json.dumps(result, ensure_ascii=True, indent=2))
    raise SystemExit(bool(result['errors']))
