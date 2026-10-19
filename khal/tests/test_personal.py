"""Exercise the local additions against the installed khal, using temporary calendars."""

import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import uuid

from icalendar import vCalAddress
from khal.cli_utils import build_collection
from khal.settings import get_config

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import personal
import contacts

personal.install()


class OrganizerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        config = root / "config"
        config.write_text(f"""[calendars]
[[uu]]
path = {root}/uu
addresses = me@example.org
[[private]]
path = {root}/private
[default]
default_calendar = uu
[locale]
default_timezone = Europe/Amsterdam
local_timezone = Europe/Amsterdam
[sqlite]
path = {root}/khal.db
""")
        self.collection = build_collection(get_config(str(config)), None)
        self.addCleanup(self.collection._backend.conn.close)

    def new(self, calendar="uu"):
        return self.collection.create_event_from_dict({
            "dtstart": dt.datetime(2027, 1, 18, 10),
            "dtend": dt.datetime(2027, 1, 18, 11),
            "summary": "Offline fixture",
        }, calendar)

    def imported(self, organizer=""):
        raw = (
            "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\n"
            f"UID:{uuid.uuid4()}\r\nDTSTART:20270118T100000Z\r\n"
            "DTEND:20270118T110000Z\r\nSUMMARY:Imported fixture\r\n"
            "ATTENDEE:mailto:me@example.org\r\n"
            + (f"ORGANIZER:mailto:{organizer}\r\n" if organizer else "")
            + "END:VEVENT\r\nEND:VCALENDAR\r\n"
        )
        return self.collection.create_event_from_ics(raw, "uu")

    def save(self, event, calendar=None):
        self.collection.insert(event, calendar)
        return self.collection.get_event(event.href, calendar or event.calendar)

    def test_new_uu_meeting_has_organizer_after_save(self):
        event = self.new()
        event.update_attendees(["guest@example.org"])
        saved = self.save(event)
        self.assertEqual(saved.organizer, "me@example.org")
        self.assertEqual(saved.attendees, "guest@example.org")
        self.assertEqual(saved.start, event.start)

    def test_new_appointment_gets_organizer_before_attendees_are_added(self):
        self.assertEqual(self.save(self.new()).organizer, "me@example.org")

    def test_other_calendars_are_unchanged(self):
        self.assertEqual(self.save(self.new("private")).organizer, "")
        self.assertEqual(self.save(self.new(), "private").organizer, "")

    def test_selected_calendar_controls_organizer(self):
        self.assertEqual(self.save(self.new("private"), "uu").organizer, "me@example.org")

    def test_imported_invitation_keeps_organizer(self):
        self.assertEqual(self.save(self.imported("host@example.org")).organizer, "host@example.org")

    def test_missing_organizer_on_import_is_not_claimed(self):
        self.assertEqual(self.save(self.imported()).organizer, "")

    def test_existing_organizer_is_preserved(self):
        event = self.new()
        event._vevents[event.ref].add("organizer", vCalAddress("mailto:host@example.org"))
        self.assertEqual(self.save(event).organizer, "host@example.org")

    def test_trailing_separator_does_not_create_empty_attendee(self):
        event = self.new()
        event.update_attendees(["jane@example.org", "john@example.org", " "])
        self.assertEqual(self.save(event).attendees, "jane@example.org, john@example.org")

    def test_existing_single_attendee_keeps_invitation_parameters(self):
        event = self.imported("host@example.org")
        attendee = event._vevents[event.ref]["ATTENDEE"]
        attendee.params.update(PARTSTAT="ACCEPTED", ROLE="OPT-PARTICIPANT", CN="My Name")
        # Both MAILTO and mailto are valid in incoming invitations.
        for prefix in ("MAILTO:", "mailto:"):
            old = vCalAddress(prefix + "me@example.org")
            old.params.update(attendee.params)
            event._vevents[event.ref]["ATTENDEE"] = old
            event.update_attendees(["ME@example.org", "new@example.org", " "])
            kept = event._vevents[event.ref]["ATTENDEE"][0]
            self.assertIs(kept, old)
            self.assertEqual(str(kept.params["PARTSTAT"]), "ACCEPTED")
            self.assertEqual(str(kept.params["ROLE"]), "OPT-PARTICIPANT")
        event.update_attendees([" ", ""])
        self.assertNotIn("ATTENDEE", event._vevents[event.ref])


