"""Local auditor JSON must preserve quoted braces and reject ambiguous decisions."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from judge_response import parse_judge_response


class JudgeResponseTests(unittest.TestCase):
    def test_quoted_braces_and_escapes(self):
        value = {'assessment': 'review', 'reason': 'Case contains {quoted} text and "escaped" evidence.'}
        self.assertEqual(parse_judge_response(json.dumps(value)), value)

    def test_markdown_fences_and_text_prefix(self):
        value = {'assessment': 'uncertain', 'reason': 'Evidence is limited.'}
        self.assertEqual(parse_judge_response('Result:\n```json\n'+json.dumps(value)+'\n```'), value)

    def test_multiple_decisions_are_rejected(self):
        first = json.dumps({'assessment': 'review', 'reason': 'Mixed cases.'})
        second = json.dumps({'assessment': 'support', 'reason': 'Agree.'})
        with self.assertRaises(ValueError):
            parse_judge_response(first+'\n'+second)

    def test_invalid_schema_does_not_become_support(self):
        for value in ({'assessment': []}, {'assessment': 'support', 'reason': []},
                      {'assessment': 'yes', 'reason': 'A'}, {'assessment': 'support', 'reason': ' '},
                      {'assessment': 'support', 'reason': 'A', 'command': 'extra'}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_judge_response(json.dumps(value))

    def test_incomplete_or_non_text_response_is_rejected(self):
        for value in ('', '{"assessment":"support"', 'no response', None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_judge_response(value)


if __name__ == '__main__':
    unittest.main()
