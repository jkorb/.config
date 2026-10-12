"""Source-position matching and Plannotator block selection."""

import importlib.machinery
import importlib.util
import os
from pathlib import Path
import unittest


def helper(name):
    path = Path(__file__).resolve().parents[1] / 'scripts' / name
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


position = helper('md-position')
annotate = helper('md-annotate')


class PositionTests(unittest.TestCase):
    def test_annotation_terminal_size_and_resize(self):
        master, slave = os.openpty()
        try:
            for rows, columns in ((28, 110), (22, 70), (40, 160)):
                annotate.set_window_size(master, (rows, columns))
                self.assertEqual(os.get_terminal_size(slave), (columns, rows))
                self.assertEqual(annotate.get_window_size(slave), (rows, columns))
        finally:
            os.close(slave)
            os.close(master)

    def test_wrapping_and_formatting(self):
        source = '# Title\n\nA **long paragraph** with a [link](other.md) and more words.\nNext source line.\n'
        rendered = ['  # Title', '', '  A long paragraph with a', '  link /other.md and more words.',
                    '  Next source line.']
        self.assertEqual(position.source_line(source, rendered, 4), 3)
        self.assertEqual(position.source_line(source, rendered, 5), 4)

    def test_repeated_text_uses_surrounding_document(self):
        source = '# First\n\nRepeated passage.\n\n# Second\n\nRepeated passage.\n'
        rendered = ['# First', '', 'Repeated passage.', '', '# Second', '', 'Repeated passage.']
        self.assertEqual(position.source_line(source, rendered, 7), 7)

    def test_transformed_math_uses_nearby_source(self):
        source = '# Formula\n\n$$\\Gamma \\vdash A \\to B$$\n\n# Next section\n'
        rendered = ['# Formula', '', 'Γ ⊢ A → B', '', '# Next section']
        self.assertEqual(position.source_line(source, rendered, 3), 3)

    def test_sections_do_not_confuse_notes_and_source(self):
        def marker(name):
            return f'\x1b]8;;md-reader:{name}\x07\x1b]8;;\x07'
        rendered = marker('source') + '\n# Source\n\nRepeated passage.\n'
        rendered += marker('comments') + '\nRepeated passage.\n'
        rendered += marker('notes') + '\n# Reading notes\n\nRepeated passage.\nMore notes.\n'
        notes = 'Repeated passage.\nMore notes.\n'
        self.assertEqual(position.locate(notes, rendered, 11, 'notes'), 2)
        self.assertEqual(position.locate(notes, rendered, 2, 'notes'), 1)
        self.assertEqual(position.locate('# Source\n\nRepeated passage.\n', rendered, 11), 3)

    def test_blank_and_missing_content(self):
        self.assertEqual(position.source_line('', [], 99), 1)
        self.assertEqual(position.locate('', 'Source', 1, 'notes'), 1)
        self.assertEqual(position.source_line('One\n\nTwo\n', ['One', '', 'Two'], 2), 3)

    def test_pinned_breadcrumb_does_not_shift_source_matching(self):
        def marker(name):
            return f'\x1b]8;;md-reader:{name}\x07\x1b]8;;\x07'
        rendered = marker('header') + 'First.md › Second.md\n'
        rendered += marker('source') + '# Title\n\nFirst passage.\nSecond passage.\n'
        source = '# Title\n\nFirst passage.\nSecond passage.\n'
        self.assertEqual(position.locate(source, rendered, 4), 3)
        self.assertEqual(position.locate(source, rendered, 5), 4)

    def test_block_selection_uses_order_for_duplicate_heads(self):
        source = '# First\n\nSame text.\n\n# Second\n\nSame text.\n'
        blocks = ('  0 Heading row 0  # First\n  1 Paragraph row 2  Same text.\n'
                  '  2 Heading row 4  # Second\n  3 Paragraph row 6  Same text.\n')
        self.assertEqual(annotate.block_at_line(source, blocks, 7), 3)
        self.assertEqual(annotate.block_at_line(source, blocks, 3), 1)
        self.assertEqual(annotate.block_at_line(source, blocks, 1), 0)

    def test_block_selection_skips_closing_fences(self):
        source = '```\n# A heading inside code\n```\n\n```\nSecond block\n```\n'
        blocks = '0 Code row 0  ```\n1 Code row 4  ```\n'
        self.assertEqual(annotate.block_at_line(source, blocks, 3), 0)
        self.assertEqual(annotate.block_at_line(source, blocks, 6), 1)

    def test_annotation_startup_ignores_terminal_setup(self):
        setup = b'\x1b[?1049h\x1b[?25l\x1b[?2004h\x1b[?u\x1b[c'
        self.assertFalse(annotate.first_frame(setup))
        self.assertFalse(annotate.first_frame(setup + b'\x1b[1;80HReview'))

    def test_annotation_startup_does_not_require_footer_text(self):
        # A narrow pane can show only a truncated filename and key hints.
        frame = b'\x1b[1;40HReview\x1b[28;1Hlong-filename i move q quit\x1b[0m\x1b[?25l'
        self.assertTrue(annotate.first_frame(frame))

    def test_annotation_startup_waits_for_complete_frame(self):
        frame = b'\x1b[1;1HDocument\x1b[m\x1b[?25l'
        for end in range(len(frame)):
            self.assertFalse(annotate.first_frame(frame[:end]))
        self.assertTrue(annotate.first_frame(frame))


if __name__ == '__main__':
    unittest.main()
