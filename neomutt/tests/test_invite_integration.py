"""Real ci popups and HTML relay, using a fake local CalDAV server only."""

import base64
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
import select
import shlex
import sqlite3
import sys
import threading
import time
import unittest

from icalendar import Calendar

import test_html
from test_invite import ACCOUNT, FakeClient, message


class InvitationIntegration(unittest.TestCase):
    def setUp(self):
        self.gateway = FakeClient()
        gateway = self.gateway
        self.reads = []
        reads = self.reads
        self.context = test_html.HtmlIntegration("test_markdown_alternatives_and_editing")
        self.context.setUp()
        self.addCleanup(self.context.doCleanups)
        self.f = self.context.fixture

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def authorized(self):
                expected = "Basic " + base64.b64encode((ACCOUNT + ":fixture-password").encode()).decode()
                if self.headers.get("Authorization") != expected:
                    self.send_error(401)
                    return False
                return True

            def do_GET(self):
                if not self.authorized():
                    return
                reads.append(self.path)
                if self.path != "/users/me/calendar/test.ics":
                    self.send_error(404)
                    return
                data = gateway.calendar.to_ical()
                self.send_response(200)
                self.send_header("ETag", gateway.etag)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_PUT(self):
                if not self.authorized():
                    return
                if self.path != "/users/me/calendar/test.ics" or self.headers.get("If-Match") != gateway.etag:
                    self.send_error(412)
                    return
                payload = self.rfile.read(int(self.headers["Content-Length"]))
                gateway.request("PUT", self.path, payload, self.headers["If-Match"])
                self.send_response(200)
                self.send_header("Content-Length", "0")
                self.end_headers()

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        config = self.f.home / ".config"
        (config / "khal").symlink_to(test_html.ROOT / "khal", target_is_directory=True)
        (config / "vdirsyncer/scripts").mkdir(parents=True)
        password = config / "vdirsyncer/scripts/fetch-pw.zsh"
        password.write_text("#!/bin/sh\nprintf '%s\\n' fixture-password\n")
        password.chmod(0o700)
        local = self.f.root / "calendar"
        local.mkdir()
        (local / "test.ics").write_bytes(gateway.calendar.to_ical())
        status = self.f.root / "status/uu_graph"
        status.mkdir(parents=True)
        with closing(sqlite3.connect(status / "calendar.items")) as database, database:
            database.execute("CREATE TABLE status (ident TEXT, href_b TEXT)")
            database.execute("INSERT INTO status VALUES (?, ?)", ("offline-invitation", "/users/me/calendar/test.ics"))
        (config / "vdirsyncer/config").write_text(
            '[general]\nstatus_path = "' + str(self.f.root / "status") + '"\n'
            + '[pair uu_graph]\na = "uu_graph_local"\nb = "uu_graph_remote"\n'
            + '[storage uu_graph_remote]\nurl = "http://127.0.0.1:' + str(self.server.server_port)
            + '/users/me/calendar/"\nusername = "' + ACCOUNT + '"\n'
            + '[storage uu_graph_local]\npath = "' + str(self.f.root) + '"\n')
        # Replace only the fixture's symlink; all production scripts stay intact.
        scripts = config / "neomutt/scripts"
        scripts.unlink()
        scripts.mkdir()
        for source in (test_html.ROOT / "neomutt/scripts").iterdir():
            if source.name != "neomutt-invite":
                (scripts / source.name).symlink_to(source)
        wrapper = (test_html.ROOT / "neomutt/scripts/neomutt-invite").read_text()
        wrapper = wrapper.replace("import invite\n", "import invite\ninvite.CONFIG = Path(" + repr(str(config))
                                  + ")\nos.environ['XDG_STATE_HOME'] = " + repr(str(self.f.root / "state")) + "\n")
        (scripts / "neomutt-invite").write_text(wrapper)
        (scripts / "neomutt-invite").chmod(0o700)
        # The wrapper imports the same implementation; configuration points only
        # to the fake server, fake password hook, and temporary calendar/state.
        (self.f.home / "mail/new/fixture").write_bytes(message().as_bytes())
        self.output = bytearray()
        self.f.drain = self.drain
        self.f.tmux("respawn-pane", "-k", self.context.command)
        self.wait_pane("Synthetic invitation")

    def drain(self):
        while select.select([self.f.master], [], [], 0)[0]:
            data = os.read(self.f.master, 65536)
            self.output.extend(data)
            for query, answer in {
                b'\x1b[c': b'\x1b[?64;1;2;6;9;15;18;21;22c',
                b'\x1b[>c': b'\x1b[>0;10;1c', b'\x1b[>0c': b'\x1b[>0;10;1c',
                b'\x1b[6n': b'\x1b[24;80R',
                b'\x1b]10;?\x1b\\': b'\x1b]10;rgb:abab/b2b2/bfbf\x1b\\',
                b'\x1b]11;?\x1b\\': b'\x1b]11;rgb:1e1e/1e1e/1e1e\x1b\\',
            }.items():
                if query in data:
                    os.write(self.f.master, answer)

    def wait_output(self, text):
        end = time.monotonic() + 10
        while time.monotonic() < end:
            self.drain()
            if text.encode() in self.output:
                self.output.clear()
                return
            time.sleep(.03)
        self.fail("Missing popup text: " + text + "\n" + self.output.decode(errors="replace")[-5000:])

    def wait_pane(self, text):
        self.f.wait(lambda: text in self.f.screen(), text)

    def keys(self, data):
        self.drain()
        self.output.clear()
        os.write(self.f.master, data)

    def test_cancel_then_confirm_once_from_html(self):
        # Real mapping at the index, with cancellation at the confirmation step.
        self.keys(b"ci")
        self.wait_output("Not answered")
        self.keys(b"\r")  # Accept, then Enter.
        self.wait_output("Send response")
        self.keys(b"\x1b")
        self.wait_pane("Synthetic invitation")
        self.assertFalse(self.gateway.writes)
        # H from HTML mode opens text; ci also works in that pager.
        self.keys(b"H")
        self.wait_pane("Autoview using w3m")
        self.keys(b"ci")
        self.wait_output("Not answered")
        self.keys(b"\x1b")
        self.wait_pane("Autoview using w3m")
        self.assertFalse(self.gateway.writes)
        # Open Chawan and exercise its actual ci handoff to the same popup.
        self.keys(b"H")
        self.wait_pane("Viewing <file://")
        self.keys(b"ci")
        self.wait_output("Not answered")
        self.keys(b"\t\r")  # Move right to Tentative.
        self.wait_output("Send response")
        self.keys(b"\x0e\r")  # Explicit Send.
        self.wait_output("Response submitted")
        self.keys(b"\x1b")
        self.assertEqual(len(self.gateway.writes), 1)
        method, path, body, etag = self.gateway.writes[0]
        self.assertEqual((method, path, etag), ("PUT", "/users/me/calendar/test.ics", '"version-one"'))
        result = Calendar.from_ical(body).walk("VEVENT")
        self.assertEqual(len(result), 1)
        self.assertEqual(str(result[0]["ATTENDEE"][0].params["PARTSTAT"]), "TENTATIVE")
        # A repeated click is a no-op, even before the local cache catches up.
        self.wait_pane("Synthetic invitation")
        self.keys(b"ci")
        self.wait_output("Your reply: Tentative")
        self.keys(b"\x0e\r")
        self.wait_output("Send response")
        self.keys(b"\x0e\r")
        self.wait_output("already submitted")
        self.keys(b"\x1b")
        self.assertEqual(len(self.gateway.writes), 1)

    def test_dialog_without_tmux_and_inside_existing_popup(self):
        runner = self.f.root / "dialog-fixture.py"
        result = self.f.root / "dialog-result"
        runner.write_text(
            "import sys\nfrom pathlib import Path\n"
            + "sys.path.insert(0, " + repr(str(test_html.ROOT / "neomutt/scripts")) + ")\n"
            + "from invite import choose\n"
            + "answer = choose('Invitation', 'Synthetic invitation\\nYour reply: Not answered', "
            + "[('ACCEPTED', '  Accept'), ('TENTATIVE', '󰔛  Tentative'), ('DECLINED', '  Decline')])\n"
            + "Path(" + repr(str(result)) + ").write_text(str(answer))\n")
        command = shlex.join([sys.executable, str(runner)])
        for prefix, keys, expected in (
            ("env -u TMUX ", b"\x1b[C\x1b[D\x1b[Z\r", "DECLINED"),
            ("tmux display-popup -E -w 90% -h 90% ", b"q", "None"),
        ):
            with self.subTest(prefix=prefix):
                self.output.clear()
                self.f.tmux("respawn-pane", "-k", prefix + command + "; sleep 30")
                self.wait_output("Not answered")
                self.keys(keys)
                self.f.wait(result.exists, "dialog result")
                self.assertEqual(result.read_text(), expected)
                result.unlink()
        self.assertFalse(self.gateway.writes)


if __name__ == "__main__":
    unittest.main()
