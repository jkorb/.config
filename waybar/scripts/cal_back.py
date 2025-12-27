#! /usr/bin/python3

import subprocess
from datetime import datetime, timedelta, date
import json
import html
import sys

import calendar as cal

LOGO_BLANK = "\udb80\udcee"
LOGO_EVENT = "\udb80\udced"
LOGO_REMINDER = "\udb80\udc20"
CLOCK_ITEM = "\U000023F0"
CONTINUE_LOGO = "\U000021AA"
CALENDAR_ITEM = "\U0001F4C5"
SMILEY = "\U0001F60E"
ERROR_MESSAGE = "<span color='#e06c75'>Error</span>"

KHAL_FORMAT = "{{\"start\":\"{start}\",\"end\":\"{end}\",\"title\":\"{title}\"}}"
KHAL_CMD = ['khal', 'list', 'now', '23:59', '--format', KHAL_FORMAT, '--day-format', '']

def sanitize_title(title: str):
    return html.escape(title)

def call_process(cmd: list, out: dict):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if p.returncode != 0:
        stderr = p.stderr.strip()
        cmd_str = " ".join(cmd)
        raise Exception(f"<span color='#e06c75'>Error</span>: '{cmd_str}' returned {p.returncode}\n\nstderr: {stderr}")

    return p

def get_current_time():
    return datetime.now()

def format_datetime(dt):
    return dt.strftime('%H:%M')

def format_date(dt):
    return dt.strftime('%a, %b %d, %R')

def main():
    out = {'text': '', 'tooltip': ''}
    cur_time = get_current_time()

    try:
        p = call_process(KHAL_CMD, out)

        if not p.stdout:
            out['text'] = format_date(cur_time)
            out['tooltip'] = f"{SMILEY} No upcoming appointments."
            return json.dumps(out, indent=None, separators=(",", ": "))

        out['text'] = format_date(cur_time)
        stdout_lines = p.stdout.splitlines()

        for line in stdout_lines:
            appt = json.loads(line)
            start, end, title = appt['start'], appt['end'], sanitize_title(appt['title'])

            try:
                start = datetime.strptime(start, '%d/%m/%Y %H:%M')
                end = datetime.strptime(end, '%d/%m/%Y %H:%M')
                reminder_flag = (start - timedelta(minutes=15) <= cur_time <= start)
                out['tooltip'] += f"{CLOCK_ITEM} {format_datetime(start)}-{format_datetime(end)}: {title}\n"

            except ValueError:
                out['tooltip'] += f"{ERROR_MESSAGE} processing appointment\n"

        if 'reminder_flag' in locals() and reminder_flag:
            out['text'] += f"<span color='#cf6679'>{LOGO_REMINDER}</span>"

    except Exception as e:
        sys.stderr.write(str(e) + "\n")
        sys.exit(1)

    return json.dumps(out, indent=None, separators=(",", ": "))

if __name__ == "__main__":
    print(main())
