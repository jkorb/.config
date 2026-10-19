import importlib.machinery
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit


SCRIPT = Path(__file__).resolve().parents[1] / "graph-check"
LOADER = importlib.machinery.SourceFileLoader("graph_check", str(SCRIPT))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
check = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(check)

ACCOUNT = "tester@example.edu"
SHARED = "shared@example.edu"
ACCESS = "secret-access-token"
REFRESH = "secret-refresh-token"
DEVICE = {"device_code": "secret-device-code", "user_code": "VISIBLE-CODE", "expires_in": 900}
TOKEN = {"access_token": ACCESS, "refresh_token": REFRESH, "scope": "User.Read Calendars.Read.Shared"}
OUTLOOK_TOKEN = dict(TOKEN, token_type="Bearer", resource="https://graph.microsoft.com",
                     scope="User.Read Calendars.ReadWrite Calendars.Read.Shared Mail.ReadWrite "
                           "Mail.Send MailboxSettings.Read Contacts.ReadWrite People.Read")
CALENDAR = {"canEdit": True, "allowedOnlineMeetingProviders": ["teamsForBusiness"],
            "defaultOnlineMeetingProvider": "teamsForBusiness"}


def json_body(value):
    return io.BytesIO(json.dumps(value).encode())


def api_error(code, message="Test error", status=400):
    return HTTPError("https://login.microsoftonline.com/test", status, "Error", {},
                     json_body({"error": code, "error_description": message}))


