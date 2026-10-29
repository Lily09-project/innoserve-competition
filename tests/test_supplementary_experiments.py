"""Contract fixtures verify experiment isolation; never benchmark evidence."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'experiments'))
from common import payload, retrieve, rule, summarize, PROMPT
from export_results import verify, sha, SOURCES
from contract_fixtures import event_bundle


class SupplementaryTests(unittest.TestCase):
    def setUp(self):
        self.bank, self.events, _ = event_bundle()
        for e in self.events:
            e.update(pred_ctbm=e['prediction'], pred_pbcnn=e['prediction'])

    def test_payload_excludes_truth_identity_and_label(self):
        event = self.events[2]
        evidence = retrieve(self.bank, event)
        first = payload(event, evidence)
        changed = copy.deepcopy(event)
        changed['validation_label'] = 16
        changed['event_id'] = 'different-query'
        self.assertEqual(first, payload(changed, evidence))
        self.assertEqual(set(first), {'detector_class', 'confidence', 'branch_predictions', 'train_only_neighbours'})

    def test_retrieval_rejects_overlap_and_provenance(self):
        event = copy.deepcopy(self.events[0])
        event['event_id'] = self.bank.ids[0]
        with self.assertRaisesRegex(ValueError, 'overlap'):
            retrieve(self.bank, event)
        event['event_id'] = 'new-query'
        event['representation_id'] = 'other'
        with self.assertRaisesRegex(ValueError, 'representation'):
            retrieve(self.bank, event)

    def test_same_class_fixture_ranked_and_tied_deterministically(self):
        for dimensions in (512, 529):
            rows = retrieve(self.bank, self.events[3], dimensions)
            self.assertEqual([row['rank'] for row in rows], [1, 2, 3, 4, 5])
            self.assertTrue(all(row['label_id'] == 3 for row in rows))
            self.assertEqual([row['case_id'] for row in rows], sorted(row['case_id'] for row in rows))

    def test_rules_do_not_read_truth(self):
        event = self.events[2]
        evidence = retrieve(self.bank, event)
        before = rule(event, evidence)
        event['validation_label'] = 16
        self.assertEqual(before, rule(event, evidence))

    def test_precision_coverage_and_wrong_support_separate(self):
        events = self.events[:2]
        events[1]['validation_label'] = 2
        production = {e['event_id']: retrieve(self.bank, e) for e in events}
        result = summarize(events, ['support', 'support'], production)
        self.assertEqual(result['support_precision'], .5)
        self.assertEqual(result['support_coverage'], 1)
        self.assertEqual(result['wrong_support'], 1)
        self.assertEqual(result['classification_changed_count'], 0)
        self.assertEqual(result['network_actions_executed'], 0)

    def test_shared_prompt_and_experimental_scope(self):
        self.assertIn('no neighbours', PROMPT)
        self.assertIn('Never assume ground truth', PROMPT)

    def test_public_supplementary_binding(self):
        self.assertTrue(verify(ROOT))

    def test_binding_covers_all_executed_sources(self):
        data = json.loads((ROOT / 'results/supplementary_validation.json').read_text(encoding='utf-8'))
        for name in SOURCES:
            self.assertEqual(data['bindings'][name], sha(ROOT / name))


if __name__ == '__main__':
    unittest.main()