class CompletionTests(unittest.TestCase):
    def field(self, text):
        window = Mock()
        editor = SimpleNamespace(pane=SimpleNamespace(window=window))
        return personal.AttendeesEdit(editor, edit_text=text), window

    def test_replace_middle_attendee_preserves_neighbors(self):
        field, _ = self.field("one@example.org, Ja, three@example.org")
        field.set_edit_pos(len("one@example.org, Ja"))
        left, right = personal.attendee_span(field.edit_text, field.edit_pos)
        field.insert_address(left, right, "jane@example.org")
        self.assertEqual(field.edit_text, "one@example.org, jane@example.org, three@example.org")

    def test_blank_tab_opens_picker_and_inserts_multiple_choices(self):
        field, window = self.field("present@example.org, ")
        with patch.object(personal, "pick_contacts", return_value=["jane@example.org", "john@example.org"]) as pick:
            field.keypress((80,), "tab")
        pick.assert_called_once_with("", ["present@example.org", ""])
        self.assertEqual(field.edit_text, "present@example.org, jane@example.org, john@example.org, ")
        self.assertEqual(field.edit_pos, len(field.edit_text))
        window.loop.screen.stop.assert_called_once()
        window.loop.screen.start.assert_called_once()
        window.loop.screen.clear.assert_called_once()

    def test_cancellation_and_failure_keep_text_and_restore_calendar(self):
        for error in (None, OSError, ValueError):
            field, window = self.field("Ja")
            with patch.object(personal, "pick_contacts", return_value=[], side_effect=error):
                field.keypress((80,), "tab")
            self.assertEqual(field.edit_text, "Ja")
            window.loop.screen.start.assert_called_once()
            window.loop.screen.clear.assert_called_once()
            self.assertEqual(window.alert.call_count, int(error is not None))


class ContactsTests(unittest.TestCase):
    def test_initial_order_uses_personal_recency_then_frequency(self):
        rows = [
            {"name": "Old", "email": "old@example.org", "personal": True, "last-seen": 1, "frequency": 999},
            {"name": "Recent", "email": "recent@example.org", "personal": True, "last-seen": 3, "frequency": 2},
            {"name": "List", "email": "list@example.org", "personal": False, "last-seen": 9, "frequency": 9999},
            {"name": "Frequent", "email": "frequent@example.org", "personal": True, "last-seen": 3, "frequency": 8},
        ]
        with patch.object(contacts.subprocess, "run", return_value=Mock(returncode=0, stdout=json.dumps(rows))):
            found = contacts.local_contacts([])
        self.assertEqual([name for name, _ in found], ["Frequent", "Recent", "Old", "List"])

    def test_deduplication_exclusion_and_terminal_controls(self):
        result = contacts.unique_contacts([
            ("Jane\nDoe\x1b", "jane@example.org"), ("Duplicate", "JANE@example.org"),
            ("Present", "present@example.org"), ("Invalid", "bad, address"),
            (None, "unnamed@example.org"),
        ], ["PRESENT@example.org"])
        self.assertEqual(result, [("Jane Doe", "jane@example.org"), ("", "unnamed@example.org")])

    def test_directory_query_is_passed_literally(self):
        query = "O'Name; $(touch /tmp/should-not-exist)"
        with patch.object(contacts.subprocess, "run", return_value=Mock(stdout='[{"Jane":"jane@example.org"}]')) as run:
            self.assertEqual(contacts.directory_contacts(query, []), [("Jane", "jane@example.org")])
        self.assertEqual(run.call_args.args[0][-1], query)
        self.assertNotIn("shell", run.call_args.kwargs)

    def test_short_query_does_not_lookup_directory(self):
        with patch.object(contacts.subprocess, "run") as run:
            self.assertEqual(contacts.directory_contacts("Jo", []), [])
        run.assert_not_called()

    def test_directory_failure_preserves_local_stream(self):
        from concurrent.futures import Future
        pending = Future()
        pending.set_exception(OSError("offline"))
        process = Mock()
        process.poll.side_effect = [None, None, None, 0]
        with patch.object(contacts, "ThreadPoolExecutor") as pool, patch.object(
            contacts, "current_query", return_value="Jane"
        ), patch.object(contacts.time, "sleep"), patch.object(contacts.time, "monotonic", side_effect=range(20)):
            pool.return_value.submit.return_value = pending
            contacts.feed_directory(process, "/unused", [("Jane", "jane@example.org")], [])
        process.stdin.write.assert_called_once_with("jane@example.org\tJane <jane@example.org>\n")
        pool.return_value.shutdown.assert_called_once_with(wait=False, cancel_futures=True)

    def test_directory_results_are_appended_once_without_reloading(self):
        from concurrent.futures import Future
        pending = Future()
        pending.set_result([("Jane", "JANE@example.org"), ("John", "john@example.org")])
        process = Mock()
        process.poll.side_effect = [None, None, None, 0]
        with patch.object(contacts, "ThreadPoolExecutor") as pool, patch.object(
            contacts, "current_query", return_value="John"
        ), patch.object(contacts.time, "sleep"), patch.object(contacts.time, "monotonic", side_effect=range(20)):
            pool.return_value.submit.return_value = pending
            contacts.feed_directory(process, "/unused", [("Jane", "jane@example.org")], [])
        self.assertEqual([call.args[0] for call in process.stdin.write.call_args_list], [
            "jane@example.org\tJane <jane@example.org>\n", "john@example.org\tJohn <john@example.org>\n"])


if __name__ == "__main__":
    unittest.main()
