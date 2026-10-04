"""Check colors with curses active; `neomutt -Q` does not check terminal support."""

import os
from pathlib import Path
import pty
import select
import shutil
import signal
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which("neomutt"), "NeoMutt is not installed")
class NeoMuttThemeTests(unittest.TestCase):
    def test_normal_html_and_return_under_tmux(self):
        with tempfile.TemporaryDirectory(prefix="neomutt-theme-") as temp:
            folder = Path(temp)
            mailbox = folder / "empty.mbox"
            mailbox.touch()
            config = folder / "rc"
            config.write_text(
                f'set folder="{folder}"\nset quit=yes\n'
                f'source "{ROOT}/neomutt/core/colors"\n'
                f'source "{ROOT}/neomutt/core/colors-html"\n'
                f'source "{ROOT}/neomutt/core/colors"\n'
            )
            pid, fd = pty.fork()
            if pid == 0:
                os.environ["TERM"] = "tmux-256color"
                os.execvp("neomutt", ["neomutt", "-n", "-F", str(config), "-R",
                                     "-f", str(mailbox), "-e", "push <exit>"])
            output = b""
            status = None
            try:
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    if select.select([fd], [], [], 0.1)[0]:
                        try:
                            output += os.read(fd, 65536)
                        except OSError:
                            break  # macOS/Linux PTYs signal closed slaves differently.
                    done, code = os.waitpid(pid, os.WNOHANG)
                    if done:
                        status = code
                        break
            finally:
                os.close(fd)
                if status is None:
                    done, code = os.waitpid(pid, os.WNOHANG)
                    if not done:
                        os.kill(pid, signal.SIGKILL)
                        _, code = os.waitpid(pid, 0)
                    status = code
            screen = output.decode(errors="replace")
            self.assertEqual(os.waitstatus_to_exitcode(status), 0, screen)
            self.assertNotIn("color not supported", screen)
            self.assertNotIn("source: errors", screen)
            self.assertNotIn("Press any key", screen)


if __name__ == "__main__":
    unittest.main()
