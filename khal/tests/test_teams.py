"""Meeting links are opened only through mocks, never joined during tests."""
from pathlib import Path
import json
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from urllib.parse import quote, unquote

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import teams
import personal
import test_personal

URL = 'https://teams.microsoft.com/l/meetup-join/fixture/0?context=%7B%22Tid%22%3A%22test%22%7D'


class MeetingTests(unittest.TestCase):
    def test_text_html_and_safelinks(self):
        safe = 'https://example.safelinks.protection.outlook.com/?url=' + quote(URL, safe='') + '&data=test'
        for value in (URL, '(' + URL + ').', '<a href="' + URL + '">Join</a>', safe,
                      '<a href="' + safe.replace('&', '&amp;') + '">Join</a>'):
            self.assertEqual(teams.find_meeting('Room 1', value), URL)
        self.assertEqual(teams.find_meeting('https://teams.microsoft.com/meet/123?p=test'),
                         'https://teams.microsoft.com/meet/123?p=test')

    def test_rejects_nonmeeting_urls_and_malformed_links(self):
        for url in ('https://example.test/meet/123', 'https://teams.microsoft.com.evil.test/meet/123',
                    'https://teams.microsoft.com@evil.test/meet/123', 'file:///tmp/meet/123',
                    'https://teams.microsoft.com/chat', 'https://[bad', URL + '\nmalformed',
                    'https://teams.microsoft.com:bad/meet/123'):
            self.assertIsNone(teams.meeting_url(url))

    def test_native_open_and_browser_fallback(self):
        with patch.object(teams.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as run:
            teams.open_meeting(URL)
        self.assertEqual(run.call_args.args[0], ['/usr/bin/open', URL.replace('https:', 'msteams:', 1)])
        with patch.object(teams.subprocess, 'run', side_effect=[subprocess.CompletedProcess([], 1),
                                                               subprocess.CompletedProcess([], 0)]) as run:
            teams.open_meeting(URL)
        self.assertEqual(run.call_args.args[0], ['/usr/bin/open', URL])

    def test_J_uses_selected_event_and_keeps_no_link_in_calendar(self):
        event = SimpleNamespace(url='', location='', description=URL, ref='0', _vevents={'0': {}})
        column = SimpleNamespace(focus_event=SimpleNamespace(event=event),
                                 pane=SimpleNamespace(window=SimpleNamespace(alert=Mock())))
        with patch.object(personal, 'open_meeting') as open_meeting:
            self.assertIsNone(personal.EventColumn.keypress(column, (100, 30), 'J'))
            open_meeting.assert_called_once_with(URL)
            event.description = ''
            personal.EventColumn.keypress(column, (100, 30), 'J')
            self.assertEqual(open_meeting.call_count, 1)
        column.pane.window.alert.assert_called_once_with('No Teams meeting link in this event.')

    def test_ics_roundtrip_and_outlook_extension(self):
        fixture = test_personal.OrganizerTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        event = fixture.new()
        event.update_description('Join: ' + URL)
        saved = fixture.save(event)
        self.assertEqual(unquote(teams.event_meeting(saved)), unquote(URL))
        event.update_description('')
        event._vevents[event.ref]['X-MICROSOFT-SKYPETEAMSMEETINGURL'] = URL
        self.assertEqual(teams.event_meeting(event), URL)
        fixture.collection.update(event)
        root = Path(fixture.temp.name)
        date = event.start.strftime(test_personal.get_config(str(root / 'config'))['locale']['longdateformat'])
        result = subprocess.run([str(Path(__file__).resolve().parents[1] / 'scripts/khal-personal'),
                                 '-c', str(root / 'config'), 'list', date, '1d',
                                 '--json', 'teams-url', '--day-format', ''],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(unquote(json.loads(result.stdout)[0]['teams-url']), unquote(URL))
