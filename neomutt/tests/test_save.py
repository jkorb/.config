"""Filesystem safety tests: only TemporaryDirectory fixtures are modified."""
import contextlib
import errno
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/neomutt-save'
loader = importlib.machinery.SourceFileLoader('neomutt_save', str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
save = importlib.util.module_from_spec(spec)
loader.exec_module(save)


class SaveSafety(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.run = self.root / 'run'
        self.run.mkdir()
        for name in ('raw', 'files', 'discarded'):
            (self.run / name).mkdir()
        save.store(self.run, [])
        self.source = self.run / 'raw/report.txt'
        self.source.write_bytes(b'new attachment')

    def test_numbered_copy_preserves_existing_files_and_symlinks(self):
        destination = self.root / 'report.txt'
        destination.write_bytes(b'existing')
        (self.root / 'report (1).txt').symlink_to(self.root / 'missing')
        target = save.copy_new(self.source, destination)
        self.assertEqual(target.name, 'report (2).txt')
        self.assertEqual(destination.read_bytes(), b'existing')
        self.assertTrue((self.root / 'report (1).txt').is_symlink())
        self.assertEqual(target.read_bytes(), b'new attachment')

    def test_numbered_move_preserves_existing_destination(self):
        destination = self.root / 'report.txt'
        destination.write_bytes(b'existing')
        target = save.move_new(self.source, destination)
        self.assertEqual(target.name, 'report (1).txt')
        self.assertEqual(destination.read_bytes(), b'existing')
        self.assertEqual(target.read_bytes(), b'new attachment')

    def test_collect_rejects_outside_files_and_symlinks(self):
        outside = self.root / 'private.txt'
        outside.write_bytes(b'keep')
        with self.assertRaises(ValueError):
            save.collect(self.run, outside)
        link = self.run / 'raw/link.txt'
        link.symlink_to(outside)
        with self.assertRaises(ValueError):
            save.collect(self.run, link)
        self.assertEqual(outside.read_bytes(), b'keep')

    def test_duplicate_exports_get_distinct_names(self):
        save.collect(self.run, self.source)
        save.collect(self.run, self.source)
        records = save.load(self.run)
        self.assertEqual([Path(r['path']).name for r in records], ['report.txt', 'report (1).txt'])

    def test_open_descriptor_tracks_renames(self):
        fd = os.open(self.source, os.O_RDONLY)
        try:
            renamed = self.root / 'renamed.txt'
            self.source.rename(renamed)
            self.assertEqual(save.current_path(fd).resolve(), renamed)
        finally:
            os.close(fd)

    def test_replacement_is_never_discarded(self):
        expected = save.identity(self.source)
        original = self.source.with_name('original.txt')
        self.source.rename(original)
        self.source.write_bytes(b'new unrelated file')
        with patch.object(save.subprocess, 'run') as trash:
            with self.assertRaises(ValueError):
                save.discard(self.run, self.source, expected)
            trash.assert_not_called()
        self.assertEqual(self.source.read_bytes(), b'new unrelated file')
        self.assertEqual(original.read_bytes(), b'new attachment')

    def test_cleanup_race_restores_unrelated_file(self):
        expected = save.identity(self.source)
        real_move = save.move_new
        def raced(source, target):
            source.rename(source.with_name('original.txt'))
            source.write_bytes(b'replacement')
            return real_move(source, target)
        with patch.object(save, 'move_new', side_effect=raced), patch.object(save.subprocess, 'run') as trash:
            with self.assertRaises(ValueError):
                save.discard(self.run, self.source, expected)
            trash.assert_not_called()
        self.assertEqual(self.source.read_bytes(), b'replacement')

    def test_only_verified_file_is_sent_to_trash(self):
        expected = save.identity(self.source)
        with patch.object(save.subprocess, 'run') as trash:
            save.discard(self.run, self.source, expected)
            args = trash.call_args.args[0]
            self.assertEqual(args[0], '/usr/bin/trash')
            target = Path(args[1])
            self.assertEqual(target.parent, self.run / 'discarded')
            self.assertEqual(save.identity(target), expected)

    def test_move_wrapper_refuses_unrelated_file(self):
        other = self.root / 'other.txt'
        other.write_bytes(b'keep')
        with self.assertRaises(ValueError):
            save.move_selection(self.run, ['-i', '--', str(other), str(self.run)])
        self.assertEqual(other.read_bytes(), b'keep')

    def test_move_between_volumes_keeps_source(self):
        save.store(self.run, [{'path': str(self.source), 'identity': save.identity(self.source)}])
        with patch.object(save, 'rename_new', side_effect=OSError(errno.EXDEV, 'Cross-device link')):
            with self.assertRaisesRegex(ValueError, 'source retained'):
                save.move_selection(self.run, ['-i', '--', str(self.source), str(self.root)])
        self.assertEqual(self.source.read_bytes(), b'new attachment')

    def test_trash_failure_retains_file_in_recovery_directory(self):
        expected = save.identity(self.source)
        with patch.object(save.subprocess, 'run', side_effect=OSError('Trash unavailable')):
            with self.assertRaises(OSError):
                save.discard(self.run, self.source, expected)
        retained = self.run / 'discarded' / self.source.name
        self.assertEqual(save.identity(retained), expected)
        self.assertEqual(retained.read_bytes(), b'new attachment')

    def test_cancel_preserves_exports_and_existing_downloads(self):
        save.collect(self.run, self.source)
        downloads = self.root / 'Downloads'
        downloads.mkdir()
        existing = downloads / 'report.txt'
        existing.write_bytes(b'existing')
        with patch.object(save.Path, 'home', return_value=self.root), patch.object(save, 'organize', side_effect=RuntimeError('cancel')):
            with self.assertRaises(RuntimeError):
                save.manage(self.run)
        self.assertEqual(existing.read_bytes(), b'existing')
        self.assertEqual((downloads / 'report (1).txt').read_bytes(), b'new attachment')

    def test_foreign_selection_does_not_affect_foreign_files(self):
        save.collect(self.run, self.source)
        foreign = self.root / 'foreign.txt'
        foreign.write_bytes(b'keep')
        def picker(run, paths):
            return {str(paths[0]), str(foreign)}
        with patch.object(save.Path, 'home', return_value=self.root), patch.object(save, 'organize', side_effect=picker), patch.object(save.subprocess, 'run') as trash, contextlib.redirect_stdout(io.StringIO()):
            save.manage(self.run)
        trash.assert_not_called()
        self.assertEqual(foreign.read_bytes(), b'keep')

    def test_selection_through_directory_symlink_keeps_moved_attachment(self):
        save.collect(self.run, self.source)
        destination = self.root / 'Dropbox/Teaching/Letters/Example, Person'
        destination.mkdir(parents=True)
        alias = self.root / 'Teaching'
        alias.symlink_to(self.root / 'Dropbox/Teaching', target_is_directory=True)
        moved = destination / 'main_-_with_abstract.pdf'
        def picker(run, paths):
            paths[0].rename(moved)
            return {str(alias / 'Letters/Example, Person' / moved.name)}
        with patch.object(save.Path, 'home', return_value=self.root), patch.object(save, 'organize', side_effect=picker), patch.object(save.subprocess, 'run') as trash, contextlib.redirect_stdout(io.StringIO()):
            save.manage(self.run)
        trash.assert_not_called()
        self.assertEqual(moved.read_bytes(), b'new attachment')

    def test_unreadable_selection_cancels_all_cleanup(self):
        save.collect(self.run, self.source)
        def picker(run, paths):
            return {str(self.root / 'missing-selected-file.pdf')}
        with patch.object(save.Path, 'home', return_value=self.root), patch.object(save, 'organize', side_effect=picker), patch.object(save.subprocess, 'run') as trash:
            with self.assertRaisesRegex(RuntimeError, 'all exported files were kept'):
                save.manage(self.run)
        trash.assert_not_called()
        self.assertEqual((self.root / 'Downloads/report.txt').read_bytes(), b'new attachment')

    def test_bulk_symlink_selection_trashes_only_unselected_export(self):
        save.collect(self.run, self.source)
        save.collect(self.run, self.source)
        destination = self.root / 'real folder'
        destination.mkdir()
        alias = self.root / 'linked folder'
        alias.symlink_to(destination, target_is_directory=True)
        moved = []
        def picker(run, paths):
            for path in paths:
                moved.append(destination / path.name)
                path.rename(moved[-1])
            return {str(alias / moved[0].name)}
        with patch.object(save.Path, 'home', return_value=self.root), patch.object(save, 'organize', side_effect=picker), patch.object(save.subprocess, 'run') as trash, contextlib.redirect_stdout(io.StringIO()):
            save.manage(self.run)
        self.assertEqual(moved[0].read_bytes(), b'new attachment')
        self.assertFalse(moved[1].exists())
        trash.assert_called_once_with([save.TRASH, str(self.run / 'discarded' / moved[1].name)], check=True)

    def test_filename_sanitization(self):
        self.assertEqual(save.safe_name('../../report.txt'), 'report.txt')
        self.assertEqual(save.safe_name('a\nb.txt'), 'a_b.txt')
        self.assertEqual(save.safe_name('..'), 'attachment')


if __name__ == '__main__':
    unittest.main()
