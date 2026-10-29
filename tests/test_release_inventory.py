"""A changed preview, source or result cannot retain an old release acceptance."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from release_inventory import verify_bindings,distribution
from check_delivery_docs import delivery_digest


class ReleaseInventoryTests(unittest.TestCase):
    def test_explicit_text_hash_normalization_preserves_content_checks(self):
        self.assertEqual(delivery_digest(b'first\r\nsecond\r\n','LF'),delivery_digest(b'first\nsecond\n','LF'))
        self.assertNotEqual(delivery_digest(b'first\r\nsecond\r\n'),delivery_digest(b'first\nsecond\n'))
        self.assertNotEqual(delivery_digest(b'changed\n','LF'),delivery_digest(b'first\n','LF'))
        with self.assertRaises(ValueError):delivery_digest(b'first','unknown')
    def test_release_bindings_match_current_files_and_application(self):
        value=json.loads((ROOT/'deliverables/source/release-validation.json').read_text(encoding='utf-8'))
        self.assertTrue(verify_bindings(value))

    def test_source_preview_result_or_artifact_tampering_is_rejected(self):
        source=json.loads((ROOT/'deliverables/source/release-validation.json').read_text(encoding='utf-8'))
        for group in ('visual_sources','artifacts','previews','results'):
            value=copy.deepcopy(source);key=next(iter(value['bindings'][group]))
            value['bindings'][group][key]='0'*64
            with self.assertRaises(ValueError):verify_bindings(value)
        source['source_revision']='stale'
        with self.assertRaises(ValueError):verify_bindings(source)

    def test_timing_summary_uses_observed_samples_only(self):
        self.assertEqual(distribution([2,4,8,10]),{'samples':4,'minimum':2,'median':6,'maximum':10,'unit':'ms'})
        self.assertNotIn('p95',distribution([1,2,3]))
        for values in ([],[-1],[float('nan')],[float('inf')]):
            with self.assertRaises(ValueError):distribution(values)
