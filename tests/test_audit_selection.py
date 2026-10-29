"""Newer incomplete, replayed or stale evidence cannot become release evidence."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_selection import select_audit, validate_audit
from contract_fixtures import audit_bundle
from provenance import identifier


class AuditSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='audit-selection-contract-')
        self.root=Path(self.temp.name)
        self.summary,self.live,self.network=audit_bundle()
        self.manifest={'fixture':True};self.summary['asset_revision']=identifier(self.manifest)
        for event in self.live:event['asset_revision']=self.summary['asset_revision']

    def tearDown(self):self.temp.cleanup()

    def make(self,name,revision='current',status='passed',live=None,network=None):
        folder=self.root/('framework_audit_'+name);folder.mkdir()
        for file,value in [('asset_manifest.json',self.manifest),('summary.json',{**self.summary,'status':status,'source_revision':revision}),('live_events_private.json',self.live if live is None else live),('network_receipts_private.json',self.network if network is None else network)]:
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

    def test_broken_live_or_network_ledger_is_rejected(self):
        bad=copy.deepcopy(self.live);bad[0]['result']['ledger'][0]['sha256']='0'*64
        with self.assertRaises(ValueError):validate_audit(self.make('001',live=bad),'current')
        bad=copy.deepcopy(self.network);bad[1]['subject_after']['success_rate']=1
        with self.assertRaises(ValueError):validate_audit(self.make('002',network=bad),'current')

    def test_failed_measurement_even_when_rehashed_is_rejected(self):
        from network_contract import build_network_scenario,bind_network_receipt
        bad=copy.deepcopy(self.network)
        for i in range(1,len(bad)):
            event=next(e for e in self.live if e['event_id']==bad[i]['event_id'])
            measurement={k:v for k,v in bad[i].items() if k!='ledger'}
            measurement.update(rules_applied=0,network_action_executed=False,commands_executed=0)
            measurement['subject_after']['success_rate']=1
            bad[i]=bind_network_receipt(build_network_scenario(event),measurement)
        self.summary['non_disruptive_network_cases']=6
        with self.assertRaisesRegex(ValueError,'rules_missing'):validate_audit(self.make('001',network=bad),'current')

    def test_changed_model_manifest_or_expected_version_is_rejected(self):
        folder=self.make('001')
        with self.assertRaises(ValueError):validate_audit(folder,'current','different-assets')
        (folder/'asset_manifest.json').write_text('{}')
        with self.assertRaises(ValueError):validate_audit(folder,'current')
