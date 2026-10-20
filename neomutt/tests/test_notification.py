"""Notification tests never post notifications or open the user's mailbox."""
import importlib.machinery
import importlib.util
import io
import json
import os
import re
from pathlib import Path
import shlex
import subprocess
import tempfile
import threading
import time
import unittest
from email.message import EmailMessage
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def module(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    result = importlib.util.module_from_spec(spec)
    loader.exec_module(result)
    return result


popup = module('mail_popup', ROOT / 'neomutt/scripts/neomutt-notification')
notify = module('mail_notify', ROOT / 'launchd/scripts/mail-notify')


class NotificationTests(unittest.TestCase):
    def test_notification_action_preserves_arguments(self):
        message_id = "id'$(touch nope)@example.test"
        path = "/tmp/mail dir/cur/quote' file"
        with patch.object(notify.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as run:
            notify.notify([{':message-id': message_id, ':path': path, ':subject': 'Fixture',
                            ':maildir': '/gmail/Inbox'}])
        args = run.call_args.args[0]
        action = args[args.index('-execute') + 1]
        self.assertEqual(shlex.split(action), [notify.OPEN_MAIL, '--message-id', message_id,
                                              '--path', path, '--group', notify.group_key('gmail-' + message_id)])
        self.assertNotIn('-activate', args)

    def test_both_account_icons_and_query(self):
        messages = [{':message-id': 'id@example.test', ':maildir': '/' + account + '/Inbox'}
                    for account in ('uu', 'gmail')]
        with patch.object(notify.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as run:
            notify.notify(messages)
        work, gmail = [call.args[0] for call in run.call_args_list]
        self.assertIn('Work mail', work)
        self.assertIn(str(notify.ASSETS / 'work_icon.png'), work)
        self.assertIn('Gmail', gmail)
        self.assertIn(str(notify.ASSETS / 'gmail_icon.png'), gmail)
        self.assertNotEqual(work[work.index('-group') + 1], gmail[gmail.index('-group') + 1])
        from datetime import datetime
        with patch.object(notify.subprocess, 'run', return_value=subprocess.CompletedProcess([], 2, '')) as run, \
             patch.dict(os.environ, XDG_CACHE_DIR='/tmp/mail-test-cache'):
            self.assertEqual(notify.fetch_messages(datetime.now(), datetime.now()), [])
        self.assertIn('(maildir:/uu/Inbox OR maildir:/gmail/Inbox)', run.call_args.args[0][-1])
        self.assertIn('changed:', run.call_args.args[0][-1])
        self.assertNotIn('date:', run.call_args.args[0][-1])

    def test_baseline_and_uid_redownloads_do_not_repeat_notifications(self):
        existing = {':message-id': 'old@example.test', ':maildir': '/uu/Inbox'}
        delayed = {':message-id': 'delayed@example.test', ':maildir': '/uu/Inbox',
                   ':date': '2001-01-01'}
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, XDG_CACHE_DIR=tmp), \
             patch.object(notify, 'fetch_messages', return_value=[existing]) as fetch, \
             patch.object(notify.subprocess, 'run',
                          return_value=subprocess.CompletedProcess([], 0)) as run:
            self.assertEqual(notify.main(), 0)
            fetch.assert_called_once_with(None, None)
            run.assert_not_called()
            fetch.return_value = [existing, delayed, dict(delayed)]
            self.assertEqual(notify.main(), 0)
            self.assertEqual(run.call_count, 1)
            self.assertEqual(notify.main(), 0)
            self.assertEqual(run.call_count, 1)
            self.assertEqual(len(json.loads((Path(tmp) / 'mail-sync/notified.json').read_text())), 2)

    def test_failed_notification_keeps_checkpoint_and_retries(self):
        from datetime import datetime
        fixture = {':message-id': 'fixture@example.test', ':maildir': '/uu/Inbox'}
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, XDG_CACHE_DIR=tmp), \
             patch.object(notify, 'fetch_messages', return_value=[fixture]) as fetch, \
             patch.object(notify.subprocess, 'run',
                          return_value=subprocess.CompletedProcess([], 1)) as run:
            notify.save_notified(notify.cache_dir() / 'notified.json', set())
            checkpoint = datetime(2026, 1, 1)
            notify.write_last_run(checkpoint)
            self.assertEqual(notify.main(), 1)
            self.assertEqual(notify.load_last_run(), checkpoint)
            self.assertEqual(fetch.call_args.args[0], checkpoint)
            run.return_value = subprocess.CompletedProcess([], 0)
            self.assertEqual(notify.main(), 0)
            self.assertEqual(run.call_count, 2)
            self.assertGreater(notify.load_last_run(), checkpoint)

    def test_notification_text_escapes_property_list_and_option_prefixes(self):
        for value in ('[List] Subject', '(no subject)', '{Reminder}', '"Quoted"',
                      '<Angle>', '-starts-with-dash', r'\literal', 'Ordinary text'):
            with self.subTest(value=value), \
                 patch.object(notify, 'format_sender', return_value=value), \
                 patch.object(notify.subprocess, 'run',
                              return_value=subprocess.CompletedProcess([], 0)) as run:
                message = {':subject': value, ':maildir': '/uu/Inbox',
                           ':message-id': 'fixture@example.test'}
                self.assertEqual(notify.notify([message]), {notify.notification_key(message)})
                args = run.call_args.args[0]
                self.assertEqual(args[args.index('-message') + 1], '\\' + value)
                self.assertEqual(args[args.index('-subtitle') + 1], '\\' + value)

    def test_notifier_failure_reports_the_reason_without_debug(self):
        with patch.object(notify, 'DEBUG', False), \
             patch.object(notify.subprocess, 'run', return_value=subprocess.CompletedProcess(
                 [], 1, stderr='Could not read the -message value.\n')), \
             patch('sys.stderr', new_callable=io.StringIO) as stderr:
            self.assertEqual(notify.notify([{':message-id': 'fixture@example.test',
                                            ':maildir': '/uu/Inbox'}]), set())
            self.assertIn('terminal-notifier exited 1 (uu)', stderr.getvalue())
            self.assertIn('Could not read the -message value.', stderr.getvalue())

    def test_seen_rename_found_but_archived_deleted_and_wrong_ids_ignored(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(popup.Path, 'home', return_value=Path(tmp)):
            for account in ('uu', 'gmail'):
                inbox = Path(tmp) / '.mail' / account / 'Inbox'
                for sub in ('cur', 'new'):
                    (inbox / sub).mkdir(parents=True)
                original = inbox / 'new' / 'fixture[1]'
                original.write_text('Message-ID: <fixture@example.test>\n\nOnly synthetic mail.\n')
                self.assertEqual(popup.inbox_message('fixture@example.test', str(original)), original)
                renamed = inbox / 'cur' / 'fixture[1]:2,S'
                original.rename(renamed)
                self.assertEqual(popup.inbox_message('fixture@example.test', str(original)), renamed)
                self.assertIsNone(popup.inbox_message('wrong@example.test', str(original)))
                deleted = renamed.with_name('fixture[1]:2,ST')
                renamed.rename(deleted)
                self.assertIsNone(popup.inbox_message('fixture@example.test', str(original)))
                deleted.rename(Path(tmp) / 'archived')
                self.assertIsNone(popup.inbox_message('fixture@example.test', str(original)))
                # An inbox symlink to an archived message is not an inbox copy.
                original.symlink_to(Path(tmp) / 'archived')
                self.assertIsNone(popup.inbox_message('fixture@example.test', str(original)))
                (Path(tmp) / 'archived').unlink()

    def test_stale_click_only_removes_notification(self):
        with patch('sys.argv', ['notification', '--message-id', 'gone@example.test',
                                '--path', '/tmp/missing/cur/mail', '--group', 'test-group']), \
             patch.object(popup.subprocess, 'run') as run, patch.object(popup, 'clients') as clients:
            self.assertEqual(popup.main(), 0)
        self.assertEqual(run.call_args.args[0], [popup.NOTIFIER, '-remove', 'test-group'])
        self.assertEqual(run.call_count, 1)
        clients.assert_not_called()

    def test_maildir_selection_and_missing_path(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / 'Other mailbox'
            (folder / 'cur').mkdir(parents=True)
            message = folder / 'cur/message'
            message.touch()
            self.assertEqual(popup.mail_command('', str(message))[:3], [popup.NEOMUTT, '-f', str(folder)])
        self.assertEqual(popup.mail_command('', str(message))[2], popup.UU_INBOX)

    def test_work_notification_uses_live_imap_folder(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(popup.Path, 'home', return_value=Path(temp)):
            folder = Path(temp) / '.mail/uu/Inbox/cur'
            folder.mkdir(parents=True)
            path = folder / 'message'
            path.touch()
            self.assertEqual(popup.mail_command('', str(path))[2], popup.UU_INBOX)

    def test_work_presence_is_read_only_and_matches_exact_id(self):
        from unittest.mock import MagicMock
        client = MagicMock()
        client.select.return_value = ('OK', [b'2'])
        # Old Python's structured header parser crashes on this malformed ID.
        client.uid.return_value = ('OK', [
            (b'1 (BODY[] {37}', b'Message-ID: <[broken@example.test]>\r\n\r\n'),
            (b'2 (BODY[] {37}', b'Message-ID: <fixture@example.test>\r\n\r\n'),
        ])
        with patch.object(popup.imaplib, 'IMAP4', return_value=client), \
             patch.object(popup.subprocess, 'check_output', return_value='synthetic-password'):
            self.assertTrue(popup.work_message_present('fixture@example.test'))
            self.assertFalse(popup.work_message_present('another@example.test'))
        client.select.assert_called_with('INBOX', readonly=True)
        client.uid.assert_called_with('FETCH', '1:*', '(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])')
        client.logout.assert_called()

    def test_invalid_ids_cannot_inject_keys(self):
        for message_id in ('x<enter><shell-escape>bad', 'x\ny', 'x\x1by', 'x\x7fy'):
            self.assertFalse(any(arg.startswith('push ') for arg in popup.mail_command(message_id)))

    def test_html_body_selection(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'message'
            message = EmailMessage()
            message['Message-ID'] = '<fixture@example.test>'
            message.set_content('Plain fallback')
            path.write_bytes(message.as_bytes())
            self.assertFalse(popup.has_html_body(path, 'fixture@example.test'))
            message.add_alternative('<p>HTML body</p>', subtype='html')
            path.write_bytes(message.as_bytes())
            self.assertTrue(popup.has_html_body(path, 'fixture@example.test'))
            self.assertFalse(popup.has_html_body(path, 'other@example.test'))
            self.assertTrue(popup.mail_command('fixture@example.test', str(path))[-1].endswith('H"'))
            message.get_payload()[1]['Content-Disposition'] = 'attachment; filename="page.html"'
            path.write_bytes(message.as_bytes())
            self.assertFalse(popup.has_html_body(path, 'fixture@example.test'))
            path.unlink()
            self.assertFalse(popup.has_html_body(path, 'fixture@example.test'))

    def test_client_selection_prefers_recent_attached_terminal(self):
        result = subprocess.CompletedProcess([], 0, '10\t/dev/ttys1\n30\t/dev/ttys2\nno\tbad\n')
        with patch.object(popup.subprocess, 'run', return_value=result):
            self.assertEqual(popup.clients(), [(30, '/dev/ttys2'), (10, '/dev/ttys1')])


class NotificationWindowIntegration(unittest.TestCase):
    def test_exact_message_opens_and_one_q_returns(self):
        self.check_popup('fixture@example.test')

    def test_shell_and_regex_characters_in_message_id(self):
        self.check_popup("id.'+cash$back`tick@example.test")

    def test_html_images_and_one_q_returns(self):
        self.check_popup('html@example.test', html=True)

    def check_popup(self, message_id, html=False):
        # Reuse only the synthetic mailbox/isolated terminal fixture.
        from test_save_integration import SaveIntegration
        fixture = SaveIntegration('test_bulk_preselected_and_numbered')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.tmux('respawn-pane', '-k', 'sleep 60')
        previous_window = fixture.tmux('display-message', '-p', '#{window_id}')
        import fcntl, struct, termios
        fcntl.ioctl(fixture.master, termios.TIOCSWINSZ, struct.pack('HHHH', 35, 120, 1200, 700))
        fixture.tmux('set-option', '-as', 'terminal-features', ',xterm-256color:sixel:RGB')
        fixture.drain()
        os.write(fixture.master, b'\x1b[?64;1;2;4;6;9;15;18;21;22c')
        tmux = fixture.root / 'tmux-fixture'
        tmux.write_text('#!/bin/sh\nexec ' + shlex.join(fixture.base) + ' "$@"\n')
        tmux.chmod(0o755)
        neomutt = fixture.root / 'mail-fixture'
        neomutt.write_text('#!/bin/sh\nexec ' + shlex.join([
            '/opt/homebrew/bin/neomutt', '-n', '-F', str(fixture.root / 'muttrc'), '-R'
        ]) + ' "$@"\n')
        neomutt.chmod(0o755)
        message = next((fixture.home / 'mail/new').iterdir())
        inbox = fixture.home / '.mail/uu/Inbox'
        inbox.parent.mkdir(parents=True)
        inbox.symlink_to(fixture.home / 'mail', target_is_directory=True)
        message = inbox / 'new' / message.name
        message.write_bytes(message.read_bytes().replace(b'fixture@example.test', message_id.encode()))
        if html:
            (fixture.home / '.config/neomutt').symlink_to(ROOT / 'neomutt', target_is_directory=True)
            content = EmailMessage()
            content['From'] = 'Fixture <fixture@example.test>'
            content['Subject'] = 'Synthetic HTML notification'
            content['Message-ID'] = '<' + message_id + '>'
            content.set_content('Only synthetic mail.')
            content.add_alternative('<title>Notification HTML</title><h1>HTML notification preview</h1><img src="cid:pic@test" width="64" height="64">', subtype='html')
            import base64
            png = base64.b64decode(re.search(r'base64,([^"\s]+)', (ROOT / 'chawan/test.html').read_text())[1])
            content.get_payload()[1].add_related(png, maintype='image', subtype='png', cid='<pic@test>')
            message.write_bytes(content.as_bytes())
            self.assertTrue(popup.has_html_body(message, message_id))
            chawan = fixture.home / '.config/chawan'
            chawan.mkdir()
            (chawan / 'config.toml').write_text((ROOT / 'chawan/config.toml').read_text())
            with (fixture.root / 'muttrc').open('a') as rc:
                rc.write('\nset attach_format="%n %t %m/%M %f"\n')
                rc.write('\nset mailcap_path=' + popup.mutt_quote(str(ROOT / 'neomutt/core/mailcap')) + '\n')
                # Read the real H macro so the test follows the production flow.
                rc.write(next(line for line in (ROOT / 'neomutt/core/mappings').read_text().splitlines(True)
                              if 'View HTML in Chawan' in line))
        other = EmailMessage()
        other['From'] = 'Fixture <fixture@example.test>'
        other['Subject'] = 'A different message'
        other['Message-ID'] = '<fixture@exampleXtest>'
        other['Date'] = 'Mon, 1 Jan 2001 00:00:00 +0000'
        other.set_content('Wrong message: regex metacharacters must stay literal.')
        (fixture.home / 'mail/new/unrelated').write_bytes(other.as_bytes())
        with (fixture.root / 'muttrc').open('a') as rc:
            rc.write('\nset sort=subject\n')
        real_run = subprocess.run
        def run(args, **kwargs):
            if args[:1] == ['/usr/bin/open']:
                return subprocess.CompletedProcess(args, 0)
            return real_run(args, **kwargs)
        result = []
        with patch.dict(os.environ, fixture.env), patch.object(popup, 'TMUX', str(tmux)), \
             patch.object(popup, 'UU_INBOX', str(inbox)), \
             patch.object(popup, 'work_message_present', return_value=True), \
             patch.object(popup, 'NEOMUTT', str(neomutt)), patch.object(popup.subprocess, 'run', side_effect=run), \
             patch('sys.argv', ['popup', '--message-id', '<' + message_id + '>', '--path', str(message)]):
            worker = threading.Thread(target=lambda: result.append(popup.main()), daemon=True)
            worker.start()
            output = b''
            deadline = time.monotonic() + 10
            import select
            expected = b'HTML notification preview' if html else b'Only synthetic mail.'
            def ready():
                return expected in output and (not html or re.search(rb'\x1bP[0-9;]*q', output))
            while time.monotonic() < deadline and not ready():
                if select.select([fixture.master], [], [], .1)[0]:
                    data = os.read(fixture.master, 65536)
                    output += data
                    for query, reply in {
                        b'\x1b[c': b'\x1b[?64;1;2;4;6;9;15;18;21;22c',
                        b'\x1b[>c': b'\x1b[>0;10;1c',
                        b'\x1b[>0c': b'\x1b[>0;10;1c',
                        b'\x1b[6n': b'\x1b[24;80R',
                        b'\x1b[14t': b'\x1b[4;700;1200t',
                        b'\x1b[16t': b'\x1b[6;20;10t',
                        b'\x1b]10;?\x1b\\': b'\x1b]10;rgb:abab/b2b2/bfbf\x1b\\',
                        b'\x1b]11;?\x1b\\': b'\x1b]11;rgb:1e1e/1e1e/1e1e\x1b\\',
                    }.items():
                        if query in data:
                            os.write(fixture.master, reply)
            self.assertTrue(expected in output, re.sub(r'\x1b(?:\[[0-?]*[ -/]*[@-~]|\([A-Z])', '', output.decode(errors='replace'))[-500:])
            if html:
                self.assertRegex(output, rb'\x1bP[0-9;]*q', 'Expected actual Sixel image output through tmux')
            self.assertNotEqual(fixture.tmux('display-message', '-p', '#{window_id}'), previous_window)
            os.write(fixture.master, b'q')
            fixture.wait(lambda: fixture.tmux('list-windows', '-F', '#{window_id}') == previous_window, 'single-key close')
            self.assertEqual(fixture.tmux('display-message', '-p', '#{window_id}'), previous_window)
            worker.join(3)
            self.assertNotIn(b'Wrong message:', output)
            self.assertEqual(result, [0])


if __name__ == '__main__':
    unittest.main()
