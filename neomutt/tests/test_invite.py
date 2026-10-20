"""Invitation responses use synthetic events and a fake gateway only."""

import copy
from contextlib import closing
from datetime import date, datetime, timedelta, timezone
from email.message import EmailMessage
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from icalendar import Calendar, Event, vCalAddress

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import invite

ACCOUNT = "me@example.test"


def event(uid="offline-invitation", status="NEEDS-ACTION", recurrence=None):
    item = Event()
    item.add("uid", uid)
    item.add("dtstamp", datetime(2026, 10, 19, 12, tzinfo=timezone.utc))
    item.add("dtstart", datetime(2026, 11, 2, 10, tzinfo=timezone.utc))
    item.add("dtend", datetime(2026, 11, 2, 11, tzinfo=timezone.utc))
    item.add("summary", "Synthetic invitation")
    item.add("description", "Keep this description and all other details.")
    item.add("sequence", 2)
    item.add("organizer", vCalAddress("mailto:host@example.test"), parameters={"CN": "Test Organizer"})
    item.add("attendee", vCalAddress("mailto:" + ACCOUNT), parameters={"PARTSTAT": status, "ROLE": "REQ-PARTICIPANT"})
    item.add("attendee", vCalAddress("mailto:other@example.test"), parameters={"PARTSTAT": "ACCEPTED"})
    if recurrence is not None:
        item.add("recurrence-id", recurrence)
    return item


def calendar(*events, method=None):
    result = Calendar()
    result.add("version", "2.0")
    result.add("prodid", "-//Offline tests//EN")
    if method:
        result.add("method", method)
    for item in events:
        result.add_component(item)
    return result


def message(item=None, method="REQUEST"):
    result = EmailMessage()
    result["From"] = "host@example.test"
    result["To"] = ACCOUNT
    result["Subject"] = "Synthetic invitation"
    result.set_content("Synthetic mail only.")
    result.add_alternative("<h1>Synthetic invitation</h1>", subtype="html")
    result.add_alternative(calendar(item or event(), method=method).to_ical().decode(), subtype="calendar")
    return result


class FakeClient:
    account = ACCOUNT

    def __init__(self, resource=None):
        self.calendar = resource or calendar(event())
        self.etag = '"version-one"'
        self.writes = []
        self.error = None

    def locate(self, request):
        return "/users/me/calendar/test.ics", self.etag, copy.deepcopy(self.calendar)

    def get(self, href):
        return self.etag, copy.deepcopy(self.calendar)

    def request(self, method, href, body, etag):
        self.writes.append((method, href, body, etag))
        if self.error:
            raise self.error
        selected = Calendar.from_ical(body).walk("VEVENT")[0]
        for item in self.calendar.walk("VEVENT"):
            if invite.recurrence(item) == invite.recurrence(selected):
                invite.own_attendee(item, ACCOUNT).params["PARTSTAT"] = invite.own_attendee(selected, ACCOUNT).params["PARTSTAT"]
        self.etag = '"version-two"'
        return 200, None, b""


