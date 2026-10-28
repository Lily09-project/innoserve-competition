"""Protect A2 physical delivery and anonymous, correctly scoped live summaries."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from demo_walkthrough import summarize, summarize_receipt
from network_contract import digest
from package_finals import ASSETS, asset_bytes


class FinalsDeliveryTests(unittest.TestCase):
    def test_offline_package_matches_deliverables_and_excludes_private_data(self):
        with zipfile.ZipFile(ROOT / 'deliverables/決賽離線展示包.zip') as archive:
            self.assertEqual(set(archive.namelist()), set(ASSETS) | {'使用說明.txt', 'SHA256SUMS.txt'})
            hashes = archive.read('SHA256SUMS.txt').decode('utf-8')
            for name in ASSETS:
                value = archive.read(name)
                self.assertEqual(value, asset_bytes(name))
                self.assertIn(hashlib.sha256(value).hexdigest()+'  '+name, hashes)

    def test_a2_dimensions_fonts_and_recorded_metrics(self):
        ns = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
              'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
        with zipfile.ZipFile(ROOT / 'deliverables/決賽海報_AI資安框架_A2.pptx') as archive:
            presentation = ET.fromstring(archive.read('ppt/presentation.xml'))
            size = presentation.find('p:sldSz', ns)
            self.assertEqual((int(size.get('cx')), int(size.get('cy'))), (420*36000, 594*36000))
            self.assertEqual(len(presentation.findall('p:sldIdLst/p:sldId', ns)), 1)
            slide = ET.fromstring(archive.read('ppt/slides/slide1.xml'))
            text = ''.join(x.text or '' for x in slide.findall('.//a:t', ns))
            for value in ('79.75%', '92.10%', '93.05%', '97.62%', '93.89%', '415', '13', '35', '非原生攻擊防禦率'):
                self.assertIn(value, text)
            self.assertGreater(len(slide.findall('.//a:r', ns)), 50)
            for run in slide.findall('.//a:rPr', ns):
                self.assertEqual(run.find('a:latin', ns).get('typeface'), 'Times New Roman')
                self.assertEqual(run.find('a:ea', ns).get('typeface'), 'DFKai-SB')
            self.assertIsNone(slide.find('p:transition', ns))
            core = ET.fromstring(archive.read('docProps/core.xml'))
            for item in core:
                if item.tag.rsplit('}', 1)[-1] in ('creator', 'lastModifiedBy'):
                    self.assertFalse(item.text)
        self.assertTrue((ROOT / 'deliverables/決賽海報_AI資安框架_A2.pdf').read_bytes().startswith(b'%PDF'))

    def event(self):
        rows, previous = [], '0'*64
        for i, stage in enumerate(('detection', 'retrieval', 'judge', 'policy')):
            row = {'event_id': 'private-event', 'sequence': i, 'previous_sha256': previous, 'stage': stage}
            if i == 0:
                row.update(execution_id='private-run', prediction=2)
            row['sha256'] = digest(row)
            rows.append(row)
            previous = row['sha256']
        return {'event_id': 'private-event', 'execution_id': 'private-run', 'prediction': 2,
                'execution_mode': 'live_local_models', 'confidence': .9, 'validation_label': 'secret-truth',
                'raw_response': 'secret-model-reply', 'source_ip': 'secret-address',
                'result': {'event_id': 'private-event', 'prediction': 2, 'ledger': rows,
                           'evidence': [{'rank': i+1, 'label': 'SSH-Bruteforce', 'similarity': .9, 'case_id': 'private-case'} for i in range(5)],
                           'judge': {'assessment': 'support'}, 'policy': {'allowed': True, 'action': 'auth_hardening'}}}

    def test_anonymous_summary_drops_private_fields_and_never_claims_execution(self):
        value = summarize(self.event(), 'live')
        encoded = json.dumps(value)
        for secret in ('private-event', 'private-run', 'private-case', 'secret-truth', 'secret-model-reply', 'secret-address'):
            self.assertNotIn(secret, encoded)
        self.assertFalse(value['network_executed_in_this_walkthrough'])
        self.assertTrue(value['event_ledger_verified'])

    def test_tampered_event_and_execution_rejected(self):
        event = self.event()
        event['result']['ledger'][0]['prediction'] = 1
        with self.assertRaises(ValueError):
            summarize(event, 'live')
        event = copy.deepcopy(self.event())
        event['execution_id'] = 'other-run'
        with self.assertRaises(ValueError):
            summarize(event, 'live')

    def test_receipt_uses_nested_measurements_not_aggregate_keys(self):
        value = summarize_receipt({'action': 'auth_hardening', 'rules_applied': 2,
                                   'background_after': {'success_rate': 1},
                                   'recovery': {'success_rate': 1}, 'rollback_integrity': True,
                                   'commands_executed': 'private-details'})
        self.assertEqual(value['background_success_rate'], 1)
        self.assertEqual(value['recovery_success_rate'], 1)
        self.assertNotIn('commands_executed', value)


if __name__ == '__main__':
    unittest.main()
