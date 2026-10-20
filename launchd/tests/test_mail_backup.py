"""Exercise the actual backup command on disposable Maildirs."""
import importlib.machinery
import importlib.util
from pathlib import Path
import tempfile
import unittest

loader = importlib.machinery.SourceFileLoader('mail_backup', str(Path(__file__).resolve().parents[1] / 'scripts/mail-backup'))
spec = importlib.util.spec_from_loader(loader.name, loader)
module = importlib.util.module_from_spec(spec)
loader.exec_module(module)


class MailBackupTests(unittest.TestCase):
    def test_deleted_and_changed_messages_remain_recoverable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, dest = root / 'source', root / 'backup'
            cur = source / 'Inbox/cur'
            cur.mkdir(parents=True)
            first, second = cur / 'a:2,S', cur / 'b:2,S'
            first.write_bytes(b'original message')
            second.write_bytes(b'old body')
            (source / 'Inbox/.mbsyncstate').write_text('state')
            (source / 'Inbox/tmp').mkdir()
            (source / 'Inbox/tmp/partial').write_text('partial')
            module.backup(source, dest)
            first.unlink()
            second.write_bytes(b'new, longer body')
            module.backup(source, dest)
            self.assertEqual((dest / 'maildir/Inbox/cur/a:2,S').read_bytes(), b'original message')
            self.assertEqual((dest / 'maildir/Inbox/cur/b:2,S').read_bytes(), b'new, longer body')
            old = list((dest / 'versions').rglob('b:2,S'))
            self.assertEqual(len(old), 1)
            self.assertEqual(old[0].read_bytes(), b'old body')
            self.assertEqual(second.read_bytes(), b'new, longer body')
            self.assertFalse((dest / 'maildir/Inbox/.mbsyncstate').exists())
            self.assertFalse((dest / 'maildir/Inbox/tmp').exists())
            self.assertEqual((dest / 'maildir/Inbox/cur/b:2,S').stat().st_mode & 0o777, 0o600)

    def test_invalid_source_or_destination_refuses_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(RuntimeError):
                module.backup(root / 'missing', root / 'backup')
            (root / 'source/Inbox/cur').mkdir(parents=True)
            with self.assertRaises(RuntimeError):
                module.backup(root / 'source', root / 'source/nested')
            with self.assertRaises(RuntimeError):
                module.backup(root / 'source', root / 'source')
            (root / 'link').symlink_to(root / 'real')
            with self.assertRaises(RuntimeError):
                module.backup(root / 'source', root / 'link')