class PreviewTests(unittest.TestCase):
    def test_details_and_description_are_readable_without_calendar_access(self):
        item = event()
        item.add("location", "Test room")
        raw = calendar(item, method="REQUEST").to_ical()
        with patch.object(invite, "configured_client", side_effect=AssertionError("Preview contacted calendar")), \
                patch.object(invite.subprocess, "run", side_effect=AssertionError("Preview ran a command")):
            text = invite.preview(raw)
        for expected in ("Synthetic invitation", "Test Organizer <host@example.test>",
                         "11:00 CET", "12:00 CET", "Where: Test room", "me@example.test",
                         "Not answered", "Keep this description"):
            self.assertIn(expected, text)
        self.assertEqual(raw, calendar(item, method="REQUEST").to_ical())

    def test_cancelled_all_day_and_floating_events_can_still_be_viewed(self):
        item = event()
        item["DTSTART"].dt = date(2026, 11, 2)
        item["DTEND"].dt = date(2026, 11, 4)
        text = invite.preview(calendar(item, method="CANCEL").to_ical())
        self.assertIn("Status: Cancelled", text)
        self.assertIn("Mon 02 Nov 2026 – Tue 03 Nov 2026 (all day)", text)
        item["DTSTART"].dt = datetime(2026, 11, 2, 10)
        item["DTEND"].dt = datetime(2026, 11, 2, 11)
        self.assertIn("time zone unspecified", invite.preview(calendar(item, method="PUBLISH").to_ical()))

    def test_terminal_controls_are_removed(self):
        item = event()
        item["SUMMARY"] = "Untrusted \x1b[31m meeting"
        item["DESCRIPTION"] = "Line one\n\x1b]52;c;payload\x07\nLine two"
        text = invite.preview(calendar(item).to_ical())
        self.assertNotIn("\x1b", text)
        self.assertNotIn("\x07", text)
        self.assertIn("Line two", text)

    def test_cli_preview_needs_no_config_or_password_and_keeps_source(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "meeting with spaces.ics"
            raw = calendar(event(), method="REQUEST").to_ical()
            path.write_bytes(raw)
            script = Path(__file__).resolve().parents[1] / "scripts/neomutt-invite"
            env = {**os.environ, "HOME": directory, "XDG_CONFIG_HOME": directory,
                   "XDG_STATE_HOME": directory, "XDG_CACHE_DIR": directory}
            result = subprocess.run([str(script), "preview", str(path)], env=env,
                                    capture_output=True, text=True, check=True, timeout=5)
            self.assertIn("Synthetic invitation", result.stdout)
            self.assertFalse(result.stderr)
            self.assertEqual(path.read_bytes(), raw)
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_calendar_only_html_view_uses_the_same_preview(self):
        import test_html
        mail = EmailMessage()
        mail.set_content(calendar(event(), method="REQUEST").to_ical().decode(), subtype="calendar")
        with tempfile.TemporaryDirectory() as directory:
            text = test_html.viewer.message_html(mail, Path(directory))
        self.assertIn("Synthetic invitation", text)
        self.assertIn("&lt;host@example.test&gt;", text)
        self.assertNotIn("BEGIN:VCALENDAR", text)

    def test_malformed_empty_and_oversized_calendars_fail_without_action(self):
        for raw in (b"not a calendar", calendar().to_ical(), b"x" * (invite.MAX_SIZE + 1)):
            with self.assertRaises(invite.InviteError):
                invite.preview(raw)


class InvitationTests(unittest.TestCase):
    def test_raw_mime_calendar(self):
        parsed = invite.invitation(message().as_bytes())
        self.assertEqual(str(parsed["UID"]), "offline-invitation")

    def test_application_ics_without_filename(self):
        mail = EmailMessage()
        mail.set_content(calendar(event(), method="REQUEST").to_ical(), maintype="application", subtype="ics")
        self.assertEqual(str(invite.invitation(mail.as_bytes())["UID"]), "offline-invitation")

    def test_duplicate_calendar_part_is_one_invitation(self):
        mail = message()
        payload = mail.get_payload()[-1].get_payload(decode=True)
        mail.add_attachment(payload, maintype="application", subtype="octet-stream", filename="invite.ics")
        self.assertEqual(str(invite.invitation(mail.as_bytes())["UID"]), "offline-invitation")

    def test_cancellation_reply_and_plain_mail_are_rejected(self):
        for method in ("CANCEL", "REPLY", "PUBLISH"):
            with self.assertRaises(invite.InviteError):
                invite.invitation(message(method=method).as_bytes())
        with self.assertRaises(invite.InviteError):
            invite.invitation(b"Subject: No invitation\n\nNothing here")

    def test_attached_forwarded_invitation_is_not_answered(self):
        mail = EmailMessage()
        mail.set_content("Forwarded mail")
        mail.add_attachment(message())
        with self.assertRaises(invite.InviteError):
            invite.invitation(mail.as_bytes())

    def test_unrelated_invitation_parts_are_ambiguous(self):
        mail = message()
        mail.add_attachment(calendar(event("different"), method="REQUEST").to_ical(),
                            maintype="text", subtype="calendar", filename="other.ics")
        with self.assertRaises(invite.InviteError):
            invite.invitation(mail.as_bytes())

    def test_server_without_sequence_or_original_stamp_matches(self):
        requested = event()
        server = copy.deepcopy(requested)
        del server["SEQUENCE"]
        server["DTSTAMP"].dt += timedelta(minutes=3)
        from zoneinfo import ZoneInfo
        server["DTSTART"].dt = server["DTSTART"].dt.astimezone(ZoneInfo("Europe/Amsterdam"))
        self.assertIs(invite.matching_event(requested, calendar(server), ACCOUNT), server)

    def test_changed_meeting_or_ownership_is_rejected(self):
        for key, value in (("UID", "different"), ("SUMMARY", "Changed"),
                           ("ORGANIZER", vCalAddress("mailto:stranger@example.test")),
                           ("STATUS", "CANCELLED"), ("SEQUENCE", 3)):
            server = event()
            server[key] = value
            with self.subTest(key=key), self.assertRaises(invite.InviteError):
                invite.matching_event(event(), calendar(server), ACCOUNT)
        moved = event()
        moved["DTSTART"].dt += timedelta(hours=1)
        with self.assertRaises(invite.InviteError):
            invite.matching_event(event(), calendar(moved), ACCOUNT)

    def test_only_invited_account_can_respond(self):
        for account in ("else@example.test", "host@example.test"):
            with self.assertRaises(invite.InviteError):
                invite.matching_event(event(), calendar(event()), account)

    def test_response_changes_only_self_status_and_one_component(self):
        master = event()
        master.add("rrule", {"freq": "weekly"})
        exception = event(status="ACCEPTED", recurrence=datetime(2026, 11, 9, 10, tzinfo=timezone.utc))
        original = calendar(master, exception)
        before = original.to_ical()
        reply = Calendar.from_ical(invite.response_body(original, master, ACCOUNT, "TENTATIVE"))
        self.assertEqual(len(reply.walk("VEVENT")), 1)
        selected = reply.walk("VEVENT")[0]
        self.assertEqual(str(invite.own_attendee(selected, ACCOUNT).params["PARTSTAT"]), "TENTATIVE")
        invite.own_attendee(selected, ACCOUNT).params["PARTSTAT"] = "NEEDS-ACTION"
        self.assertEqual(selected.to_ical(), master.to_ical())
        self.assertEqual(original.to_ical(), before)

    def test_occurrence_response_does_not_include_series_master(self):
        master = event()
        master.add("rrule", {"freq": "weekly"})
        occurrence = event(recurrence=datetime(2026, 11, 9, 10, tzinfo=timezone.utc))
        resource = calendar(master, occurrence)
        selected = invite.matching_event(occurrence, resource, ACCOUNT)
        result = Calendar.from_ical(invite.response_body(resource, selected, ACCOUNT, "DECLINED"))
        self.assertEqual(len(result.walk("VEVENT")), 1)
        self.assertEqual(invite.recurrence(result.walk("VEVENT")[0]), invite.recurrence(occurrence))
        self.assertIn("This occurrence", invite.details(selected, ACCOUNT))
        self.assertIn("Entire series", invite.details(master, ACCOUNT))

    def test_missing_or_range_occurrence_stops(self):
        request = event(recurrence=datetime(2026, 11, 9, 10, tzinfo=timezone.utc))
        with self.assertRaises(invite.InviteError):
            invite.matching_event(request, calendar(event()), ACCOUNT)
        request["RECURRENCE-ID"].params["RANGE"] = "THISANDFUTURE"
        with self.assertRaises(invite.InviteError):
            invite.recurrence(request)

    def test_all_day_invitation_has_inclusive_display_and_default_duration(self):
        request = event()
        del request["DTSTART"], request["DTEND"]
        request.add("dtstart", date(2026, 11, 2))
        server = copy.deepcopy(request)
        server.add("dtend", date(2026, 11, 3))
        invite.matching_event(request, calendar(server), ACCOUNT)
        header = invite.details(server, ACCOUNT)
        self.assertIn("Mon 02 Nov 2026 (all day)", header)
        self.assertNotIn("03 Nov", header)


class ResponseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name)
        self.request = event()
        self.client = FakeClient()
        self.href, self.etag, self.shown = self.client.locate(self.request)

    def reply(self, choice="ACCEPTED"):
        return invite.reply(self.client, self.request, self.href, self.etag, self.shown, choice, self.state)

    def test_all_three_actions_send_one_put_and_no_duplicate(self):
        for choice in invite.RESPONSES:
            with self.subTest(choice=choice):
                self.assertIn("submitted", self.reply(choice))
                count = len(self.client.writes)
                self.assertIn("already submitted", self.reply(choice))
                self.assertEqual(len(self.client.writes), count)
                method, path, body, etag = self.client.writes[-1]
                self.assertEqual(method, "PUT")
                self.assertEqual(path, self.href)
                selected = Calendar.from_ical(body).walk("VEVENT")[0]
                self.assertEqual(invite.own_attendee(selected, ACCOUNT).params["PARTSTAT"], choice)
                self.etag, self.shown = self.client.get(self.href)
        self.assertEqual(len(self.client.writes), 3)

    def test_already_accepted_is_noop(self):
        invite.own_attendee(self.client.calendar.walk("VEVENT")[0], ACCOUNT).params["PARTSTAT"] = "ACCEPTED"
        self.assertIn("Already accepted", self.reply())
        self.assertFalse(self.client.writes)

    def test_event_changed_while_reviewing_is_not_sent(self):
        self.client.etag = '"new-version"'
        with self.assertRaises(invite.InviteError):
            self.reply()
        self.assertFalse(self.client.writes)

    def test_changed_body_even_with_same_etag_stops(self):
        self.client.calendar.walk("VEVENT")[0]["DESCRIPTION"] = "Changed details"
        with self.assertRaises(invite.InviteError):
            self.reply()
        self.assertFalse(self.client.writes)

    def test_timeout_is_never_retried(self):
        self.client.error = TimeoutError()
        with self.assertRaisesRegex(invite.InviteError, "may have been sent"):
            self.reply()
        self.client.error = None
        with self.assertRaisesRegex(invite.InviteError, "uncertain result"):
            self.reply()
        self.assertEqual(len(self.client.writes), 1)
        self.assertEqual(json.loads(next(self.state.glob("*.json")).read_text())["status"], "pending")

    def test_both_cancel_stages_send_nothing(self):
        for selections in ([None], ["cancel"], ["ACCEPTED", None], ["DECLINED", "cancel"]):
            with patch.object(invite, "choose", side_effect=selections), patch.object(invite, "reply") as reply:
                invite.run(message().as_bytes(), self.client)
            reply.assert_not_called()
        self.assertFalse(self.client.writes)

    def test_confirmed_menu_sends_the_selected_response(self):
        with patch.object(invite, "choose", side_effect=["TENTATIVE", "send"]), patch.object(
            invite, "state_directory", return_value=self.state
        ), patch.object(invite, "notice") as notice:
            invite.run(message().as_bytes(), self.client)
        self.assertEqual(len(self.client.writes), 1)
        self.assertIn("submitted", notice.call_args.args[0])


