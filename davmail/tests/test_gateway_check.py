import importlib.machinery
import importlib.util
import io
from pathlib import Path
import subprocess
import unittest
from unittest.mock import Mock, patch

SCRIPT = Path(__file__).resolve().parents[1] / "gateway-check"
LOADER = importlib.machinery.SourceFileLoader("gateway_check", str(SCRIPT))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
check = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(check)


class GatewayCheckTests(unittest.TestCase):
    def test_isolated_settings_disable_retention_sending_and_token_persistence(self):
        config = check.configuration(Path("/private/tmp/test-only"), [51001, 51002, 51003], "test@example.edu")
        for key in ("smtpPort", "popPort", "keepDelay", "sentKeepDelay"):
            self.assertEqual(config["davmail." + key], "0")
        for key in ("imapAutoExpunge", "oauth.persistToken", "allowRemote"):
            self.assertEqual(config["davmail." + key], "false")
        self.assertEqual(config["davmail.bindAddress"], "127.0.0.1")
        self.assertTrue(config["davmail.oauth.tokenFilePath"].startswith("/private/tmp/test-only/"))
        self.assertEqual(config["davmail.timezoneId"], "W. Europe Standard Time")

    def test_imap_only_examines_fetches_metadata_and_logs_out(self):
        client = Mock()
        client.select.return_value = ("OK", [b"2"])
        client.fetch.return_value = ("OK", [b"private returned metadata"])
        output = io.StringIO()
        with patch.object(check.imaplib, "IMAP4", return_value=client), patch("sys.stdout", output):
            check.check_imap(51001, "test@example.edu", "local-session-key")
        self.assertEqual([c[0] for c in client.mock_calls],
                         ["login", "sock.settimeout", "select", "fetch", "logout"])
        client.select.assert_called_once_with("INBOX", readonly=True)
        client.fetch.assert_called_once_with("1", "(UID FLAGS)")
        self.assertNotIn("private", output.getvalue())

    def test_failed_examine_never_closes_or_expunges(self):
        client = Mock()
        client.select.return_value = ("NO", [b"error"])
        with patch.object(check.imaplib, "IMAP4", return_value=client), patch("sys.stdout", io.StringIO()):
            with self.assertRaises(RuntimeError):
                check.check_imap(51001, "test@example.edu", "local-session-key")
        client.logout.assert_called_once()
        client.close.assert_not_called()
        client.expunge.assert_not_called()
        client.fetch.assert_not_called()

    def test_caldav_blocks_writes_and_nonlocal_targets_before_connecting(self):
        with patch.object(check.http.client, "HTTPConnection") as connect:
            for method in ("PUT", "POST", "DELETE", "PROPPATCH", "MKCALENDAR"):
                with self.assertRaises(ValueError):
                    check.caldav_read(51002, "secret", method, "/users/test/calendar/")
            for path in ("https://example.edu/users/test/calendar/", "//example.edu/users/test/calendar/"):
                with self.assertRaises(ValueError):
                    check.caldav_read(51002, "secret", "GET", path)
        connect.assert_not_called()

    def test_caldav_does_not_follow_redirects(self):
        connection = Mock()
        response = connection.getresponse.return_value
        response.status = 302
        response.read.return_value = b""
        with patch.object(check.http.client, "HTTPConnection", return_value=connection):
            with self.assertRaisesRegex(RuntimeError, "HTTP 302"):
                check.caldav_read(51002, "secret", "GET", "/users/test/calendar/item.ics")
        connection.request.assert_called_once()
        connection.close.assert_called_once()

    def test_gateway_output_only_prints_one_device_prompt(self):
        lines = io.StringIO("secret-token\nTo sign in, enter the code ABCDEF123 to authenticate.\n"
                            "private-message-content\nTo sign in, enter the code ABCDEF123 to authenticate.\n")
        output = io.StringIO()
        with patch("sys.stdout", output):
            check.show_device_code(lines)
        self.assertEqual(output.getvalue().count("ABCDEF123"), 1)
        self.assertNotIn("secret-token", output.getvalue())
        self.assertNotIn("private-message", output.getvalue())

    def test_shutdown_targets_only_owned_child_and_waits_before_cleanup(self):
        process = Mock()
        process.poll.return_value = None
        process.wait.side_effect = [subprocess.TimeoutExpired("trial", 5), 0]
        check.stop_gateway(process)
        self.assertEqual([c[0] for c in process.mock_calls],
                         ["poll", "terminate", "wait", "kill", "wait"])


if __name__ == "__main__":
    unittest.main()
