import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'app')]

import console_card
from provenance import SOURCE_FILES


def render(summary, receipt=None):
    lines = []
    card = console_card.Card(color=False, pause=0, out=lines.append)
    console_card.render_summary(summary, card)
    if receipt:
        console_card.render_receipt(receipt, card)
    return '\n'.join(lines)


SUMMARY = {'mode': 'live', 'event_token': 'abc123def456', 'prediction': 'SSH-Bruteforce', 'confidence': 0.9871,
           'top5': [{'rank': k + 1, 'label': 'SSH-Bruteforce' if k != 2 else 'FTP-BruteForce', 'similarity': 0.9 - k / 100} for k in range(5)],
           'assessment': 'support', 'policy_allowed': True, 'policy_action': 'auth_hardening'}


class ConsoleCardTests(unittest.TestCase):
    def test_summary_reads_in_plain_chinese(self):
        text = render(SUMMARY, {'action': 'auth_hardening', 'rules_applied': 2, 'background_success_rate': 1.0,
                                'recovery_success_rate': 1.0, 'rollback_integrity': True})
        for phrase in ('SSH 暴力破解（SSH-Bruteforce）', '98.7%', '4 / 5 與正式判定同類', '✓ 支持', '強化認證',
                       '✓ 允許執行', '2 條', '✓ 規則已撤銷，回復完整'):
            self.assertIn(phrase, text)
        for raw in ('True', 'False', 'auth_hardening', '0.9871'):
            self.assertNotIn(raw, text)
        self.assertEqual([line.split()[1] for line in text.splitlines() if line.startswith('━━ ')],
                         ['1/4', '2/4', '3/4', '4/4', '回條'])

    def test_blocked_action_and_uncertain_audit_are_explicit(self):
        text = render({**SUMMARY, 'assessment': 'uncertain', 'policy_allowed': False, 'policy_action': 'capture_evidence'})
        self.assertIn('? 不確定', text)
        self.assertIn('✕ 不自動執行，保留人工核准', text)
        self.assertIn('保留蒐證', text)

    def test_plain_output_has_no_escape_codes(self):
        self.assertNotIn('\033[', render(SUMMARY))

    def test_display_layer_stays_outside_recorded_code_revision(self):
        # The evidence revision covers showcase.py and demo_walkthrough.py; the projector layer must not join it.
        for name in ('scripts/console_card.py', 'scripts/present_console.py'):
            self.assertNotIn(name, SOURCE_FILES)


if __name__ == '__main__':
    unittest.main()
