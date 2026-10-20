"""Find Teams meeting links without fetching or changing an event."""
import html
import re
import subprocess
from urllib.parse import parse_qs, urlsplit


def meeting_url(value, depth=0):
    value = html.unescape(value).strip()
    if depth > 3 or any(ord(c) < 32 or ord(c) == 127 for c in value):
        return None
    try:
        parts = urlsplit(value)
        if parts.scheme not in {"https", "msteams"} or parts.username or parts.password or parts.port:
            return None
        host = parts.hostname or ""
        if parts.scheme == "https" and host.endswith(".safelinks.protection.outlook.com"):
            target = parse_qs(parts.query).get("url", [""])[0]
            return meeting_url(target, depth + 1)
        if host not in {"teams.microsoft.com", "teams.live.com", "teams.cloud.microsoft"}:
            return None
        if not parts.path.startswith(("/l/meetup-join/", "/meet/")):
            return None
        return "https:" + value.split(":", 1)[1]
    except ValueError:
        return None


def find_meeting(*fields):
    for field in fields:
        for candidate in re.findall(r'(?:https|msteams)://[^\s<>"\']+', html.unescape(str(field or ""))):
            url = meeting_url(candidate.rstrip(".,;!)"))
            if url:
                return url
    return None


def event_meeting(event):
    vevent = event._vevents[event.ref]
    return find_meeting(event.url, vevent.get("X-MICROSOFT-SKYPETEAMSMEETINGURL"),
                        event.location, event.description, vevent.get("X-ALT-DESC"))


def open_meeting(url):
    url = meeting_url(url)
    if not url:
        raise ValueError("No Teams meeting link in this event.")
    # The Teams protocol opens the pre-join screen; joining is still manual.
    result = subprocess.run(["/usr/bin/open", "msteams:" + url[len("https:"):]],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode:
        subprocess.run(["/usr/bin/open", url], check=True)
