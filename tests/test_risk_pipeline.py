"""Policy risk is authorization, not deployment; failed refresh restores files."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from contract_fixtures import event_bundle,judge_record
from pipeline import task_vector
from analyze_policy_risk import analyze
from provenance import code_revision,file_hash
import finals_pipeline


class RiskTests(unittest.TestCase):
    def test_published_risk_counts_and_source_match_recorded_evidence(self):
        risk=json.loads((ROOT/'results/policy_risk_analysis.json').read_text(encoding='utf-8'))
        judge=json.loads((ROOT/'results/local_judge_17class.json').read_text(encoding='utf-8'))
        counts=risk['counts']
        self.assertEqual(counts['total'],judge['cases'])
        self.assertEqual(counts['wrong'],judge['detector_error_count'])
        self.assertEqual(counts['wrong_support'],judge['false_support_count'])
        self.assertEqual(counts['wrong_support'],counts['wrong_support_disruptive_allowed']+counts['wrong_support_non_disruptive_or_blocked'])
        self.assertEqual(sum(row['count'] for row in risk['wrong_support_groups']),counts['wrong_support'])
        self.assertEqual(sum(row['count'] for row in risk['wrong_support_groups'] if row['disruptive_allowed']),counts['wrong_support_disruptive_allowed'])
        self.assertEqual(risk['network_actions_executed'],0)
        self.assertEqual(risk['source_revision'],code_revision())
        recovery=json.loads((ROOT/'deliverables/source/recovery-validation.json').read_text(encoding='utf-8'))
        self.assertEqual(recovery['source_revision'],code_revision())
        self.assertEqual(recovery['probe_script_sha256'],file_hash(ROOT/'scripts/network_fault_probe.py'))
        self.assertEqual(recovery['status'],'passed')
    def test_wrong_support_is_not_equated_with_actual_false_blocks(self):
        bank,events,records=event_bundle()
        events[7]['validation_label']=11
        event=events[3]
        event.update(validation_label=4,confidence=.6,probabilities=[.4,0,0,.6]+[0]*13)
        event['evidence']=bank.retrieve(task_vector(event['embedding'],event['probabilities']),event['event_id'],bank.representation_id,bank.model_sha256)
        records[3]=judge_record(event,event['evidence'])
        before=copy.deepcopy(events)
        detector=json.loads((ROOT/'results/detection_17class.json').read_text(encoding='utf-8'))['OOF Gate']
        public,private=analyze(events,bank,{r['event_id']:r for r in records},detector)
        self.assertEqual(public['counts']['wrong_support'],2)
        self.assertEqual(public['counts']['wrong_support_disruptive_allowed'],1)
        self.assertEqual(public['counts']['wrong_support_non_disruptive_or_blocked'],1)
        self.assertEqual(public['network_actions_executed'],0)
        self.assertEqual(len(private),2)
        self.assertNotIn('query-',json.dumps(public))
        self.assertEqual(events,before)

    def test_analysis_reports_confusions_from_the_actual_matrix(self):
        bank,events,records=event_bundle()
        detector=json.loads((ROOT/'results/detection_17class.json').read_text(encoding='utf-8'))['OOF Gate']
        public,_=analyze(events,bank,{r['event_id']:r for r in records},detector)
        for row in public['weak_class_analysis']:
            source=next(item for item in detector['per_class'] if item['label']==row['label'])
            self.assertEqual(row['f1'],source['f1'])
            self.assertTrue(all(item['predicted_label']!=row['label'] for item in row['largest_confusions']))


class PipelineTests(unittest.TestCase):
    def test_refresh_failure_restores_existing_and_removes_only_new_outputs(self):
        with tempfile.TemporaryDirectory(prefix='pipeline-rollback-contract-') as folder:
            root=Path(folder);(root/'results').mkdir();log=root/'validation';log.mkdir()
            original=root/'results/framework_validation.json';original.write_text('original')
            def fail(command,folder,index,root):
                original.write_text('partial')
                (root/'results/policy_risk_analysis.json').write_text('new partial output')
                raise RuntimeError('injected failure')
            with self.assertRaises(RuntimeError):finals_pipeline.refresh_evidence('fixture',log,root,fail)
            self.assertEqual(original.read_text(),'original')
            self.assertFalse((root/'results/policy_risk_analysis.json').exists())
            self.assertEqual((log/'before/results/framework_validation.json').read_text(),'original')

    def test_verification_stops_at_first_failure(self):
        calls=[]
        def fail(*args):calls.append(args[0]);raise RuntimeError('fixture failure')
        with self.assertRaises(RuntimeError):finals_pipeline.verify(Path('.'),runner=fail)
        self.assertEqual(len(calls),1)

    def test_staging_cannot_overwrite_or_escape_workspace_validation(self):
        with tempfile.TemporaryDirectory(prefix='staging-contract-') as folder:
            root=Path(folder);target=root/'validation/current';target.mkdir(parents=True)
            for path in (target,root/'outside'):
                with self.assertRaises(ValueError):finals_pipeline.stage_delivery(path,root)

    def test_refresh_order_does_not_bind_a_stale_snapshot(self):
        names=[Path(command[1]).name for command in finals_pipeline.refresh_commands('fixture')]
        self.assertLess(names.index('export_framework_validation.py'),names.index('media_results.py'))
        self.assertLess(names.index('analyze_policy_risk.py'),names.index('release_inventory.py'))
        self.assertLess(names.index('media_results.py'),names.index('release_inventory.py'))
