"""Stage and publish private assets without overwriting an existing import."""
import argparse
from pathlib import Path
import shutil
import os
import stat
import tempfile
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from asset_validation import validate_bundle
REQUIRED = ('train_bank.npz', 'train_bank_manifest.json', 'events.json',
            'live_inputs_private.npz', 'judge_records_private.jsonl')


def validate_tree(folder):
    for path in [folder, *folder.rglob('*')]:
        info = path.lstat()
        mode = info.st_mode
        reparse = getattr(info,'st_file_attributes',0) & getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0x400)
        if path.is_symlink() or reparse or not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
            raise ValueError('Private import contains a link or special file')
    for name in REQUIRED:
        if not (folder / name).is_file():
            raise FileNotFoundError('Missing required private asset: '+name)


def import_assets(source, root=ROOT):
    source, root = Path(source).resolve(), Path(root).resolve()
    if source == root or source in root.parents or root in source.parents:
        raise ValueError('Source and destination must be separate, non-nested directories')
    origin = source / 'evidence/fresh17'
    if origin.parent.is_symlink() or not origin.resolve().is_relative_to(source):
        raise ValueError('Private source escapes the selected directory')
    validate_tree(origin)
    parent = root / 'evidence'
    if parent.is_symlink() or (parent.exists() and parent.resolve() != parent.absolute()) or not parent.resolve().is_relative_to(root):
        raise ValueError('Private target escapes the selected workspace')
    target = parent / 'fresh17'
    if target.exists() or target.is_symlink():
        raise FileExistsError('Private assets already exist; no files were overwritten')
    parent.mkdir(parents=True, exist_ok=True)
    lock = parent / '.fresh17-import.lock'
    with lock.open('x') as handle:
        stage = None
        try:
            if target.exists() or target.is_symlink():
                raise FileExistsError('Private assets already exist; no files were overwritten')
            stage = Path(tempfile.mkdtemp(prefix='.fresh17-import-', dir=parent))
            shutil.copytree(origin, stage, dirs_exist_ok=True, symlinks=True)
            validate_tree(stage)
            validate_bundle(stage)
            if target.exists() or target.is_symlink():
                raise FileExistsError('Private assets already exist; no files were overwritten')
            os.rename(stage, target)
            stage = None
        finally:
            if stage is not None:
                if stage.resolve().parent != parent.resolve() or not stage.name.startswith('.fresh17-import-'):
                    raise RuntimeError('Refusing cleanup outside owned staging directory')
                shutil.rmtree(stage)
            handle.close()
            lock.unlink()
    return target


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--source",type=Path,required=True)
    args=parser.parse_args()
    import_assets(args.source)
    print("Private assets imported locally. They remain excluded by .gitignore.")


if __name__=="__main__":main()
