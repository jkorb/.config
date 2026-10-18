"""HTML conversion and real compose tests; delivery is always a local test file."""
import contextlib
import io
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import time
import unittest
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from unittest.mock import patch

from test_notification import module
import test_save_integration as fixtures

ROOT = Path(__file__).resolve().parents[2]
composer = module('html_compose', ROOT / 'neomutt/scripts/neomutt-html')
viewer = module('html_view', ROOT / 'neomutt/scripts/neomutt-view')


class HtmlIntegration(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.SaveIntegration('test_bulk_preselected_and_numbered')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f = self.fixture
        config = f.home / '.config/neomutt'
        config.mkdir()
        for name in ('core', 'dynamic', 'scripts'):
            (config / name).symlink_to(ROOT / 'neomutt' / name, target_is_directory=True)
        (config / 'accounts').mkdir()
        (f.home / '.config/chawan').symlink_to(ROOT / 'chawan', target_is_directory=True)
        for folder in re.findall(r"named-mailboxes.*?'\+([^']+)'", (ROOT / 'neomutt/core/settings').read_text()):
            for sub in ('cur', 'new', 'tmp'):
                (f.home / '.mail' / folder / sub).mkdir(parents=True, exist_ok=True)
        self.outbox = f.root / 'sent.eml'
        self.fail_send = f.root / 'fail-send'
        transport = f.root / 'capture-send'
        transport.write_text('#!/usr/bin/python3\nimport sys\nfrom pathlib import Path\ndata=sys.stdin.buffer.read()\n'
                             + 'Path(' + repr(str(self.outbox)) + ').write_bytes(data)\n'
                             + 'sys.exit(1 if Path(' + repr(str(self.fail_send)) + ').exists() else 0)\n')
        transport.chmod(0o755)
        self.body = f.root / 'edit-body'
        self.body.write_text('Hello **world**.\nA soft line break.\n\n- One\n- Two\n')
        editor = f.root / 'edit-fixture'
        editor.write_text('''#!/usr/bin/python3
from pathlib import Path
import sys
p=Path(sys.argv[-1]);headers,_,body=p.read_text().partition('\\n\\n')
lines=headers.splitlines()
for n,line in enumerate(lines):
 if line.startswith('To:') and not line[3:].strip(): lines[n]='To: recipient@example.test'
 if line.startswith('Subject:') and not line[8:].strip(): lines[n]='Subject: Fixture'
headers='\\n'.join(lines)
markers=[body.index(m) for m in ['<!-- neomutt-signature -->','<!-- neomutt-quote -->'] if m in body]
body=body[min(markers):] if markers else ''
new=Path(''' + repr(str(self.body)) + ''').read_text()
p.write_text(headers+'\\n\\n'+new+'\\n'+body)
''')
        editor.chmod(0o755)
        self.document = f.root / 'user-document.pdf'
        self.document.write_bytes(b'untouched existing attachment')
        f.env['NEOMUTT_MARKDOWN_EDITOR'] = str(editor)
        rc = f.root / 'html.rc'
        rc.write_text('source ' + str(ROOT / 'neomutt/core/mappings') + '\n'
                      + 'source ' + str(ROOT / 'neomutt/dynamic/html_on') + '\n'
                      + 'set folder=' + str(f.home / 'mail') + '\n'
                      + 'set from=sender@example.test realname=Fixture signature=""\n'
                      + 'set sendmail=' + str(transport) + '\n'
                      + 'unset record header_cache message_cache_dir\n'
                      + 'set sleep_time=0 wait_key=no edit_headers=yes auto_edit=yes abort_noattach=no abort_nosubject=no\n'
                      + 'macro compose X "<attach-file>' + str(self.document) + '<enter><tag-entry>"\n'
                      + 'set sort=unsorted index_format="%s"\n')
        self.command = 'env NEOMUTT_MARKDOWN_EDITOR=' + str(editor) + ' /opt/homebrew/bin/neomutt -n -F ' + str(rc) + ' -f ' + str(f.home / 'mail')
        f.tmux('respawn-pane', '-k', self.command)
        f.wait(lambda: 'Synthetic attachment fixture' in f.screen(), 'fresh test index')

    def draft(self):
        return next((self.fixture.home / '.cache/neomutt-html').glob('draft-*'))

    def compose(self, keys='cc'):
        self.fixture.keys(keys)
        self.fixture.wait(lambda: 'Attachments' in self.fixture.screen() or 'Size:' in self.fixture.screen(), 'compose menu')
        self.assertTrue(composer.load(self.draft())['valid'], self.fixture.screen())

    def send(self):
        self.fixture.keys('cc')
        self.fixture.wait(self.outbox.exists, 'captured outgoing message')
        return BytesParser(policy=policy.default).parsebytes(self.outbox.read_bytes())

    def test_markdown_alternatives_and_editing(self):
        self.compose()
        self.body.write_text('Edited **bold** and `code`.\nSecond line.\n')
        self.fixture.keys('ce')
        self.fixture.wait(lambda: 'Edited' in (self.draft() / 'message.html').read_text(), 'regenerated edit')
        message = self.send()
        self.assertEqual(message.get_content_type(), 'multipart/alternative')
        self.assertIn('<strong>bold</strong>', message.get_body(('html',)).get_content())
        self.assertIn('<br', message.get_body(('html',)).get_content())
        self.assertNotIn('**bold**', message.get_body(('plain',)).get_content())
        self.assertEqual(len(list(message.walk())), 3)

    def test_html_signature_and_unicode_math(self):
        accounts = self.fixture.home / '.config/neomutt/accounts'
        (accounts / 'fixture.conf').write_text('set from="sender@example.test"\n')
        footer = '<hr><p><strong>Fixture Footer</strong> | <a href="https://example.test">Website</a></p>'
        (accounts / 'fixture_html_signature.html').write_text(footer)
        (accounts / 'fixture_signature.txt').write_text('Fixture Footer | Website')
        self.body.write_text(r'Maybe some latex too? $\forall x \exists y\phi(x,y)$.' + '\n')
        self.compose()
        self.assertIn(footer, (self.draft() / 'source.md').read_text())
        self.fixture.keys('ce')
        self.fixture.wait(lambda: composer.load(self.draft())['valid'], 'signature re-edit')
        message = self.send()
        html_body = message.get_body(('html',)).get_content()
        plain = message.get_body(('plain',)).get_content()
        self.assertEqual(html_body.count(footer), 1)
        self.assertEqual(plain.count('Fixture Footer'), 1)
        self.assertIn('∀', html_body)
        self.assertIn('∃', html_body)
        self.assertNotIn('\\forall', html_body)
        self.assertNotIn('<annotation', html_body)
        self.assertNotIn('neomutt-signature', plain)

    def test_retry_and_reedit_after_failed_send(self):
        self.compose()
        self.fixture.keys('X')
        self.fixture.wait(lambda: '2 attachments' in self.fixture.screen(), 'user attachment')
        self.fail_send.touch()
        self.send()
        self.fixture.keys('Enter')
        self.fixture.wait(lambda: 'Size:' in self.fixture.screen(), 'compose after failed send')
        self.body.write_text('Retry **edited**.\n')
        self.fixture.keys('ce')
        self.fixture.wait(lambda: 'Retry' in (self.draft() / 'message.html').read_text(), 'edit after failed send')
        self.outbox.unlink()
        self.fail_send.unlink()
        message = self.send()
        self.assertEqual(message.get_content_type(), 'multipart/mixed')
        self.assertEqual(len(list(message.walk())), 5)
        self.assertIn('<strong>edited</strong>', message.get_body(('html',)).get_content())
        self.assertEqual(list(message.iter_attachments())[0].get_payload(decode=True), self.document.read_bytes())

    def test_local_markdown_image_is_sent_as_related_part(self):
        picture = self.fixture.root / 'picture.png'
        picture.write_bytes(b'fixture image bytes')
        self.body.write_text('Hello **image**.\n\n![caption](' + str(picture) + ')\n')
        self.compose()
        message = self.send()
        self.assertEqual(message.get_content_type(), 'multipart/alternative')
        self.assertEqual([part.get_content_type() for part in message.iter_parts()], ['text/plain', 'multipart/related'])
        self.assertIn('src="cid:', message.get_body(('html',)).get_content())
        self.assertEqual([p.get_payload(decode=True) for p in message.walk() if p.get_content_type() == 'image/png'], [b'fixture image bytes'])
        self.assertEqual(picture.read_bytes(), b'fixture image bytes')

    def test_html_reply_preserves_quote_and_cid(self):
        original = EmailMessage()
        original['From'] = 'Original Sender <original@example.test>'
        original['To'] = 'sender@example.test'
        original['Subject'] = 'Synthetic attachment fixture'
        original['Message-ID'] = '<original@example.test>'
        original.set_content('Original readable quote')
        fragment = '<table cellpadding="7"><tr><td>*literal quoted text*</td></tr></table><img src="cid:pic@test">'
        original.add_alternative('<html><body>' + fragment + '</body></html>', subtype='html')
        original.get_payload()[1].add_related(b'synthetic image', maintype='image', subtype='png', cid='<pic@test>')
        (self.fixture.home / 'mail/new/fixture').write_bytes(original.as_bytes())
        self.fixture.tmux('respawn-pane', '-k', self.command)
        self.fixture.wait(lambda: 'Synthetic attachment fixture' in self.fixture.screen(), 'reply fixture index')
        self.compose('cr')
        message = self.send()
        self.assertIn(fragment, message.get_body(('html',)).get_content())
        self.assertIn('Original readable quote', message.get_body(('plain',)).get_content())
        self.assertEqual(message['In-Reply-To'], '<original@example.test>')
        self.assertEqual([p.get_payload(decode=True) for p in message.walk() if p.get('Content-ID') == '<pic@test>'], [b'synthetic image'])

    def test_tagged_user_attachment_stays_outside_alternatives(self):
        self.compose()
        self.fixture.keys('X')
        self.fixture.wait(lambda: '2 attachments' in self.fixture.screen(), 'user attachment')
        message = self.send()
        self.assertEqual(message.get_content_type(), 'multipart/mixed')
        self.assertEqual([part.get_content_type() for part in message.iter_parts()], ['multipart/alternative', 'application/pdf'])
        self.assertEqual(list(message.iter_attachments())[0].get_payload(decode=True), b'untouched existing attachment')
        self.assertEqual(self.document.read_bytes(), b'untouched existing attachment')

    def test_conversion_failure_does_not_send(self):
        self.body.write_text('![missing](/no-such-file-neomutt-test.png)\n')
        self.fixture.keys('cc')
        self.fixture.wait(lambda: (self.fixture.home / '.cache/neomutt-html').exists(), 'draft creation')
        self.fixture.wait(lambda: (self.draft() / 'source.md').exists(), 'source retained')
        self.fixture.wait(lambda: 'Size:' in self.fixture.screen(), 'compose after conversion failure')
        self.fixture.keys('cc')
        time.sleep(.3)
        self.assertFalse(self.outbox.exists())
        self.assertFalse(composer.load(self.draft())['valid'])
        self.body.write_text('Fixed **reply**.\n')
        self.fixture.keys('ce')
        self.fixture.wait(lambda: composer.load(self.draft())['valid'], 'fixed conversion')
        message = self.send()
        self.assertIn('<strong>reply</strong>', message.get_body(('html',)).get_content())


class HtmlContentTests(unittest.TestCase):
    def test_missing_generated_file_cannot_queue_a_send(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            composer.store(run, {'valid': True, 'prepared': False})
            output = io.StringIO()
            with contextlib.redirect_stdout(output), self.assertRaisesRegex(ValueError, 'file is missing'):
                composer.send(run)
            self.assertEqual(output.getvalue(), '')

    def test_failed_conversion_retains_header_edits(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            composer.store(run, {'valid': False, 'initialized': False})
            draft = run / 'draft.eml'
            draft.write_text('To: old@example.test\n\nOriginal\n')
            edited = 'To: edited@example.test\nSubject: Updated\n\nMarkdown **edit**\n'
            def edit_fixture(*args, **kwargs):
                draft.write_text(edited)
            with patch.object(composer.subprocess, 'run', side_effect=edit_fixture), \
                 patch.object(composer, 'render', side_effect=ValueError('conversion failed')), \
                 self.assertRaisesRegex(ValueError, 'conversion failed'):
                composer.editor(run, draft)
            self.assertEqual(draft.read_text(), edited)
            self.assertEqual((run / 'recovery.eml').read_text(), edited)
            self.assertEqual((run / 'source.md').read_text(), 'Markdown **edit**\n')
            self.assertFalse(composer.load(run)['valid'])

    def test_quoted_markup_and_embedded_images_survive(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            composer.store(run, {'valid': False, 'initialized': True})
            message = EmailMessage()
            message['From'] = 'Sender <sender@example.test>'
            message.set_content('Original plain text')
            fragment = '<table style="border:1px solid red"><tr><td>*unchanged*</td></tr></table><img src="cid:pic@test">'
            message.add_alternative('<html><head><style>td { color: blue }</style></head><body>' + fragment + '</body></html>', subtype='html')
            message.get_payload()[1].add_related(b'fake png', maintype='image', subtype='png', cid='<pic@test>')
            with patch.object(sys, 'stdin', io.TextIOWrapper(io.BytesIO(message.as_bytes()))):
                composer.capture(run)
            state = composer.load(run)
            composer.render(run, '**New text**\n\n' + state['quote_block'])
            result = (run / 'message.html').read_text()
            self.assertIn(fragment, result)
            self.assertIn('<style>td { color: blue }</style>', result)
            self.assertIn('<strong>New text</strong>', result)
            self.assertEqual(composer.load(run)['resources'][0]['cid'], 'pic@test')
            with self.assertRaisesRegex(ValueError, 'Quoted section changed'):
                composer.render(run, state['quote_block'].replace('Original plain text', 'changed'))
            composer.render(run, 'Reply without quote')
            self.assertEqual(composer.load(run)['resources'], [])

    def test_viewer_excludes_html_attachments_and_resolves_cid(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            message = EmailMessage()
            message.set_content('Actual body')
            message.add_attachment('<p>unrelated attachment</p>', subtype='html', filename='page.html')
            self.assertNotIn('unrelated', viewer.message_html(message, run))

    def test_preview_resolves_images_without_changing_outgoing_html(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            image = run / 'pic.png'
            image.write_bytes(b'fixture image')
            original = '<img src="cid:picture@test">'
            (run / 'message.html').write_text(original)
            composer.store(run, {'valid': True, 'resources': [{'cid': 'picture@test', 'path': str(image)}]})
            def check_preview(command, **kwargs):
                path = Path(command[-1])
                self.assertIn(image.as_uri(), path.read_text())
                self.assertNotIn('cid:', path.read_text())
            with patch.object(composer.subprocess, 'run', side_effect=check_preview):
                composer.preview(run)
            self.assertEqual((run / 'message.html').read_text(), original)
            self.assertEqual(list(run.glob('preview-*')), [])


if __name__ == '__main__':
    unittest.main()
