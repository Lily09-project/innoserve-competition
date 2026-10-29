"""Protect time allocation, exact Q&A mapping and current offline materials."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from check_finals_readiness import validate_plan, require_tokens, check_bundle, check_claims, audit


class FinalsReadinessTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((ROOT / 'deliverables/source/finals-runbook.json').read_text(encoding='utf-8'))

    def test_five_minute_plan_includes_video_and_buffer(self):
        value = validate_plan(self.plan)
        self.assertEqual(value['planned_spoken_seconds'], 260)
        self.assertEqual(value['planned_total_seconds'], 300)
        self.assertFalse(value['timing_is_human_measured'])

    def test_extra_minute_cannot_be_filled_with_more_content(self):
        changed = copy.deepcopy(self.plan)
        changed['segments'][2]['seconds'] += 60
        with self.assertRaisesRegex(ValueError, 'five_minute'):
            validate_plan(changed)

    def test_video_must_remain_second_and_thirty_seconds(self):
        changed = copy.deepcopy(self.plan)
        changed['video']['slide'] = 3
        with self.assertRaisesRegex(ValueError, 'video'):
            validate_plan(changed)

    def test_six_questions_must_map_to_three_final_pages(self):
        changed = copy.deepcopy(self.plan)
        changed['qa'][0]['slide'] = 9
        with self.assertRaisesRegex(ValueError, 'question'):
            validate_plan(changed)

    def test_metric_match_ignores_spacing_but_not_changed_numbers(self):
        require_tokens('相同 18,998 筆 97.62%', ['18998', '97.62%'], 'fixture')
        with self.assertRaisesRegex(ValueError, 'claim_mismatch'):
            require_tokens('97.61%', ['97.62%'], 'fixture')

    def test_all_public_claim_surfaces_match_recorded_metrics(self):
        self.assertTrue(check_claims()['embedded_movie_matches'])

    def test_bundle_contains_current_operator_materials(self):
        self.assertEqual(check_bundle()['offline_assets'], 10)

    def test_readiness_does_not_assert_human_checks_completed(self):
        value = audit()
        self.assertFalse(value['human_checks_verified_by_this_script'])
        self.assertEqual(len(value['human_checks']), 3)
        self.assertFalse(value['claims']['native_playback_executed'])


if __name__ == '__main__':
    unittest.main()
