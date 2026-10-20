"""Actual NeoMutt/Chawan mode switching and attachment handoff with fake mail."""
from email.message import EmailMessage
import os
from pathlib import Path
import json
import re
import select
import shlex
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlparse

import test_html
from test_notification import module

display = module('mail_display', test_html.ROOT / 'neomutt/scripts/mail-display')


class FirefoxExportTests(unittest.TestCase):
    def test_browser_copy_keeps_html_and_embedded_images_after_reader_closes(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch.dict(os.environ, XDG_CACHE_DIR=tmp), \
             patch.object(test_html.viewer.subprocess, 'run') as run:
            message = EmailMessage()
            message.set_content('Plain text')
            markup = '<p style="color:red">Original HTML</p><img src="cid:fixture@test">'
            message.add_alternative(markup, subtype='html')
            message.get_payload()[1].add_related(b'fixture image', maintype='image',
                                                subtype='png', cid='<fixture@test>')
            original = message.as_bytes()
            with tempfile.TemporaryDirectory(dir=tmp) as assets:
                path = Path(assets) / 'message.html'
                path.write_text(test_html.viewer.message_html(message, Path(assets)))
                test_html.viewer.open_firefox(path)
                target = Path(unquote(urlparse(run.call_args.args[0][-1]).path))
                test_html.viewer.open_firefox(path)
                self.assertEqual(Path(unquote(urlparse(run.call_args.args[0][-1]).path)), target)
            self.assertTrue(target.is_file())
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            content = target.read_text()
            self.assertIn('<p style="color:red">Original HTML</p>', content)
            self.assertIn('data:image/png;base64,Zml4dHVyZSBpbWFnZQ==', content)
            self.assertNotIn(Path(assets).as_uri(), content)
            self.assertIn('Content-Security-Policy', content)
            self.assertEqual(message.as_bytes(), original)
            self.assertEqual(run.call_args.args[0][:3], ['open', '-a', 'Firefox'])


class TextLayoutTests(unittest.TestCase):
    def test_width_quotes_unicode_and_mime_markers(self):
        marker = '\x1b]9;12345\x07'
        text = ('From: Fixture <fixture@example.test>\n\n' + marker + '[-- Attachment #1 --]\n'
                + '> ' + 'A quoted sentence. ' * 12 + '\n'
                + '日本語 e\u0301 ' * 30 + '\n')
        for columns in (40, 80, 120, 180):
            with self.subTest(columns=columns):
                lines = list(display.display(text, columns))
                margin = (columns - min(80, columns - 4)) // 2
                self.assertTrue(lines[0].startswith(' ' * margin + 'From:'))
                self.assertEqual(lines[2], marker + ' ' * margin + '[-- Attachment #1 --]')
                for line in lines:
                    visible = display.MARKER.sub('', line)
                    self.assertLessEqual(sum(map(display.cells, visible)), columns - margin)
                quotes = [line.strip() for line in lines if line.strip().startswith('>')]
                self.assertEqual(' '.join(line[2:] for line in quotes), ('A quoted sentence. ' * 12).strip())
                self.assertEqual(''.join(lines).count('日本語'), 30)

    def test_long_unbroken_text_is_not_dropped(self):
        text = 'https://example.test/' + 'x' * 300
        lines = list(display.display(text, 60))
        self.assertEqual(''.join(line.strip() for line in lines), text)


class ReaderStyleTests(unittest.TestCase):
    def test_centered_column_overrides_mobile_wrappers_and_preserves_tables(self):
        sentence = ('A readable message should have a comfortable line length and '
                    'consistent left alignment instead of looking like a narrow phone screen. ')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'fixture.html'
            original = ('''<style>
                @media (max-width: 2000px) {
                  .mobile { width: 180px !important; text-align: center !important; }
                }
                .hidden { display: none; }
                </style><table role="presentation" width="600"><tr><td style="padding:50px">
                <div class="mobile"><p>''' + sentence * 3 + '''</p></div>
                <span class="hidden">HIDDEN PREHEADER</span>
                <table><tr><th>Left</th><th>Right</th></tr><tr><td>One</td><td>Two</td></tr></table>
                <a href="https://example.test">LINK</a></td></tr></table>''')
            path.write_text(original)
            for columns, margin in ((60, 2), (120, 20), (180, 50)):
                with self.subTest(columns=columns):
                    result = subprocess.run(
                        ['cha', '-C', '/dev/null', '-d', '-I', 'utf-8', '-T', 'text/html',
                         '-o', 'buffer.history=false', '-o', f'display.columns={columns}',
                         '-o', 'buffer.user-style=' + json.dumps((test_html.ROOT / 'chawan/mail.css').read_text()),
                         str(path)], text=True, capture_output=True, check=True)
                    plain = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)
                    lines = plain.splitlines()
                    first = next(line for line in lines if 'A readable message' in line)
                    self.assertEqual(len(first) - len(first.lstrip()), margin)
                    self.assertGreater(len(first.strip()), 50)
                    self.assertTrue(all(len(line.rstrip()) <= columns - margin for line in lines))
                    self.assertRegex(plain, r'Left +Right')
                    self.assertRegex(plain, r'One +Two')
                    self.assertNotIn('HIDDEN PREHEADER', plain)
                    self.assertIn('LINK', plain)
                    self.assertEqual(path.read_text(), original)

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

    def capture_browser(self):
        directory = self.f.root / 'browser-bin'
        directory.mkdir()
        log = self.f.root / 'browser.jsonl'
        opener = directory / 'open'
        opener.write_text('#!/usr/bin/python3\nimport json,sys\n'
                          + 'with open(' + repr(str(log)) + ', "a") as out:\n'
                          + ' out.write(json.dumps(sys.argv[1:])+"\\n")\n')
        opener.chmod(0o755)
        path = str(directory) + ':' + self.f.env['PATH']
        self.context.command = 'env PATH=' + shlex.quote(path) + ' ' + self.context.command
        return log

    def test_chawan_links_and_whole_message_open_in_firefox(self):
        log = self.capture_browser()
        url = "https://example.test/path?x='quote'&y=$(touch%20never)&z=`literal`"
        message = EmailMessage()
        message['From'] = 'Fixture <fixture@example.test>'
        message['Subject'] = 'Browser link fixture'
        message.set_content('Only synthetic mail')
        from html import escape
        message.add_alternative('<p>FIREFOX MAIL MARKER</p><a href="' + escape(url, quote=True)
                                + '">Open link</a><p><a href="#anchor">Local anchor</a></p>'
                                + '<p id="anchor">Anchor destination</p>', subtype='html')
        (self.f.home / 'mail/new/fixture').write_bytes(message.as_bytes())
        self.f.tmux('respawn-pane', '-k', self.context.command)
        self.wait('Browser link fixture')
        self.f.keys('Enter')
        self.wait('FIREFOX MAIL MARKER')
        self.f.keys(']')
        self.wait('Viewing> https://example.test/')
        self.f.keys('Enter')
        self.f.wait(log.exists, 'Firefox link launch')
        calls = [json.loads(line) for line in log.read_text().splitlines()]
        self.assertEqual(calls, [['-a', 'Firefox', url.replace("'", '%27')]])
        self.assertIn('FIREFOX MAIL MARKER', self.f.screen())
        screen = subprocess.check_output(self.f.base + ['capture-pane', '-p'],
                                         env=self.f.env, text=True)
        y, row = next((y, row) for y, row in enumerate(screen.splitlines()) if 'Open link' in row)
        x = row.index('Open link')
        os.write(self.f.master, f'\x1b[<0;{x+1};{y+1}M\x1b[<0;{x+1};{y+1}m'.encode())
        self.f.wait(lambda: len(log.read_text().splitlines()) == 2, 'mouse link launch')
        self.assertEqual(json.loads(log.read_text().splitlines()[-1]), calls[0])
        self.f.keys('B')
        self.f.wait(lambda: len(log.read_text().splitlines()) == 3, 'Firefox whole-message launch')
        target = Path(unquote(urlparse(json.loads(log.read_text().splitlines()[-1])[-1]).path))
        self.assertIn('FIREFOX MAIL MARKER', target.read_text())
        self.assertIn('FIREFOX MAIL MARKER', self.f.screen())
        self.f.keys(']')
        self.wait('file:///')
        self.f.keys('Enter')
        self.wait('Anchor destination')
        self.assertEqual(len(log.read_text().splitlines()), 3)
        self.f.keys('q')
        self.wait('Browser link fixture')
        self.assertTrue(target.is_file(), 'Browser copy must outlive the terminal preview')

    def test_B_opens_firefox_from_index_and_text_pager(self):
        log = self.capture_browser()
        path = self.f.home / 'mail/new/fixture'
        path.write_bytes(path.read_bytes().replace(b'Synthetic attachment fixture', b'Browser shortcut fixture'))
        self.f.tmux('respawn-pane', '-k', self.context.command)
        self.wait('Browser shortcut fixture')
        self.f.keys('B')
        self.f.wait(log.exists, 'index browser launch')
        self.assertIn('Browser shortcut fixture', self.f.screen())
        self.f.keys('H')
        self.wait('HTML VIEW MARKER')
        self.f.keys('B')
        self.f.wait(lambda: len(log.read_text().splitlines()) == 2, 'pager browser launch')
        for line in log.read_text().splitlines():
            call = json.loads(line)
            self.assertEqual(call[:2], ['-a', 'Firefox'])
            self.assertIn('HTML VIEW MARKER', Path(unquote(urlparse(call[-1]).path)).read_text())

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

    def test_pager_column_with_and_without_sidebar(self):
        self.f.tmux('resize-window', '-x', '120', '-y', '35')
        self.f.keys('H')
        self.wait('HTML VIEW MARKER')
        screen = self.f.tmux('capture-pane', '-p')
        line = next(line for line in screen.splitlines() if 'HTML VIEW MARKER' in line)
        self.assertEqual(line.index('HTML VIEW MARKER'), 20)
        self.f.keys('q')
        self.wait('Synthetic attachment fixture')
        # A 20-column sidebar leaves a 100-column pager, with 10-column margins.
        self.f.keys(':set sidebar_visible=yes', 'Enter', 'H')
        self.wait('HTML VIEW MARKER')
        screen = self.f.tmux('capture-pane', '-p')
        line = next(line for line in screen.splitlines() if 'HTML VIEW MARKER' in line)
        self.assertEqual(line.index('HTML VIEW MARKER'), 30)
        self.f.tmux('resize-window', '-x', '60', '-y', '35')
        time.sleep(.2)  # Let curses process SIGWINCH before sending the next key.
        self.f.keys('C-l')
        self.f.wait(
            lambda: any(line.index('HTML VIEW MARKER') == 22
                        for line in self.f.screen().splitlines() if 'HTML VIEW MARKER' in line),
            'recentered narrow pager')

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

    def check_reply_view(self, keys, initial_html, views):
        # A deterministic plain editor keeps the quoted text and adds literal
        # Markdown. HTML replies continue through the existing Markdown editor.
        editor = self.f.root / 'plain-editor'
        editor.write_text('#!/usr/bin/python3\nfrom pathlib import Path\nimport sys\n'
                          'p = Path(sys.argv[-1])\n'
                          'headers, _, body = p.read_text().partition("\\n\\n")\n'
                          'p.write_text(headers + "\\n\\nPlain **reply**.\\n\\n" + body)\n')
        editor.chmod(0o755)
        settings = self.f.home / '.config/neomutt/core/settings'
        settings.write_text(settings.read_text().replace('= "nvim"', '= "' + str(editor) + '"'))
        path = self.f.home / 'mail/new/fixture'
        original = test_html.BytesParser(policy=test_html.policy.default).parsebytes(path.read_bytes())
        original.replace_header('Subject', 'Reply format fixture')
        original['To'] = 'sender@example.test'
        original['Cc'] = 'colleague@example.test'
        original['Message-ID'] = '<reply-view@example.test>'
        path.write_bytes(original.as_bytes())
        if not initial_html:
            with (self.f.root / 'html.rc').open('a') as rc:
                rc.write('source ~/.config/neomutt/dynamic/html_off\n')
        self.f.tmux('respawn-pane', '-k', self.context.command)
        self.wait('Reply format fixture')
        for key, html in views:
            self.f.keys(key)
            self.wait('Viewing <file://' if html else 'HTML VIEW MARKER')
        self.f.keys(keys)
        self.wait('Size:')
        message = self.context.send()  # Transport writes a local file only.
        self.assertEqual(message['In-Reply-To'], '<reply-view@example.test>')
        self.assertIn('fixture@example.test', str(message['To']))
        if keys == 'ca':
            self.assertIn('colleague@example.test', str(message['To']) + str(message['Cc']))
        if views[-1][1]:
            self.assertEqual(message.get_content_type(), 'multipart/alternative')
            self.assertIn('<strong>world</strong>', message.get_body(('html',)).get_content())
            self.assertIn('HTML VIEW MARKER', message.get_body(('html',)).get_content())
            self.assertTrue(test_html.composer.load(self.context.draft())['valid'])
        else:
            self.assertEqual(message.get_content_type(), 'text/plain')
            self.assertIn('Plain **reply**.', message.get_content())
            self.assertIn('HTML VIEW MARKER', message.get_content())
            self.assertFalse((self.f.home / '.cache/neomutt-html').exists())

    def test_html_reply_from_text_mode(self):
        self.check_reply_view('cr', initial_html=False, views=[('H', True)])

    def test_html_reply_all_from_text_pager(self):
        self.check_reply_view('ca', initial_html=False, views=[('Enter', False), ('H', True)])

    def test_text_reply_from_html_mode(self):
        self.check_reply_view('cr', initial_html=True, views=[('H', False)])

    def test_text_reply_all_after_leaving_chawan(self):
        self.check_reply_view('ca', initial_html=True, views=[('Enter', True), ('H', False)])

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
