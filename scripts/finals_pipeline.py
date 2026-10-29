"""One entry for evidence refresh, public verification and offline delivery staging."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts/presentation')]
from check_delivery_docs import audit,delivery_digest

REFRESH_OUTPUTS=('results/framework_validation.json','results/policy_risk_analysis.json',
                 'media/film/metrics.json','deliverables/source/release-validation.json',
                 'deliverables/source/delivery-manifest.json')
STAGE_METADATA=('deliverables/source/delivery-manifest.json','deliverables/source/release-validation.json',
                'deliverables/source/finals-readiness.json','deliverables/source/recovery-validation.json',
                'deliverables/interactive/README.md')


def refresh_commands(audit_dir):
    return [[sys.executable,'scripts/'+name,*args] for name,args in (
        ('audit_alignment_assets.py',['--audit-dir',str(audit_dir)]),
        ('export_framework_validation.py',['--audit-dir',str(audit_dir)]),
        ('analyze_policy_risk.py',['--publish']),('media_results.py',[]),
        ('release_inventory.py',['--audit-dir',str(audit_dir)]))]


def execute(command,folder,index,root=ROOT):
    process=subprocess.run(command,cwd=root,capture_output=True,timeout=900)
    (folder/f'{index:02d}.log').write_bytes(process.stdout+process.stderr)
    if process.returncode:raise RuntimeError('pipeline_step_failed:'+str(index))


def refresh_manifest(root=ROOT,audit_dir=None):
    root=Path(root)
    path=root/'deliverables/source/delivery-manifest.json'
    value=json.loads(path.read_text(encoding='utf-8'))
    for name in ('results/policy_risk_analysis.json',):
        value['files'].setdefault(name,{'hash_normalization':'LF'})
    for name,entry in value['files'].items():
        content=(root/name).read_bytes()
        entry.update(bytes=len(content),sha256=delivery_digest(content,entry.get('hash_normalization')))
    framework=json.loads((root/'results/framework_validation.json').read_text(encoding='utf-8'))
    value.update(source_revision=framework['source_revision'],asset_revision=framework['asset_revision'],
        fresh_audit_started_utc=framework['started_utc'],live_audit_source='framework_audit_'+framework['started_utc'],
        fresh_audit_status='passed',fresh_live_classes=framework['real_live_classes'],
        fresh_local_llm_calls=framework['real_local_llm_calls'],fresh_network_cases=framework['network_cases'],
        fresh_background_preserved_cases=framework['background_preserved_cases'],fresh_rollback_passed_cases=framework['rollback_passed_cases'])
    value['python_tests']=unittest.TestLoader().discover(str(root/'tests')).countTestCases()
    if audit_dir is not None:
        alignment=json.loads((Path(audit_dir)/'asset_alignment.json').read_text(encoding='utf-8'))
        value['maximum_live_saved_probability_delta']=alignment['maximum_absolute_probability_difference']
        value['model_lineage_checkpoints']=alignment['checkpoint_count']
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report=audit(root)
    if report['errors']:raise ValueError('refresh_delivery_validation_failed')
    value.update(markdown_documents=report['document_count'],local_links_checked=report['local_links_checked'])
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def refresh_evidence(audit_dir,folder,root=ROOT,runner=execute):
    root=Path(root)
    if any((root/name).is_symlink() or not (root/name).resolve().is_relative_to(root.resolve()) for name in REFRESH_OUTPUTS):
        raise ValueError('unsafe_pipeline_target')
    originals={name:(root/name).read_bytes() if (root/name).exists() else None for name in REFRESH_OUTPUTS}
    before=folder/'before';before.mkdir()
    for name,content in originals.items():
        if content is not None:
            target=before/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(content)
    try:
        for i,command in enumerate(refresh_commands(audit_dir),1):runner(command,folder,i,root)
        refresh_manifest(root,audit_dir)
    except BaseException:
        for name,content in originals.items():
            target=root/name
            if not target.resolve().is_relative_to(root.resolve()):raise RuntimeError('unsafe_pipeline_restore')
            if content is None:
                if target.is_file():target.unlink()
            else:target.write_bytes(content)
        raise


def verify(folder,node='node',root=ROOT,runner=execute):
    commands=[[sys.executable,'scripts/media_results.py','--check'],
        [sys.executable,'-m','unittest','discover','-s','tests','-q'],
        [node,'tests/media-smoke.cjs'],[node,'tests/media-render-smoke.cjs'],[node,'tests/media-data.cjs'],
        [node,'tests/offline-exhibit.cjs'],
        [sys.executable,'scripts/check_delivery_docs.py'],[sys.executable,'scripts/check_public_files.py']]
    for i,command in enumerate(commands,20):runner(command,folder,i,root)


def stage_delivery(target,root=ROOT):
    """Reproduce the approved package; stop if editable sources would change."""
    root=Path(root);target=Path(target).resolve()
    if not target.is_relative_to(root.resolve()/'validation') or target.exists():
        raise ValueError('Choose a new staging directory within validation')
    target.mkdir(parents=True)
    import editorial_assets
    old_project=editorial_assets.PROJECT
    try:
        editorial_assets.PROJECT=target/'authoring'
        editorial_assets.build_pages()
    finally:editorial_assets.PROJECT=old_project
    for i in range(1,13):
        name=f'{i:02d}_slide.svg'
        if (target/'authoring/svg_output'/name).read_text(encoding='utf-8')!=(root/'deliverables/source/slides'/name).read_text(encoding='utf-8'):
            raise ValueError('Native deck rebuild required before packaging changed slide sources')
    from package_finals import ASSETS
    names=[*ASSETS,'deliverables/決賽離線展示包.zip',*STAGE_METADATA]
    sums=[]
    for name in names:
        dst=target/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/name,dst)
        sums.append(hashlib.sha256(dst.read_bytes()).hexdigest()+'  '+name)
    (target/'SHA256SUMS.txt').write_text('\n'.join(sums)+'\n',encoding='utf-8')
    return {'assets':len(names),'native_delivery':'approved byte-identical files retained',
        'source_svgs_regenerated':12,'scope':'Reproduces the verified delivery, not an automatic redesign or conversion of changed SVG into a new native deck.'}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh-evidence',action='store_true')
    parser.add_argument('--audit-dir',type=Path)
    parser.add_argument('--stage',type=Path)
    parser.add_argument('--node',default=os.environ.get('NODE_BINARY','node'))
    args=parser.parse_args(argv)
    if args.refresh_evidence and not args.audit_dir:parser.error('--refresh-evidence requires --audit-dir')
    folder=ROOT/'validation'/('finals-pipeline-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(parents=True)
    try:
        if args.refresh_evidence:refresh_evidence(args.audit_dir,folder)
        verify(folder,args.node)
        staged=stage_delivery(args.stage) if args.stage else None
        report={'status':'passed','staged':staged,'native_playback_executed':False}
        (folder/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(report,ensure_ascii=False))
        return 0
    except (OSError,ValueError,RuntimeError,ImportError,subprocess.SubprocessError):
        print('Pipeline stopped; previous evidence is restored after a refresh failure. Inspect local logs before publishing.',file=sys.stderr)
        return 1


if __name__=='__main__':raise SystemExit(main())
