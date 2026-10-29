"""Newer incomplete, replayed or stale evidence cannot become release evidence."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_selection import select_audit, validate_audit


class AuditSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='audit-selection-contract-')
        self.root=Path(self.temp.name)
        self.live=[{'event_id':str(i),'execution_id':'run-'+str(i),'validation_label':i,'execution_mode':'live_local_models'} for i in range(17)]
        self.network=[{'event_id':str(i),'execution_id':'run-'+str(i)} for i in (0,1,2,7,11,13)]

    def tearDown(self):self.temp.cleanup()

    def make(self,name,revision='current',status='passed',live=None,network=None):
        folder=self.root/('framework_audit_'+name);folder.mkdir()
        for file,value in [('summary.json',{'status':status,'source_revision':revision,'real_live_classes':17,'network_cases':6}),('live_events_private.json',self.live if live is None else live),('network_receipts_private.json',self.network if network is None else network)]:
            (folder/file).write_text(json.dumps(value),encoding='utf-8')
        return folder

    def test_skips_newer_failed_incomplete_stale_and_malformed(self):
        valid=self.make('001');self.make('002',status='failed');self.make('003',revision='old')
        incomplete=self.make('004');(incomplete/'network_receipts_private.json').unlink()
        malformed=self.make('005');(malformed/'summary.json').write_text('{')
        self.assertEqual(select_audit(self.root,'current'),valid)

    def test_explicit_invalid_audit_never_falls_back(self):
        self.make('001');invalid=self.make('002',revision='old')
        with self.assertRaisesRegex(ValueError,'source differs'):select_audit(self.root,'current',invalid)

    def test_no_current_success_requires_a_new_audit(self):
        self.make('001',revision='old')
        with self.assertRaisesRegex(ValueError,'No complete passed audit'):select_audit(self.root,'current')

    def test_duplicate_or_short_live_coverage_rejected(self):
        bad=copy.deepcopy(self.live);bad[-1]=bad[0]
        for i,rows in enumerate((self.live[:-1],bad)):
            with self.assertRaises(ValueError):validate_audit(self.make(str(i),live=rows),'current')

    def test_replay_cannot_be_selected_as_live_evidence(self):
        bad=copy.deepcopy(self.live);bad[0]['execution_mode']='saved_prediction_replay'
        with self.assertRaisesRegex(ValueError,'saved replay'):validate_audit(self.make('001',live=bad),'current')

    def test_network_receipt_must_match_same_execution_and_six_classes(self):
        wrong=copy.deepcopy(self.network);wrong[0]['execution_id']='stale'
        with self.assertRaisesRegex(ValueError,'another execution'):validate_audit(self.make('001',network=wrong),'current')
        wrong=copy.deepcopy(self.network);wrong[-1]=wrong[0]
        with self.assertRaisesRegex(ValueError,'coverage mismatch'):validate_audit(self.make('002',network=wrong),'current')
