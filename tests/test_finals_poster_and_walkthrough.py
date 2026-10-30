"""Protect A2 physical delivery and anonymous, correctly scoped live summaries."""
import copy
import hashlib
import json
import re
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
from media_results import load_metrics


class FinalsDeliveryTests(unittest.TestCase):
    def test_speaker_notes_match_embedded_notes(self):
        source = (ROOT / 'deliverables/source/speaker-notes.md').read_text(encoding='utf-8')
        sections = re.findall(r'^# (\d+)_slide\n\n(.*?)(?=\n\n---|\Z)', source, re.M | re.S)
        self.assertEqual(len(sections), 12)
        ns = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
        with zipfile.ZipFile(ROOT / 'deliverables/決賽簡報_AI資安框架.pptx') as archive:
            for number, body in sections:
                root = ET.fromstring(archive.read(f'ppt/notesSlides/notesSlide{int(number)}.xml'))
                rendered = ''.join(node.text or '' for node in root.findall('.//a:t', ns))
                self.assertIn(re.sub(r'\s+', '', body), re.sub(r'\s+', '', rendered), number)

    def test_anonymous_scan_includes_poster_and_deck(self):
        from audit_final_chain import scan_delivery_anonymity
        rows = scan_delivery_anonymity()
        for name in ('決賽簡報_AI資安框架.pptx', '決賽海報_AI資安框架_A2.pptx'):
            self.assertTrue(any(row['path'].startswith(name+'::') for row in rows))
        self.assertFalse(any(row['identity_matches'] for row in rows))

    def test_user_palette_is_present_in_native_poster_and_slides(self):
        colors = json.loads((ROOT / 'design-system/palette.json').read_text(encoding='utf-8'))
        expected = {'navy': '#16324F', 'blue': '#245EA8', 'teal': '#087F8C', 'gray': '#F4F7FA', 'gold': '#E3A338', 'ink': '#243447'}
        for key, value in expected.items():
            self.assertEqual(colors[key], value)
        for name in ('deliverables/決賽海報_AI資安框架_A2.pptx', 'deliverables/決賽簡報_AI資安框架.pptx'):
            with zipfile.ZipFile(ROOT / name) as archive:
                ns = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
                theme = ET.fromstring(archive.read('ppt/theme/theme1.xml'))
                scheme = {}
                for node in theme.find('.//a:clrScheme', ns):
                    paint = list(node)[0]
                    scheme[node.tag.rsplit('}', 1)[-1]] = paint.get('val') if paint.tag.endswith('srgbClr') else paint.get('lastClr')
                resolved = set()
                for path in archive.namelist():
                    if path.startswith('ppt/slides/slide') and path.endswith('.xml'):
                        slide = ET.fromstring(archive.read(path))
                        resolved.update(c.get('val') for c in slide.findall('.//a:srgbClr', ns))
                        resolved.update(scheme.get(c.get('val')) for c in slide.findall('.//a:schemeClr', ns))
                for color in expected.values():
                    self.assertIn(color.lstrip('#'), resolved, name)
                self.assertNotIn('0070D1', resolved)

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
            metrics=load_metrics()
            expected=[f'{metrics["macro_f1"][name]*100:.2f}%' for name in ('PBCNN','CTBM','OOF Gate')]
            expected += [f'{metrics[key]*100:.2f}%' for key in ('accuracy','top5','mrr5')]
            expected += [str(metrics[key]) for key in ('support','review','uncertain')]+['非原生攻擊防禦率']
            for value in expected:
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

    def test_poster_centered_hierarchy_and_visible_advantages(self):
        ns = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
              'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
        with zipfile.ZipFile(ROOT / 'deliverables/決賽海報_AI資安框架_A2.pptx') as archive:
            slide = ET.fromstring(archive.read('ppt/slides/slide1.xml'))
            texts = slide.findall('.//p:sp', ns)
            title = next(s for s in texts if s.find('p:nvSpPr/p:cNvPr', ns).get('name') == 'PosterTitle_Centered_210mm')
            self.assertTrue(all(int(r.get('sz')) >= 4400 for r in title.findall('.//a:rPr', ns)))
            paragraphs = [p for p in slide.findall('.//a:p', ns) if p.find('a:r', ns) is not None]
            centered = [p for p in paragraphs if p.find('a:pPr', ns) is not None and p.find('a:pPr', ns).get('algn') == 'ctr']
            self.assertGreater(len(centered) / len(paragraphs), .85)
            content = ''.join(t.text or '' for t in slide.findall('.//a:t', ns))
            for phrase in ('互補判定', '任務證據', '受控可追溯', '保留正式分類', '本機AI', '到期回復'):
                self.assertIn(phrase, content)

    def test_poster_comparison_scale_is_explicit_and_zero_based(self):
        ns = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
        with zipfile.ZipFile(ROOT / 'deliverables/決賽海報_AI資安框架_A2.pptx') as archive:
            root = ET.fromstring(archive.read('ppt/slides/slide1.xml'))
            labels = {''.join(p.itertext()) for p in root.findall('.//a:t', ns)}
            self.assertTrue({'0%', '50%', '100%'}.issubset(labels))
        source = (ROOT / 'scripts/presentation/build_a2_poster.py').read_text(encoding='utf-8')
        self.assertIn('94*value/100', source)

    def event(self):
        evidence = [{'rank': i+1, 'label_id': 2, 'label': 'SSH-Bruteforce', 'similarity': .9, 'case_id': 'private-case-'+str(i)} for i in range(5)]
        judge = {'assessment': 'support', 'mode': 'live_local_llm_inference',
                 'input_sha256': digest({'event_id': 'private-event', 'prediction': 2, 'evidence': evidence})}
        policy = {'allowed': True, 'action': 'auth_hardening'}
        payloads = [{'mode': 'live_checkpoint_inference', 'execution_id': 'private-run', 'prediction': 2},
                    {'count': 5}, judge, policy]
        rows, previous = [], '0'*64
        for i, stage in enumerate(('detection', 'retrieval', 'judge', 'policy')):
            row = {'event_id': 'private-event', 'sequence': i, 'previous_sha256': previous, 'stage': stage, **payloads[i]}
            row['sha256'] = digest(row)
            rows.append(row)
            previous = row['sha256']
        return {'event_id': 'private-event', 'execution_id': 'private-run', 'prediction': 2,
                'execution_mode': 'live_local_models', 'confidence': .9, 'validation_label': 'secret-truth',
                'probabilities': [.1, 0, .9]+[0]*14,
                'raw_response': 'secret-model-reply', 'source_ip': 'secret-address',
                'result': {'event_id': 'private-event', 'prediction': 2, 'ledger': rows,
                           'evidence': evidence, 'judge': judge, 'policy': policy}}

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

    def test_display_fields_cannot_disagree_with_bound_evidence(self):
        for target in ('policy', 'judge', 'evidence', 'confidence', 'prediction', 'mode'):
            event = self.event()
            if target == 'policy':
                event['result']['policy'] = {'allowed': False, 'action': 'capture_evidence'}
            elif target == 'judge':
                event['result']['judge'] = {**event['result']['judge'], 'assessment': 'uncertain'}
            elif target == 'evidence':
                event['result']['evidence'][0]['similarity'] = .1
            elif target == 'confidence':
                event['confidence'] = .99
            elif target == 'mode':
                event['execution_mode'] = 'saved_prediction_retrieval_recomputed'
            else:
                event['prediction'] = event['result']['prediction'] = 0
            with self.subTest(target=target), self.assertRaises(ValueError):
                summarize(event, 'live')

    def test_saved_mode_is_explicit_and_does_not_claim_new_execution(self):
        event = self.event()
        event['execution_mode'] = 'saved_prediction_retrieval_recomputed'
        value = summarize(event, 'saved')
        self.assertNotIn('execution_token', value)
        self.assertFalse(value['network_executed_in_this_walkthrough'])

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