class GraphCheckTests(unittest.TestCase):
    def run_flow(self, responses, extra_args=()):
        opener = Mock()
        opener.open.side_effect = [r if isinstance(r, BaseException) else json_body(r) for r in responses]
        output = io.StringIO()
        with patch.object(check, "build_opener", return_value=opener), \
                patch.object(check.time, "sleep") as sleep, \
                patch.object(check.time, "monotonic", return_value=0), \
                patch.object(check.sys, "argv", [str(SCRIPT), "--account", ACCOUNT, *extra_args]), \
                patch.object(check.sys, "stdout", output), patch.object(check.sys, "stderr", output):
            result = check.main()
        return result, output.getvalue(), opener.open.call_args_list, sleep.call_args_list

    def test_complete_flow_only_reads_metadata_and_keeps_tokens_out_of_output(self):
        result, output, calls, sleeps = self.run_flow([
            DEVICE, api_error("authorization_pending"), api_error("slow_down"), TOKEN,
            {"mail": ACCOUNT, "userPrincipalName": "alias@example.edu"}, CALENDAR, CALENDAR,
        ], ["--shared", SHARED])
        self.assertEqual(result, 0)
        self.assertEqual(output.count("Teams supported: yes"), 2)
        for secret in (ACCESS, REFRESH, DEVICE["device_code"]):
            self.assertNotIn(secret, output)
        self.assertIn(DEVICE["user_code"], output)
        self.assertEqual([c.args[0] for c in sleeps], [5, 5, 10])

        requests = [c.args[0] for c in calls]
        for request in requests[:4]:
            self.assertEqual(request.method, "POST")
            self.assertEqual(urlsplit(request.full_url).netloc, "login.microsoftonline.com")
            self.assertIsNone(request.get_header("Authorization"))
        scope = parse_qs(requests[0].data.decode())["scope"][0]
        self.assertEqual(set(scope.split()), {
            "https://graph.microsoft.com/User.Read",
            "https://graph.microsoft.com/Calendars.Read.Shared",
        })
        self.assertNotIn("offline_access", scope)
        for request in requests[4:]:
            self.assertEqual(request.method, "GET")
            self.assertIsNone(request.data)
            self.assertEqual(urlsplit(request.full_url).netloc, "graph.microsoft.com")
            self.assertEqual(request.get_header("Authorization"), "Bearer " + ACCESS)
        self.assertEqual([urlsplit(r.full_url).path for r in requests[4:]], [
            "/v1.0/me", "/v1.0/me/calendar", "/v1.0/users/shared%40example.edu/calendar",
        ])

    def test_broader_existing_consent_is_rejected_before_any_graph_request(self):
        for permission in ("Mail.ReadWrite", "Calendars.ReadWrite", "Mail.Send", "offline_access", "User.Read.All"):
            with self.subTest(permission=permission):
                token = dict(TOKEN, scope=TOKEN["scope"] + " " + permission)
                result, output, calls, _ = self.run_flow([DEVICE, token])
                self.assertEqual(result, 1)
                self.assertIn("Unexpected permissions", output)
                self.assertEqual(len(calls), 2)
                self.assertNotIn(ACCESS, output)

    def test_missing_scope_fails_closed(self):
        with self.assertRaisesRegex(check.CheckError, "No granted permission list"):
            check.checked_token({"access_token": ACCESS})

    def test_missing_calendar_permission_is_not_treated_as_success(self):
        with self.assertRaisesRegex(check.CheckError, "not granted"):
            check.checked_token(dict(TOKEN, scope="User.Read"))

    def test_fully_qualified_scopes_are_supported(self):
        scope = "openid profile " + " ".join("https://graph.microsoft.com/" + s for s in check.SCOPES)
        self.assertEqual(check.checked_token(dict(TOKEN, scope=scope)), ACCESS)

    def test_wrong_account_stops_before_calendar_requests(self):
        result, output, calls, _ = self.run_flow([DEVICE, TOKEN, {"mail": "wrong@example.edu"}])
        self.assertEqual(result, 1)
        self.assertIn("different account", output)
        self.assertEqual(len(calls), 3)

    def test_shared_access_failure_preserves_personal_result(self):
        result, output, calls, _ = self.run_flow([
            DEVICE, TOKEN, {"userPrincipalName": ACCOUNT.upper()}, CALENDAR,
            api_error({"code": "ErrorAccessDenied", "message": "Access denied"}, status=403),
        ], ["--shared", SHARED])
        self.assertEqual(result, 1)
        self.assertIn("Your default calendar: readable", output)
        self.assertIn("shared@example.edu: FAILED", output)
        self.assertEqual(len(calls), 5)

    def test_tenant_policy_failure_stops_without_fallback_or_scope_escalation(self):
        result, output, calls, _ = self.run_flow([
            DEVICE, api_error("access_denied", "Administrator approval required"),
        ])
        self.assertEqual(result, 1)
        self.assertIn("Administrator approval required", output)
        self.assertEqual(len(calls), 2)

    def test_expired_flow_does_not_keep_polling(self):
        with patch.object(check, "oauth_post", return_value=DEVICE) as oauth, \
                patch.object(check.time, "monotonic", side_effect=[0, 901]), \
                patch.object(check.sys, "stdout", io.StringIO()):
            with self.assertRaisesRegex(check.CheckError, "expired"):
                check.authenticate(check.CLIENT_ID)
            self.assertEqual(oauth.call_count, 1)

    def test_unsupported_endpoints_are_rejected_before_network_access(self):
        with patch.object(check, "request_json") as request:
            for path in ("/me/messages", "/me/events", "/me/calendar/events", "/me/calendar/accept",
                         "https://example.org/", "/me?anything=1", "/me/calendar?anything=1"):
                with self.subTest(path=path), self.assertRaises(check.CheckError):
                    check.graph_get(ACCESS, path)
            request.assert_not_called()

    def test_no_redirect_can_forward_a_token(self):
        handler = check.NoRedirect()
        for code in (301, 302, 303, 307, 308):
            self.assertIsNone(handler.redirect_request(None, None, code, "", {}, "https://example.org/"))

    def test_no_false_teams_success_when_provider_is_absent(self):
        result, output, _, _ = self.run_flow([
            DEVICE, TOKEN, {"mail": ACCOUNT}, {"canEdit": False, "allowedOnlineMeetingProviders": []},
        ])
        self.assertEqual(result, 0)
        self.assertIn("Teams supported: no; account can edit: no", output)

    def test_cancel_does_not_print_authentication_secrets(self):
        result, output, _, _ = self.run_flow([DEVICE, KeyboardInterrupt()])
        self.assertEqual(result, 130)
        self.assertIn("Cancelled", output)
        self.assertNotIn(DEVICE["device_code"], output)

    def test_timeout_is_reported_without_a_traceback_or_retry(self):
        result, output, calls, _ = self.run_flow([TimeoutError()])
        self.assertEqual(result, 1)
        self.assertIn("Connection timed out", output)
        self.assertEqual(len(calls), 1)

    def test_outlook_flow_uses_resource_auth_then_metadata_gets_only(self):
        result, output, calls, _ = self.run_flow([
            DEVICE, OUTLOOK_TOKEN, {"mail": ACCOUNT}, CALENDAR, CALENDAR,
            {"id": "private-mailbox-id"}, {"timeZone": "UTC"},
            {"value": [{"id": "private-contact-id"}]}, {"value": []},
            {"id": "private-shared-id"},
        ], ["--outlook", "--shared", SHARED, "--shared-mailbox", SHARED])
        self.assertEqual(result, 0)
        self.assertIn("Mail.ReadWrite", output)
        self.assertIn("Personal mailbox: readable", output)
        self.assertIn("People lookup API: readable", output)
        self.assertIn("Shared mailbox shared@example.edu: readable", output)
        for private in (ACCESS, REFRESH, DEVICE["device_code"], "private-mailbox-id", "private-contact-id", "private-shared-id"):
            self.assertNotIn(private, output)
        requests = [c.args[0] for c in calls]
        self.assertEqual(len(requests), 10)
        self.assertEqual(requests[0].full_url, check.LEGACY_LOGIN + "/devicecode")
        self.assertEqual(requests[1].full_url, check.LEGACY_LOGIN + "/token")
        device_fields = parse_qs(requests[0].data.decode())
        token_fields = parse_qs(requests[1].data.decode())
        self.assertEqual(device_fields, {"client_id": [check.OUTLOOK_CLIENT_ID],
                                         "resource": [check.GRAPH_RESOURCE]})
        self.assertEqual(token_fields["code"], [DEVICE["device_code"]])
        self.assertNotIn("device_code", token_fields)
        self.assertEqual(token_fields["client_id"], [check.OUTLOOK_CLIENT_ID])
        for request in requests[2:]:
            self.assertEqual(request.method, "GET")
            self.assertIsNone(request.data)
            self.assertEqual(urlsplit(request.full_url).netloc, "graph.microsoft.com")
            query = parse_qs(urlsplit(request.full_url).query)
            self.assertIn("$select", query)
            self.assertNotIn("body", query["$select"][0])
            self.assertNotIn("subject", query["$select"][0])
            if urlsplit(request.full_url).path in {"/v1.0/me/contacts", "/v1.0/me/people"}:
                self.assertEqual(query["$top"], ["1"])

    def test_outlook_shared_mail_failure_does_not_hide_other_results(self):
        result, output, calls, _ = self.run_flow([
            DEVICE, OUTLOOK_TOKEN, {"mail": ACCOUNT}, CALENDAR,
            {"id": "inbox"}, {"timeZone": "UTC"}, {"value": []}, {"value": []},
            api_error({"code": "ErrorAccessDenied", "message": "Shared mailbox denied"}, status=403),
        ], ["--outlook", "--shared-mailbox", SHARED])
        self.assertEqual(result, 1)
        self.assertIn("Personal mailbox: readable", output)
        self.assertIn("Shared mailbox shared@example.edu: FAILED", output)
        self.assertEqual(len(calls), 9)

    def test_using_outlook_client_id_alone_does_not_relax_default_scope_guard(self):
        result, output, calls, _ = self.run_flow([DEVICE, OUTLOOK_TOKEN], ["--client-id", check.OUTLOOK_CLIENT_ID])
        self.assertEqual(result, 1)
        self.assertIn("Unexpected permissions", output)
        self.assertEqual(len(calls), 2)

    def test_outlook_rejects_wrong_resource_before_graph_access(self):
        for resource in ("https://outlook.office365.com", "https://graph.microsoft.com.example.org", ""):
            with self.subTest(resource=resource):
                result, output, calls, _ = self.run_flow([
                    DEVICE, dict(OUTLOOK_TOKEN, resource=resource),
                ], ["--outlook"])
                self.assertEqual(result, 1)
                self.assertIn("not identified", output)
                self.assertEqual(len(calls), 2)

    def test_outlook_missing_scope_fails_closed(self):
        token = dict(OUTLOOK_TOKEN)
        del token["scope"]
        result, output, calls, _ = self.run_flow([DEVICE, token], ["--outlook"])
        self.assertEqual(result, 1)
        self.assertIn("No granted permission list", output)
        self.assertEqual(len(calls), 2)

    def test_outlook_wrong_account_stops_all_calendar_and_mail_reads(self):
        result, output, calls, _ = self.run_flow([
            DEVICE, OUTLOOK_TOKEN, {"mail": "wrong@example.edu"},
        ], ["--outlook", "--shared-mailbox", SHARED])
        self.assertEqual(result, 1)
        self.assertIn("different account", output)
        self.assertEqual(len(calls), 3)

    def test_outlook_does_not_expand_the_allowlist_to_messages_events_or_files(self):
        with patch.object(check, "request_json") as request:
            for path in ("/me/messages", "/me/events", "/me/sendMail", "/me/drive/root",
                         "/me/mailFolders/inbox/messages", "/me/contacts?$expand=photo",
                         "/me/calendar?x=1", "https://example.org/"):
                with self.subTest(path=path), self.assertRaises(check.CheckError):
                    check.graph_get(ACCESS, path, outlook=True)
            request.assert_not_called()

    def test_default_mode_still_cannot_read_mailbox_or_contact_metadata(self):
        with patch.object(check, "request_json") as request:
            for path in ("/me/mailFolders/inbox", "/me/mailboxSettings", "/me/people", "/me/contacts"):
                with self.subTest(path=path), self.assertRaises(check.CheckError):
                    check.graph_get(ACCESS, path)
            request.assert_not_called()

    def test_outlook_permission_failure_does_not_try_another_app_or_auth_flow(self):
        result, output, calls, _ = self.run_flow([
            DEVICE, api_error("access_denied", "Tenant policy denied access"),
        ], ["--outlook"])
        self.assertEqual(result, 1)
        self.assertIn("Tenant policy denied access", output)
        self.assertEqual(len(calls), 2)

    def test_mutually_exclusive_auth_options_fail_before_network_access(self):
        with patch.object(check, "build_opener") as opener, \
                patch.object(check.sys, "stderr", io.StringIO()), \
                patch.object(check.sys, "argv", [str(SCRIPT), "--account", ACCOUNT,
                                                "--outlook", "--client-id", check.CLIENT_ID]):
            with self.assertRaises(SystemExit) as stopped:
                check.main()
            self.assertEqual(stopped.exception.code, 2)
            opener.assert_not_called()


if __name__ == "__main__":
    unittest.main()
