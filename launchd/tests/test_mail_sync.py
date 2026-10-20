"""Preserve partial downloads and keep the two accounts independent."""
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch

loader = importlib.machinery.SourceFileLoader('mail_sync', str(Path(__file__).resolve().parents[1] / 'scripts/mail-sync'))
spec = importlib.util.spec_from_loader(loader.name, loader)
sync = importlib.util.module_from_spec(spec)
loader.exec_module(sync)


class MailSyncTests(unittest.TestCase):
    def test_failures_are_backed_up_and_other_account_continues(self):
        for failed_account in ('uu', 'gmail'):
            with self.subTest(account=failed_account), patch.object(sync, 'has_internet', return_value=True), \
                 patch.object(sync, 'davmail_running', return_value=True), \
                 patch.dict(os.environ, XDG_CACHE_DIR='/tmp/test-mail-cache'), \
                 patch.object(sync, 'run_cmd', side_effect=lambda args:
                              2 if args == [sync.MB_SYNC, failed_account] else 0) as run:
                self.assertEqual(sync.sync_accounts(), 2)
                calls = [c.args[0] for c in run.call_args_list]
                for account in ('gmail', 'uu'):
                    pos = calls.index([sync.MB_SYNC, account])
                    self.assertEqual(calls[pos-1], [sync.MAIL_BACKUP, '--account', account])
                    self.assertEqual(calls[pos+1], [sync.MAIL_BACKUP, '--account', account])
                self.assertEqual(sum(c[0] == sync.MU for c in calls), 1)
                self.assertEqual(sum(c[0] == sync.MAIL_NOTIFY for c in calls), 1)

    def test_gmail_notifies_before_uu_and_works_without_davmail(self):
        for running in (True, False):
            with self.subTest(davmail=running), patch.object(sync, 'has_internet', return_value=True), \
                 patch.object(sync, 'davmail_running', return_value=running), \
                 patch.dict(os.environ, XDG_CACHE_DIR='/tmp/test-mail-cache'), \
                 patch.object(sync, 'run_cmd', return_value=0) as run:
                self.assertEqual(sync.sync_accounts(), 0)
                calls = [c.args[0] for c in run.call_args_list]
                self.assertIn([sync.MB_SYNC, 'gmail'], calls)
                first_notice = next(i for i,c in enumerate(calls) if c[0] == sync.MAIL_NOTIFY)
                if running:
                    self.assertLess(first_notice, calls.index([sync.MB_SYNC, 'uu']))
                else:
                    self.assertNotIn([sync.MB_SYNC, 'uu'], calls)

    def test_backup_failure_blocks_that_account(self):
        with patch.object(sync, 'has_internet', return_value=True), \
             patch.object(sync, 'davmail_running', return_value=True), \
             patch.dict(os.environ, XDG_CACHE_DIR='/tmp/test-mail-cache'), \
             patch.object(sync, 'run_cmd', side_effect=lambda args:
                          1 if args == [sync.MAIL_BACKUP, '--account', 'uu'] else 0) as run:
            self.assertEqual(sync.sync_accounts(), 1)
            self.assertNotIn([sync.MB_SYNC, 'uu'], [c.args[0] for c in run.call_args_list])

    def test_error_details_are_retained_privately(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, XDG_CACHE_DIR=tmp), \
             patch.object(sync.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, stderr='Synthetic APPEND failure\n')):
            self.assertEqual(sync.run_cmd([sync.MB_SYNC, '-a']), 1)
            path = Path(tmp) / 'mail-sync/last-error.log'
            self.assertIn('Synthetic APPEND failure', path.read_text())
            self.assertIn('mbsync exited 1', path.read_text())
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