class GatewayTests(unittest.TestCase):
    def test_reader_and_invite_pipe_settings_parse_and_restore(self):
        scripts = Path(__file__).resolve().parents[1] / "scripts"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env = {**os.environ, "XDG_CACHE_DIR": directory}
            for script, restore_name in (("neomutt-invite", "restore.rc"), ("neomutt-view", "actions.rc")):
                commands = subprocess.run([str(scripts / script), "prepare"], env=env,
                                          capture_output=True, text=True, check=True).stdout
                restore = next(root.glob("**/" + restore_name))
                config = root / "muttrc"
                config.write_text('set pipe_decode=yes auto_tag=yes wait_key=yes\n' + commands
                                  + '\nsource "' + str(restore) + '"\n')
                result = subprocess.run(["/opt/homebrew/bin/neomutt", "-n", "-F", str(config),
                                         "-Q", "pipe_decode", "-Q", "auto_tag", "-Q", "wait_key"],
                                        capture_output=True, text=True, check=True)
                self.assertFalse(result.stderr)
                self.assertEqual(result.stdout.count("= yes"), 3)

    def test_sync_mapping_uses_remote_href_not_local_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "calendar.items"
            with closing(sqlite3.connect(path)) as database, database:
                database.execute("CREATE TABLE status (ident TEXT, href_b TEXT)")
                database.execute("INSERT INTO status VALUES (?, ?)", ("offline-invitation", "/users/me/calendar/server-id.ics"))
            before = path.read_bytes()
            client = invite.Client("http://127.0.0.1:1/users/me/calendar/", ACCOUNT, "fake", path)
            with patch.object(client, "request", return_value=(200, '"etag"', calendar(event()).to_ical())) as request:
                href, _, _ = client.locate(event())
            self.assertEqual(href, "/users/me/calendar/server-id.ics")
            request.assert_called_once_with("GET", href)
            self.assertEqual(path.read_bytes(), before)

    def test_unsynced_report_is_filtered_locally_and_refuses_ambiguity(self):
        from xml.sax.saxutils import escape
        def response(uid, href):
            return ('<d:response><d:href>' + href + '</d:href><d:propstat><d:prop>'
                    '<c:calendar-data>' + escape(calendar(event(uid)).to_ical().decode())
                    + '</c:calendar-data></d:prop><d:status>HTTP/1.1 200 OK</d:status></d:propstat></d:response>')
        start = '<d:multistatus xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">'
        first = response("offline-invitation", "/users/me/calendar/right.ics")
        other = response("unrelated", "/users/me/calendar/other.ics")
        client = invite.Client("http://127.0.0.1:1/users/me/calendar/", ACCOUNT, "fake")
        with patch.object(client, "request", side_effect=[
            (207, None, (start + first + other + '</d:multistatus>').encode()),
            (200, '"etag"', calendar(event()).to_ical()),
        ]) as request:
            href, _, _ = client.locate(event())
        self.assertEqual(href, "/users/me/calendar/right.ics")
        self.assertEqual([call.args[0] for call in request.call_args_list], ["REPORT", "GET"])
        self.assertIn(b'time-range start="20261101T100000Z" end="20261103T100000Z"', request.call_args_list[0].args[2])
        duplicate = response("offline-invitation", "/users/me/calendar/duplicate.ics")
        with patch.object(client, "request", return_value=(207, None, (start + first + duplicate + '</d:multistatus>').encode())):
            with self.assertRaises(invite.InviteError):
                client.locate(event())

    def test_read_only_mode_refuses_put_before_connecting(self):
        client = invite.Client("http://127.0.0.1:1/users/me/calendar/", ACCOUNT, "fake", read_only=True)
        with patch.object(invite.http.client, "HTTPConnection") as connection:
            with self.assertRaises(invite.InviteError):
                client.request("PUT", "one.ics", b"anything", '"etag"')
        connection.assert_not_called()

    def test_paths_cannot_leave_the_calendar_or_leak_credentials(self):
        client = invite.Client("http://127.0.0.1:1/users/me/calendar/", ACCOUNT, "fake")
        for path in ("http://example.test/item.ics", "//example.test/item.ics", "../other/item.ics",
                     "%2e%2e/item.ics", "sub%2fitem.ics", "one.ics?query=1", "one.ics#fragment", "bad%0afile.ics"):
            with self.subTest(path=path), self.assertRaises(invite.InviteError):
                client.path(path)
        self.assertEqual(client.path("a%20file.ics"), "/users/me/calendar/a%20file.ics")


if __name__ == "__main__":
    unittest.main()
