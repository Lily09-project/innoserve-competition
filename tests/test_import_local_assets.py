"""An interrupted import never replaces existing evidence or publishes partial data."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import import_local_assets as importer
from contract_fixtures import write_private_bundle


class ImportAssetTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='private-import-contract-')
        base=Path(self.temp.name)
        self.source=base/'source';self.root=base/'destination'
        self.origin=self.source/'evidence/fresh17';self.origin.mkdir(parents=True)
        self.root.mkdir()
        write_private_bundle(self.origin)

    def tearDown(self):self.temp.cleanup()

    def test_success_publishes_all_files_and_removes_owned_staging(self):
        target=importer.import_assets(self.source,self.root)
        for name in importer.REQUIRED:self.assertEqual((target/name).read_bytes(),(self.origin/name).read_bytes())
        self.assertEqual([p.name for p in target.parent.iterdir()],['fresh17'])

    def test_existing_import_including_empty_folder_is_never_overwritten(self):
        target=self.root/'evidence/fresh17';target.mkdir(parents=True)
        for populated in (False,True):
            if populated:(target/'keep').write_text('user evidence')
            with self.assertRaises(FileExistsError):importer.import_assets(self.source,self.root)
            if populated:self.assertEqual((target/'keep').read_text(),'user evidence')

    def test_missing_required_file_does_not_create_destination(self):
        (self.origin/importer.REQUIRED[0]).unlink()
        with self.assertRaises(FileNotFoundError):importer.import_assets(self.source,self.root)
        self.assertFalse((self.root/'evidence').exists())

    def test_nested_or_identical_workspaces_are_rejected(self):
        for source,target in ((self.root,self.root),(self.root,self.root/'child'),(self.root/'child',self.root)):
            with self.assertRaises(ValueError):importer.import_assets(source,target)

    def test_copy_failure_does_not_publish_partial_files(self):
        def interrupted(origin,stage,**kwargs):
            (stage/'partial').write_text('partial')
            raise OSError('simulated disk failure')
        with patch.object(importer.shutil,'copytree',side_effect=interrupted):
            with self.assertRaises(OSError):importer.import_assets(self.source,self.root)
        self.assertEqual(list((self.root/'evidence').iterdir()),[])
        self.assertTrue(all((self.origin/name).exists() for name in importer.REQUIRED))

    def test_publish_failure_removes_only_owned_staging(self):
        keep=self.root/'evidence/other';keep.mkdir(parents=True);(keep/'keep').write_text('preserved')
        with patch.object(importer.os,'rename',side_effect=PermissionError('simulated publish failure')):
            with self.assertRaises(PermissionError):importer.import_assets(self.source,self.root)
        self.assertEqual((keep/'keep').read_text(),'preserved')
        self.assertEqual([p.name for p in keep.parent.iterdir()],['other'])

    def test_foreign_lock_is_preserved(self):
        parent=self.root/'evidence';parent.mkdir();lock=parent/'.fresh17-import.lock';lock.write_text('another importer')
        with self.assertRaises(FileExistsError):importer.import_assets(self.source,self.root)
        self.assertEqual(lock.read_text(),'another importer')

    def test_target_link_is_rejected_before_copy(self):
        parent=self.root/'evidence'
        original=Path.is_symlink
        with patch.object(Path,'is_symlink',lambda path:path==parent or original(path)):
            with self.assertRaisesRegex(ValueError,'escapes'):importer.import_assets(self.source,self.root)
        self.assertFalse(parent.exists())

    def test_symbolic_link_is_rejected_before_copy(self):
        name=self.origin/importer.REQUIRED[0]
        original=Path.is_symlink
        with patch.object(Path,'is_symlink',lambda p:p==name or original(p)):
            with self.assertRaises(ValueError):importer.import_assets(self.source,self.root)
        self.assertFalse((self.root/'evidence').exists())

    def test_invalid_json_and_npz_never_publish(self):
        for name in ('events.json','live_inputs_private.npz'):
            original=(self.origin/name).read_bytes()
            (self.origin/name).write_bytes(b'invalid bundle')
            with self.assertRaises(ValueError):importer.import_assets(self.source,self.root)
            self.assertFalse((self.root/'evidence/fresh17').exists())
            self.assertEqual(list((self.root/'evidence').iterdir()),[])
            (self.origin/name).write_bytes(original)
