"""Calendar reminders with fake events and no notifications or meetings opened."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
loader = importlib.machinery.SourceFileLoader('calendar_notify', str(ROOT / 'launchd/scripts/vdirsyncer-sync'))
spec = importlib.util.spec_from_loader(loader.name, loader)
calendar = importlib.util.module_from_spec(spec)
with patch.dict(os.environ, XDG_CONFIG_HOME=str(ROOT)):
    loader.exec_module(calendar)


class CalendarNotifyTests(unittest.TestCase):
    def test_teams_action_and_ordinary_event_activation(self):
        url = 'https://teams.microsoft.com/meet/123?p=fixture'
        events = [dict(title='Teams fixture', calendar='uu', **{'teams-url': url}),
                  dict(title='Local fixture', calendar='private', location='Home')]
        with patch.object(calendar.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, json.dumps(events))) as fetch, \
             patch.object(calendar, 'load_cache', return_value={'notified': []}), \
             patch.object(calendar, 'save_cache') as save, patch.object(calendar, 'run_cmd') as notify:
            calendar.notify_upcoming()
        self.assertIn('teams-url', fetch.call_args.args[0])
        teams, ordinary = [call.args[0] for call in notify.call_args_list]
        self.assertEqual(shlex.split(teams[teams.index('-execute') + 1]), [calendar.TEAMS_JOIN, url])
        self.assertNotIn('-activate', teams)
        self.assertIn('-activate', ordinary)
        self.assertNotIn('-execute', ordinary)
        self.assertEqual(len(save.call_args.args[0]['notified']), 2)

    def test_already_notified_event_is_not_reposted(self):
        event = {'title': 'Fixture', 'calendar': 'uu', 'start-time': '10:00'}
        with patch.object(calendar.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, json.dumps([event]))), \
             patch.object(calendar, 'load_cache', return_value={'notified': ['10:00|Fixture|uu']}), \
             patch.object(calendar, 'run_cmd') as notify:
            calendar.notify_upcoming()
        notify.assert_not_called()
