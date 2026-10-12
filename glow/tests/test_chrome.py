"""Breadcrumb clipping and the shared reader footer."""

import json
from pathlib import Path
import unittest

from test_position import helper

chrome = helper('reader-prompt')
hints = helper('md-hints')
theme = json.loads((Path(__file__).resolve().parents[1] / 'onedark.json').read_text())


class ChromeTests(unittest.TestCase):
    def test_breadcrumb_order_and_current_file(self):
        text = chrome.header(['/one/root.md', '/two/child.md', '/three/current.md'],
                             'md', 100, theme, False)
        self.assertEqual(text.strip(), '  root.md  ›  child.md  ›  current.md')
        left, right = len(text) - len(text.lstrip()), 100 - len(text)
        self.assertLessEqual(abs(left - right), 1)

    def test_deep_trail_collapses_ancestors_and_keeps_current(self):
        text = chrome.header(['/long-parent-name.md'] * 10 + ['/current.md'], 'md', 35, theme, False)
        self.assertEqual(text.strip(), '… +10  ›  current.md')

    def test_long_unicode_names_and_control_characters(self):
        for columns in (8, 20, 40, 80):
            text = chrome.header(['/parent.md', '/\x1b\n' + '界' * 40 + '.md'],
                                 'md', columns, theme, False)
            self.assertNotIn('\x1b', text)
            self.assertNotIn('\n', text)
            self.assertTrue(text.endswith('.md'))
            self.assertLess(chrome.cells(text), columns)

    def test_compact_footers_keep_all_keys(self):
        for columns in (20, 40, 70, 80, 160):
            text = chrome.prompt('md', columns, theme, False)
            self.assertLess(len(text), columns)
            for key in ('e', 'a', 's', 'o', 'O', 'r', 'q'):
                self.assertIn(key, text.split())

    def test_hint_header_replaces_hidden_row_without_shifting_links(self):
        header = '\x1b]8;;md-reader:header\x07\x1b]8;;\x07 root.md\n'
        body = 'hidden row\nVisible passage\n'
        restored = hints.with_header(body, header)
        self.assertEqual(restored, header + 'Visible passage\n')
        self.assertEqual(hints.with_header(restored, header), restored)
        lines, _ = hints.viewport(restored, Path('/tmp/root.md'), 80, 24)
        self.assertTrue(lines[0].startswith(' root.md'))
        self.assertTrue(lines[1].startswith('Visible passage'))


if __name__ == '__main__':
    unittest.main()
