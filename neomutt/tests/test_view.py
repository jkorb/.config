"""Actual NeoMutt/Chawan mode switching and attachment handoff with fake mail."""
from email.message import EmailMessage
import os
from pathlib import Path
import json
import select
import subprocess
import tempfile
import time
import unittest

import test_html


class ReaderStyleTests(unittest.TestCase):
    def test_mail_palette_and_math_annotation_are_view_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'fixture.html'
            original = '<body bgcolor="white"><p style="color:red">Readable text <a href="https://example.test">LINK</a></p><math><semantics><mi>∀</mi><annotation encoding="application/x-tex">HIDDEN LATEX</annotation></semantics></math></body>'
            path.write_text(original)
            css = (test_html.ROOT / 'chawan/mail.css').read_text()
            result = subprocess.run(['cha', '-d', '-I', 'utf-8', '-T', 'text/html',
                                     '-o', 'buffer.history=false', '-o', 'display.color-mode="true-color"',
                                     '-o', 'buffer.user-style=' + json.dumps(css), str(path)],
                                    text=True, capture_output=True, check=True)
            self.assertIn('\x1b[38;2;171;178;191m', result.stdout)
            self.assertIn('\x1b[38;2;66;179;194mLINK', result.stdout)
            self.assertIn('∀', result.stdout)
            self.assertNotIn('HIDDEN LATEX', result.stdout)
            self.assertEqual(path.read_text(), original)


class ViewerIntegration(unittest.TestCase):
    def setUp(self):
        self.context = test_html.HtmlIntegration('test_markdown_alternatives_and_editing')
        self.context.setUp()
        self.addCleanup(self.context.doCleanups)
        self.f = self.context.fixture
        message = EmailMessage()
        message['From'] = 'Fixture <fixture@example.test>'
        message['Subject'] = 'Synthetic attachment fixture'
        message.set_content('TEXT VIEW MARKER')
        message.add_alternative('<h1>HTML VIEW MARKER</h1><p>HTML body.</p>', subtype='html')
        message.add_attachment(b'fake PDF', maintype='application', subtype='pdf', filename='fixture.pdf')
        (self.f.home / 'mail/new/fixture').write_bytes(message.as_bytes())
        self.f.tmux('respawn-pane', '-k', self.context.command)
        self.f.wait(lambda: 'Synthetic attachment fixture' in self.f.screen(), 'reader index')

    def pump(self):
        while select.select([self.f.master], [], [], 0)[0]:
            data = os.read(self.f.master, 65536)
            for query, answer in {
                b'\x1b[c': b'\x1b[?64;1;2;6;9;15;18;21;22c',
                b'\x1b[>c': b'\x1b[>0;10;1c', b'\x1b[>0c': b'\x1b[>0;10;1c',
                b'\x1b[6n': b'\x1b[24;80R',
                b'\x1b]10;?\x1b\\': b'\x1b]10;rgb:abab/b2b2/bfbf\x1b\\',
                b'\x1b]11;?\x1b\\': b'\x1b]11;rgb:1e1e/1e1e/1e1e\x1b\\',
            }.items():
                if query in data:
                    os.write(self.f.master, answer)

    def wait(self, text):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            self.pump()
            if text in self.f.tmux('capture-pane', '-p'):
                return
            time.sleep(.03)
        self.fail(self.f.tmux('capture-pane', '-p', '-S', '-40'))

    def test_html_A_opens_neomutt_attachments(self):
        self.f.keys('Enter')
        self.wait('Viewing <file://')
        self.f.keys('A')
        self.wait('fixture.pdf')
        self.assertIn('Attachments', self.f.screen())

    def test_both_modes_and_H(self):
        # HTML mode: H opens full-pane native text, whose H opens Chawan.
        self.f.keys('H')
        self.wait('HTML VIEW MARKER')
        self.assertNotIn('From:                    Subject:', self.f.screen())
        self.f.keys('H')
        self.wait('Viewing <file://')
        self.f.keys('H')
        self.wait('Fixture')
        self.f.keys('q')
        self.wait('Synthetic attachment fixture')
        self.f.keys('gh')
        self.f.keys('Enter')
        self.wait('HTML VIEW MARKER')
        self.f.keys('A')
        self.wait('fixture.pdf')

    def test_preview_is_repeatable_and_does_not_attach_parts(self):
        self.context.compose()
        for _ in range(2):
            self.f.keys('ch')
            self.wait('Viewing <file://')
            self.f.keys('q')
            self.wait('Size:')
            self.assertFalse(test_html.composer.load(self.context.draft())['prepared'])
        message = self.context.send()
        self.assertEqual(message.get_content_type(), 'multipart/alternative')
        self.assertEqual(len(list(message.walk())), 3)

    def test_reply_shortcut_from_html_opens_normal_composer(self):
        self.f.keys('Enter')
        self.wait('Viewing <file://')
        self.f.keys('cr')
        self.wait('Size:')
        self.assertEqual(test_html.composer.load(self.context.draft())['kind'], 'reply')
        message = self.context.send()
        self.assertIn('fixture@example.test', str(message['To']))
        self.assertIn('HTML VIEW MARKER', message.get_body(('html',)).get_content())

    def check_account_archive(self, account, html):
        archive = self.f.home / '.mail' / account / ('All Mail' if account == 'gmail' else 'Archive')
        for folder in ('cur', 'new', 'tmp'):
            (archive / folder).mkdir(parents=True, exist_ok=True)
            (archive.parent / 'Trash' / folder).mkdir(parents=True, exist_ok=True)
        account_file = self.f.home / '.config/neomutt/accounts' / (account + '.conf')
        account_text = (test_html.ROOT / 'neomutt/accounts' / account_file.name).read_text()
        if account == 'uu':
            account_text = account_text.replace('$my_uu_folder', str(self.f.home / '.mail/uu'))
        account_file.write_text(account_text)
        with (self.f.root / 'html.rc').open('a') as rc:
            rc.write('\nsource "' + str(account_file) + '"\n')
            rc.write('set folder="' + str(self.f.home / '.mail') + '" confirmappend=no confirmcreate=no delete=yes\n')
            if not html:
                rc.write('source ~/.config/neomutt/dynamic/html_off\n')
        self.f.tmux('respawn-pane', '-k', self.context.command)
        self.wait('Synthetic attachment fixture')
        # Sidebar exit used to lose sa even though the account was still active.
        self.f.keys('Tab')
        time.sleep(.1)
        self.f.keys('Tab')
        time.sleep(.1)
        self.f.keys('Enter')
        self.wait('Viewing <file://' if html else 'HTML VIEW MARKER')
        self.f.keys('sa')
        self.f.wait(lambda: len(list(archive.glob('cur/*'))) + len(list(archive.glob('new/*'))) == 1, 'archived fixture')
        self.f.wait(lambda: not list((self.f.home / 'mail/cur').iterdir()) and not list((self.f.home / 'mail/new').iterdir()), 'original removed after safe archive')

    def test_archive_work_html_after_sidebar(self):
        self.check_account_archive('uu', html=True)

    def test_archive_work_text_after_sidebar(self):
        self.check_account_archive('uu', html=False)

    def test_archive_gmail_html_after_sidebar(self):
        self.check_account_archive('gmail', html=True)

    def test_archive_gmail_text_after_sidebar(self):
        self.check_account_archive('gmail', html=False)


if __name__ == '__main__':
    unittest.main()
