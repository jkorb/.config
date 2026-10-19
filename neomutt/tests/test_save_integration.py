"""Real NeoMutt -> nnn tests using synthetic mail and a fake Trash folder.

These tests create a separate tmux server and HOME. No real mailbox, Downloads,
notification, or Trash is used. Requires local tmux, nnn and NeoMutt on macOS.
"""
import errno
import json
import os
from pathlib import Path
import pty
import select
import shlex
import signal
import subprocess
import tempfile
import time
import unittest
from email.message import EmailMessage

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/neomutt-save'


@unittest.skipUnless(os.uname().sysname == 'Darwin', 'macOS file identity handling')
class SaveIntegration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mail-save-test-')
        self.root = Path(self.temp.name).resolve()
        self.home = self.root / 'home'
        self.downloads = self.home / 'Downloads'
        self.downloads.mkdir(parents=True)
        (self.home / '.cache').mkdir()
        (self.home / '.config').mkdir()
        # Exercise the real directory-jump plugin/fzf against only the fake HOME.
        repo = SCRIPT.parents[2]
        for name in ('nnn', 'zsh'):
            (self.home / '.config' / name).symlink_to(repo / name, target_is_directory=True)
        (self.downloads / 'report.txt').write_bytes(b'existing document')
        self.sentinel = self.downloads / 'unrelated.txt'
        self.sentinel.write_bytes(b'untouched')
        self.destination = self.home / 'destination'
        self.destination.mkdir()
        self.trash = self.root / 'trash'
        self.trash.mkdir()
        trash_cmd = self.root / 'trash-fixture'
        trash_cmd.write_text('#!/usr/bin/python3\nimport shutil,sys\nfrom pathlib import Path\nfor p in sys.argv[1:]:\n shutil.move(p, str(Path(' + repr(str(self.trash)) + ') / Path(p).name))\n')
        trash_cmd.chmod(0o755)
        self.helper = self.root / 'neomutt-save'
        self.helper.write_text(SCRIPT.read_text().replace('TRASH = "/usr/bin/trash"', 'TRASH = ' + repr(str(trash_cmd))))
        self.helper.chmod(0o755)
        maildir = self.home / 'mail'
        for name in ('cur', 'new', 'tmp'):
            (maildir / name).mkdir(parents=True)
        message = EmailMessage()
        message['From'] = 'Fixture <student@students.uu.nl>'
        message['To'] = 'Test <test@example.test>'
        message['Subject'] = 'Synthetic attachment fixture'
        message['Message-ID'] = '<fixture@example.test>'
        message.set_content('Only synthetic mail.')
        for payload in (b'first payload', b'second payload'):
            message.add_attachment(payload, maintype='application', subtype='octet-stream', filename='report.txt')
        (maildir / 'new/fixture').write_bytes(message.as_bytes())
        rc = self.root / 'muttrc'
        rc.write_text('''set mbox_type=Maildir
set sleep_time=0 wait_key=no confirmappend=yes delete=no quit=yes
set shell=/bin/bash
set sort=unsorted
set attach_format="%n %t %f"
set index_format="%s"
bind index A view-attachments
bind attach q exit
bind index q quit
bind attach t tag-entry
macro attach s "<enter-command>source \\\"''' + str(self.helper) + ''' prepare |\\\"<enter>"
''')
        config = self.root / 'tmux.conf'
        jump_binding = next(line for line in (repo / 'tmux/conf/keybinds.conf').read_text().splitlines()
                            if line.startswith('bind-key -n C-g '))
        config.write_text('set -g default-shell /bin/bash\nset -g status off\nset -s escape-time 10\n' + jump_binding + '\n')
        self.env = {**os.environ, 'HOME':str(self.home), 'XDG_CACHE_DIR':str(self.home / '.cache'),
                    'XDG_CONFIG_HOME':str(self.home / '.config'),
                    'TERM':'xterm-256color', 'PATH':'/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin',
                    'SHELL':'/bin/bash', 'TMPDIR':str(self.root) + '/', 'NNN_OPTS':'',
                    'NNN_BMS':'t:' + str(self.destination), 'NNN_PLUG':'g:goto-dir',
                    'FZF_DEFAULT_OPTS':'', 'FZF_DEFAULT_OPTS_FILE':'',
                    'PYTHONDONTWRITEBYTECODE':'1'}
        self.env.pop('TMUX', None)
        self.env.pop('TMUX_PANE', None)
        self.base = ['/opt/homebrew/bin/tmux', '-S', str(self.root / 'tmux.sock')]
        self.master = self.child = None
        command = shlex.join(['/opt/homebrew/bin/neomutt', '-n', '-F', str(rc), '-f', str(maildir)])
        self.tmux('-f', str(config), 'new-session', '-d', '-s', 'fixture', '-x', '120', '-y', '35', command)
        self.child, self.master = pty.fork()
        if self.child == 0:
            os.execve(self.base[0], self.base + ['attach-session', '-t', 'fixture'], self.env)
        self.addCleanup(self.cleanup)
        self.wait(lambda: 'Synthetic attachment fixture' in self.screen(), 'mail index')
        self.keys('A')
        self.wait(lambda: 'report.txt' in self.screen(), 'attachment menu')

    def cleanup(self):
        subprocess.run(self.base + ['kill-server'], env=self.env, capture_output=True)
        if self.master is not None:
            os.close(self.master)
        if self.child is not None:
            os.waitpid(self.child, 0)
        self.temp.cleanup()

    def tmux(self, *args):
        return subprocess.check_output(self.base + list(args), env=self.env, text=True, stderr=subprocess.STDOUT).strip()

    def drain(self):
        while self.master is not None and select.select([self.master], [], [], 0)[0]:
            try:
                if not os.read(self.master, 65536):
                    break
            except OSError as error:
                if error.errno == errno.EIO:
                    break
                raise

    def screen(self):
        self.drain()
        return self.tmux('capture-pane', '-p')

    def wait(self, check, description):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            self.drain()
            if check():
                return
            time.sleep(.03)
        self.fail(description + '\n' + self.tmux('capture-pane', '-p', '-S', '-80'))

    def keys(self, *keys):
        self.tmux('send-keys', *keys)

    def selection(self):
        files = list((self.home / '.cache/neomutt-save').glob('*/selection'))
        if not files:
            return set()
        return {os.fsdecode(p) for p in files[-1].read_bytes().split(b'\0') if p}

    def start_picker(self, bulk=False):
        self.keys('j', 'j')
        if bulk:
            self.keys('t', 't')
        self.keys('s')
        count = 2 if bulk else 1
        self.wait(lambda: len(self.selection()) == count, 'initial nnn selection')
        self.assertIn('~/Downloads', self.screen())
        return sorted(Path(p) for p in self.selection())

    def finish(self):
        self.keys('q')
        self.wait(lambda: 'Attachments' in self.screen(), 'return to NeoMutt')
        self.assertEqual(self.sentinel.read_bytes(), b'untouched')
        self.assertEqual((self.downloads / 'report.txt').read_bytes(), b'existing document')

    def test_bulk_preselected_and_numbered(self):
        paths = self.start_picker(bulk=True)
        self.assertEqual([p.name for p in paths], ['report (1).txt', 'report (2).txt'])
        self.finish()
        self.assertEqual([p.read_bytes() for p in paths], [b'first payload', b'second payload'])
        self.assertEqual(list(self.trash.iterdir()), [])

    def test_single_and_deselect(self):
        paths = self.start_picker()
        self.keys('Space')
        self.wait(lambda: not self.selection(), 'deselection')
        self.finish()
        self.assertFalse(paths[0].exists())
        self.assertEqual((self.trash / paths[0].name).read_bytes(), b'first payload')

    def test_native_rename_and_reselect(self):
        paths = self.start_picker()
        self.keys('C-r', 'C-u')
        self.tmux('send-keys', '-l', 'renamed file.txt')
        self.keys('Enter')
        renamed = self.downloads / 'renamed file.txt'
        self.wait(renamed.exists, 'rename')
        self.keys('Space')
        self.wait(lambda: str(renamed) in self.selection(), 'select renamed file')
        self.finish()
        self.assertFalse(paths[0].exists())
        self.assertEqual(renamed.read_bytes(), b'first payload')

    def test_safe_rename_numbers_collision(self):
        self.start_picker()
        self.tmux('send-keys', '-l', ';r')
        self.wait(lambda: 'New filename' in self.screen(), 'safe rename prompt')
        self.tmux('send-keys', '-l', 'unrelated.txt')
        self.keys('Enter')
        renamed = self.downloads / 'unrelated (1).txt'
        self.wait(renamed.exists, 'numbered rename')
        self.keys('Enter')
        self.wait(lambda: '~/Downloads' in self.screen(), 'return from rename')
        # The safe rename clears selection; pick the renamed file explicitly.
        self.keys('g', 'j', 'Space')
        self.wait(lambda: str(renamed) in self.selection(), 'select safely renamed file')
        self.finish()
        self.assertEqual(renamed.read_bytes(), b'first payload')

    def test_move_numbers_collision_and_reselect(self):
        paths = self.start_picker()
        existing = self.destination / paths[0].name
        existing.write_bytes(b'existing destination')
        self.keys('b', 't')
        self.wait(lambda: '~/destination' in self.screen(), 'destination directory')
        self.keys('v')
        moved = self.destination / 'report (1) (1).txt'
        self.wait(moved.exists, 'move with collision')
        self.assertFalse(self.selection())
        self.keys('g', 'Space')
        self.wait(lambda: str(moved) in self.selection(), 'select moved file')
        self.finish()
        self.assertEqual(moved.read_bytes(), b'first payload')
        self.assertEqual(existing.read_bytes(), b'existing destination')

    def test_move_to_symlinked_directory_and_reselect(self):
        paths = self.start_picker()
        destination = self.home / 'Dropbox/Teaching/Letters/Example, Person'
        destination.mkdir(parents=True)
        (self.destination / 'Teaching').symlink_to(self.home / 'Dropbox/Teaching', target_is_directory=True)
        self.keys('b', 't', 'l', 'l', 'l')
        self.wait(lambda: 'Example, Person' in self.screen(), 'symlinked destination')
        self.keys('v')
        moved = destination / paths[0].name
        self.wait(moved.exists, 'move through directory symlink')
        self.keys('g', 'Space')
        self.wait(lambda: any(p.endswith('/' + moved.name) for p in self.selection()), 'select moved file through alias')
        self.finish()
        self.assertEqual(moved.read_bytes(), b'first payload')
        self.assertEqual(list(self.trash.iterdir()), [])

    def test_ctrl_g_jumps_and_selected_move_is_kept(self):
        paths = self.start_picker()
        # Physical client input exercises the normal tmux binding as well.
        os.write(self.master, b'\x07')
        self.wait(lambda: '🚀' in self.screen(), 'directory picker')
        self.tmux('send-keys', '-l', 'destination')
        self.keys('Enter')
        self.wait(lambda: '~/destination' in self.screen(), 'jump to destination')
        self.keys('v')
        moved = self.destination / paths[0].name
        self.wait(moved.exists, 'move after jump')
        self.keys('g', 'Space')
        self.wait(lambda: str(moved) in self.selection(), 'reselect after jump and move')
        self.finish()
        self.assertEqual(moved.read_bytes(), b'first payload')
        self.assertEqual(list(self.trash.iterdir()), [])

    def test_ctrl_g_in_fzf_cancels_only_directory_jump(self):
        paths = self.start_picker()
        os.write(self.master, b'\x07')
        self.wait(lambda: '🚀' in self.screen(), 'directory picker')
        os.write(self.master, b'\x07')
        self.wait(lambda: '~/Downloads' in self.screen() and '🚀' not in self.screen(), 'return from cancelled jump')
        self.assertTrue(paths[0].exists())
        self.keys('Space')
        self.wait(lambda: not self.selection(), 'deselection after cancelling jump')
        self.finish()
        self.assertFalse(paths[0].exists())
        self.assertEqual((self.trash / paths[0].name).read_bytes(), b'first payload')

    def test_cancel_keeps_exported_files(self):
        paths = self.start_picker()
        self.keys('C-x')
        self.wait(lambda: 'kept' in self.screen(), 'cancellation diagnostic')
        self.keys('Enter')
        self.wait(lambda: 'Attachments' in self.screen(), 'return after cancel')
        self.assertEqual(paths[0].read_bytes(), b'first payload')
        self.assertEqual(list(self.trash.iterdir()), [])

    def test_interruption_keeps_exported_files(self):
        paths = self.start_picker()
        processes = subprocess.check_output(['ps', '-axo', 'pid=,command='], text=True)
        matches = [int(line.split()[0]) for line in processes.splitlines()
                   if str(self.helper) + ' manage ' in line and 'python' in line.lower()]
        self.assertEqual(len(matches), 1)
        os.kill(matches[0], signal.SIGTERM)
        self.wait(lambda: 'Picker interrupted' in self.screen(), 'interruption diagnostic')
        self.keys('Enter')
        self.wait(lambda: 'Attachments' in self.screen(), 'return after interruption')
        self.assertEqual(paths[0].read_bytes(), b'first payload')
        self.assertEqual(list(self.trash.iterdir()), [])

    def test_unselected_moved_file_goes_to_trash(self):
        paths = self.start_picker()
        self.keys('b', 't')
        self.wait(lambda: '~/destination' in self.screen(), 'destination directory')
        self.keys('v')
        moved = self.destination / paths[0].name
        self.wait(moved.exists, 'move')
        self.wait(lambda: not self.selection(), 'move clears selection')
        self.finish()
        self.assertFalse(moved.exists())
        self.assertEqual((self.trash / moved.name).read_bytes(), b'first payload')

    def test_stale_selection_after_native_rename_keeps_exports(self):
        paths = self.start_picker()
        self.keys('C-r', 'C-u')
        self.tmux('send-keys', '-l', 'renamed.txt')
        self.keys('Enter')
        renamed = self.downloads / 'renamed.txt'
        self.wait(renamed.exists, 'rename')
        # Native rename can leave the old (now missing) path in nnn's selection.
        # An unresolved selection must retain everything rather than guess.
        self.assertIn(str(paths[0]), self.selection())
        self.keys('q')
        self.wait(lambda: 'all exported files were kept' in self.screen(), 'stale selection diagnostic')
        self.keys('Enter')
        self.wait(lambda: 'Attachments' in self.screen(), 'return after retaining exports')
        self.assertEqual(renamed.read_bytes(), b'first payload')
        self.assertEqual(list(self.trash.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
