"""Respond to an existing UU invitation through the local DavMail calendar."""

import base64
import configparser
import copy
from datetime import date, datetime, timedelta, timezone
from email import policy
from email.parser import BytesParser
import fcntl
import hashlib
import http.client
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
from urllib.parse import quote, unquote, urljoin, urlsplit
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

from icalendar import Calendar

CONFIG = Path(__file__).resolve().parents[2]
MAX_SIZE = 20 * 1024 * 1024
DAV = "{DAV:}"
CALDAV = "{urn:ietf:params:xml:ns:caldav}"
RESPONSES = {"ACCEPTED": "Accept", "TENTATIVE": "Tentative", "DECLINED": "Decline"}
STATUSES = {"NEEDS-ACTION": "Not answered", "ACCEPTED": "Accepted",
            "TENTATIVE": "Tentative", "DECLINED": "Declined"}


class InviteError(Exception):
    pass


def clean(value):
    return " ".join("".join(c for c in str(value) if c.isprintable() or c.isspace()).split())


def address(value):
    text = str(value or "")
    if not text.lower().startswith("mailto:"):
        raise InviteError("The invitation has an unsupported calendar address.")
    text = text[7:]
    if text.count("@") != 1 or any(c.isspace() or not c.isprintable() for c in text):
        raise InviteError("The invitation has an invalid calendar address.")
    return text.casefold()


def own_attendee(event, account):
    attendees = event.get("ATTENDEE", [])
    if not isinstance(attendees, list):
        attendees = [attendees]
    found = [item for item in attendees if address(item) == account.casefold()]
    if len(found) != 1:
        raise InviteError("Your UU address is not a unique attendee of this meeting.")
    return found[0]


def date_value(event, key):
    if key not in event:
        return None
    value = event.decoded(key)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise InviteError("The invitation has a time without a time zone.")
        return value.astimezone(timezone.utc)
    if isinstance(value, date):
        return value
    raise InviteError("The invitation has an unsupported date.")


def recurrence(event):
    prop = event.get("RECURRENCE-ID")
    if prop is not None and prop.params.get("RANGE"):
        raise InviteError("Responses to 'this and future occurrences' need Outlook.")
    return date_value(event, "RECURRENCE-ID")


def end_time(event):
    if "DTEND" in event:
        return date_value(event, "DTEND")
    start = date_value(event, "DTSTART")
    duration = event.decoded("DURATION", None)
    if duration is not None:
        return start + duration
    return start if isinstance(start, datetime) else start + timedelta(days=1)


def rule(event):
    value = event.get("RRULE")
    if not value:
        return None
    result = {key: sorted(str(item) for item in values) for key, values in value.items()}
    result.setdefault("INTERVAL", ["1"])
    result.setdefault("WKST", ["MO"])
    return result


def invitation(raw):
    if len(raw) > MAX_SIZE:
        raise InviteError("This message is too large for the invitation reader.")
    message = BytesParser(policy=policy.default).parsebytes(raw)
    calendars = {}

    def visit(part):
        # Don't respond to an invitation inside an attached/forwarded email.
        if part.get_content_type() == "message/rfc822":
            return
        if part.is_multipart():
            for child in part.iter_parts():
                visit(child)
        elif (part.get_content_type() == "text/calendar"
              or str(part.get_filename() or "").lower().endswith(".ics")):
            try:
                calendar = Calendar.from_ical(part.get_payload(decode=True) or b"")
            except (ValueError, TypeError) as error:
                raise InviteError("The calendar attachment could not be read.") from error
            calendars[calendar.to_ical()] = calendar

    visit(message)
    if len(calendars) != 1:
        raise InviteError("No single invitation found in this message.")
    calendar = next(iter(calendars.values()))
    if str(calendar.get("METHOD", "")).upper() != "REQUEST":
        raise InviteError("This is not a meeting invitation or update (METHOD:REQUEST).")
    events = calendar.walk("VEVENT")
    if len(events) != 1 or not events[0].get("UID"):
        raise InviteError("This invitation contains several events or has no event ID.")
    event = events[0]
    if str(event.get("STATUS", "")).upper() == "CANCELLED":
        raise InviteError("This meeting has been cancelled.")
    if date_value(event, "DTSTART") is None:
        raise InviteError("The invitation has no start time.")
    recurrence(event)
    return event


class Client:
    def __init__(self, url, account, password, status_file=None, read_only=False):
        self.url = url.rstrip("/") + "/"
        self.origin = urlsplit(self.url)
        if (self.origin.scheme != "http" or self.origin.hostname != "127.0.0.1"
                or self.origin.username or self.origin.query or self.origin.fragment):
            raise InviteError("Expected the local DavMail calendar address.")
        self.account = account
        self.status_file = status_file
        self.read_only = read_only
        self.authorization = "Basic " + base64.b64encode(f"{account}:{password}".encode()).decode()

    def path(self, href):
        target = urlsplit(urljoin(self.url, href))
        decoded = unquote(target.path)
        base = unquote(self.origin.path)
        if ((target.scheme, target.netloc) != (self.origin.scheme, self.origin.netloc)
                or target.query or target.fragment or not decoded.startswith(base)
                or any(part in (".", "..") for part in decoded.split("/"))
                or any(not char.isprintable() for char in decoded)
                or "\\" in decoded or "/" in decoded[len(base):]):
            raise InviteError("DavMail returned an unexpected calendar path.")
        return quote(decoded, safe="/@:+,=~!$&'()*-._")

    def request(self, method, href, body=None, etag=None):
        if method not in {"GET", "REPORT", "PUT"} or (self.read_only and method == "PUT"):
            raise InviteError("Writes are disabled for this check.")
        headers = {"Authorization": self.authorization}
        if method == "REPORT":
            headers.update(Depth="1", **{"Content-Type": "application/xml; charset=utf-8"})
        if method == "PUT":
            if not etag:
                raise InviteError("DavMail supplied no event version; response stopped.")
            headers.update({"If-Match": etag, "Content-Type": "text/calendar; charset=utf-8"})
        connection = http.client.HTTPConnection(self.origin.hostname, self.origin.port, timeout=30)
        try:
            connection.request(method, self.path(href), body=body, headers=headers)
            response = connection.getresponse()
            data = response.read(MAX_SIZE + 1)
            if len(data) > MAX_SIZE:
                raise InviteError("The calendar response is too large.")
            return response.status, response.getheader("ETag"), data
        finally:
            connection.close()

    def get(self, href):
        status, etag, data = self.request("GET", href)
        if status != 200:
            raise InviteError(f"Could not read the current meeting (HTTP {status}). Nothing sent.")
        if not etag:
            raise InviteError("DavMail supplied no event version; response stopped.")
        return etag, Calendar.from_ical(data)

    def locate(self, event):
        uid = str(event["UID"])
        # Local .ics filenames are based on UIDs, not remote resource names.
        # Read the existing sync mapping without modifying its database.
        href = None
        if self.status_file and self.status_file.is_file():
            try:
                database = sqlite3.connect(self.status_file.as_uri() + "?mode=ro", uri=True, timeout=1)
                try:
                    row = database.execute("SELECT href_b FROM status WHERE ident=?", (uid,)).fetchone()
                    href = row[0] if row else None
                finally:
                    database.close()
            except sqlite3.Error:
                pass  # A new/unsynced event can still be found by REPORT.
        if href:
            status, etag, data = self.request("GET", href)
            if status == 200 and etag:
                return self.path(href), etag, Calendar.from_ical(data)
            if status not in (404, 503):  # DavMail also uses 503 for missing items.
                raise InviteError(f"Could not read the current meeting (HTTP {status}). Nothing sent.")

        # DavMail may ignore the UID filter, so also filter the returned data.
        root = ET.Element(CALDAV + "calendar-query")
        props = ET.SubElement(root, DAV + "prop")
        ET.SubElement(props, DAV + "getetag")
        ET.SubElement(props, CALDAV + "calendar-data")
        filt = ET.SubElement(root, CALDAV + "filter")
        comp = ET.SubElement(ET.SubElement(filt, CALDAV + "comp-filter", name="VCALENDAR"),
                             CALDAV + "comp-filter", name="VEVENT")
        # DavMail ignores UID filters. Bound the time range as well, otherwise
        # it fetches every historical event individually from Graph.
        start = date_value(event, "DTSTART")
        if not isinstance(start, datetime):
            start = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
        ET.SubElement(comp, CALDAV + "time-range",
                      start=(start - timedelta(days=1)).strftime("%Y%m%dT%H%M%SZ"),
                      end=(start + timedelta(days=1)).strftime("%Y%m%dT%H%M%SZ"))
        prop = ET.SubElement(comp, CALDAV + "prop-filter", name="UID")
        ET.SubElement(prop, CALDAV + "text-match", collation="i;octet").text = uid
        status, _, data = self.request("REPORT", self.url, ET.tostring(root))
        if status != 207:
            raise InviteError(f"Could not find the meeting (HTTP {status}). Nothing sent.")
        matches = set()
        for response in ET.fromstring(data).findall(DAV + "response"):
            for propstat in response.findall(DAV + "propstat"):
                if " 200 " not in propstat.findtext(DAV + "status", ""):
                    continue
                content = propstat.findtext(DAV + "prop/" + CALDAV + "calendar-data")
                if content and any(str(item.get("UID")) == uid
                                   for item in Calendar.from_ical(content).walk("VEVENT")):
                    matches.add(self.path(response.findtext(DAV + "href", "")))
        if len(matches) != 1:
            raise InviteError("The invitation does not match exactly one meeting on your UU calendar. Nothing sent.")
        href = matches.pop()
        etag, calendar = self.get(href)
        return href, etag, calendar


def configured_client(read_only=False):
    config = configparser.ConfigParser(interpolation=None)
    config.read(CONFIG / "vdirsyncer/config")
    remote = config["storage uu_graph_remote"]
    pair = config["pair uu_graph"]
    if json.loads(pair["a"]) != "uu_graph_local" or json.loads(pair["b"]) != "uu_graph_remote":
        raise InviteError("The UU sync mapping has changed; invitation lookup needs updating.")
    # Use the existing password hook; credentials never enter argv or files.
    password = subprocess.run([str(CONFIG / "vdirsyncer/scripts/fetch-pw.zsh")],
                              capture_output=True, text=True, check=True, timeout=8).stdout.strip()
    if not password or "\n" in password:
        raise InviteError("The calendar password could not be loaded.")
    status_file = Path(json.loads(config["general"]["status_path"])).expanduser() / "uu_graph/calendar.items"
    return Client(json.loads(remote["url"]), json.loads(remote["username"]), password,
                  status_file, read_only)


def matching_event(request, calendar, account):
    own_attendee(request, account)
    if address(request.get("ORGANIZER")) == account.casefold():
        raise InviteError("You organize this meeting; there is no invitation to answer.")
    if any(str(event.get("UID")) != str(request["UID"]) for event in calendar.walk("VEVENT")):
        raise InviteError("The calendar resource contains unrelated events. Nothing sent.")
    matches = [event for event in calendar.walk("VEVENT")
               if str(event.get("UID")) == str(request["UID"])
               and recurrence(event) == recurrence(request)]
    if len(matches) != 1:
        raise InviteError("This event or occurrence is not uniquely present on the server. Nothing sent.")
    event = matches[0]
    own_attendee(event, account)
    if str(event.get("STATUS", "")).upper() == "CANCELLED":
        raise InviteError("This meeting has been cancelled. Nothing sent.")
    if (address(event.get("ORGANIZER")) != address(request.get("ORGANIZER"))
            or date_value(event, "DTSTART") != date_value(request, "DTSTART")
            or end_time(event) != end_time(request)
            or clean(event.get("SUMMARY", "")) != clean(request.get("SUMMARY", ""))
            or rule(event) != rule(request)
            or ("SEQUENCE" in event and int(event["SEQUENCE"]) != int(request.get("SEQUENCE", 0)))):
        raise InviteError("This invitation no longer matches the current meeting. Open the latest invitation. Nothing sent.")
    # DavMail Graph 7.1 omits SEQUENCE and regenerates DTSTAMP. Comparing those
    # unconditionally rejects valid invitations; dates/organizer/scope above
    # are compared against the current server event instead.
    return event


def response_body(calendar, event, account, choice):
    if choice not in RESPONSES:
        raise InviteError("Unknown response.")
    result = copy.deepcopy(calendar)
    selected = copy.deepcopy(event)
    own_attendee(selected, account).params["PARTSTAT"] = choice
    # Only one VEVENT: DavMail evaluates every non-NEEDS-ACTION self status
    # in a PUT. Including other exceptions could send additional responses.
    result.subcomponents = [part for part in result.subcomponents if part.name == "VTIMEZONE"]
    result.add_component(selected)
    result.pop("METHOD", None)
    return result.to_ical()


def state_directory():
    return Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state"))) / "neomutt-invites"


def reply(client, request, href, shown_etag, shown_calendar, choice, state=None):
    identity = [str(request.get(key, "")) for key in ("UID", "RECURRENCE-ID", "SEQUENCE", "DTSTAMP")]
    key = hashlib.sha256(json.dumps([client.account, *identity]).encode()).hexdigest()
    folder = state or state_directory()
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (folder / (key + ".lock")).open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        record = folder / (key + ".json")
        previous = json.loads(record.read_text()) if record.exists() else {}
        if previous.get("status") == "pending":
            raise InviteError("A previous response has an uncertain result. Check Outlook before retrying; no second response was sent.")
        if previous.get("status") == "sent" and previous.get("choice") == choice:
            return "This response was already submitted. Nothing sent again."
        etag, calendar = client.get(href)
        event = matching_event(request, calendar, client.account)
        current = str(own_attendee(event, client.account).params.get("PARTSTAT", "NEEDS-ACTION")).upper()
        if current == choice:
            return f"Already {STATUSES[choice].lower()}. Nothing sent again."
        if etag != shown_etag or calendar.to_ical() != shown_calendar.to_ical():
            raise InviteError("The meeting changed while the menu was open. Open ci again to review it. Nothing sent.")
        body = response_body(calendar, event, client.account, choice)

        def remember(status):
            with tempfile.NamedTemporaryFile(mode="w", dir=folder, delete=False) as file:
                json.dump({"status": status, "choice": choice,
                           "time": datetime.now(timezone.utc).isoformat()}, file)
                file.flush()
                os.fsync(file.fileno())
            os.replace(file.name, record)

        remember("pending")
        try:
            status, _, _ = client.request("PUT", href, body, etag)
            if status not in (200, 204):
                raise InviteError(f"DavMail returned HTTP {status}.")
        except Exception as error:
            raise InviteError("Could not confirm the response. It may have been sent. Check Outlook before retrying; no automatic retry was made.") from error
        try:
            remember("sent")
        except OSError:
            return "Response submitted, but its local receipt could not be saved. Do not send it again."
        return "Response submitted to the organizer. Your calendar updates on the next sync."


def details(event, account):
    def formatted(value):
        if isinstance(value, datetime):
            return value.astimezone(ZoneInfo("Europe/Amsterdam")).strftime("%a %d %b %Y, %H:%M %Z")
        return value.strftime("%a %d %b %Y")

    start, end = date_value(event, "DTSTART"), end_time(event)
    scope = "This occurrence" if recurrence(event) is not None else "Entire series" if event.get("RRULE") else "This meeting"
    organizer = event["ORGANIZER"]
    name = clean(organizer.params.get("CN", ""))
    status = str(own_attendee(event, account).params.get("PARTSTAT", "NEEDS-ACTION")).upper()
    lines = [clean(event.get("SUMMARY", "Meeting")), f"Organizer: {name} <{address(organizer)}>"]
    if isinstance(start, datetime):
        lines += [f"Starts: {formatted(start)}", f"Ends:   {formatted(end)}"]
    else:
        last = end - timedelta(days=1)
        lines.append("When: " + formatted(start) + (" – " + formatted(last) if last != start else "") + " (all day)")
    lines.append(f"Scope: {scope} · Your reply: {STATUSES.get(status, clean(status))}")
    if event.get("LOCATION"):
        lines.append("Where: " + clean(event["LOCATION"]))
    return "\n".join(lines)


def choose(title, header, options):
    # The dialog gets display text only; it cannot access the RSVP client.
    with tempfile.TemporaryDirectory(prefix="neomutt-invite-") as directory:
        folder = Path(directory)
        (folder / "dialog.json").write_text(json.dumps({"title": title, "header": header, "options": options}))
        args = [sys.executable, str(CONFIG / "neomutt/scripts/invite_dialog.py"), str(folder)]
        # NeoMutt pipes the message on stdin; stderr still names its real tty.
        # Opening /dev/tty instead also breaks kqueue input handling on macOS.
        tty = os.ttyname(2) if os.isatty(2) else "/dev/tty"
        with open(tty, "r+b", buffering=0) as terminal:
            if os.environ.get("TMUX"):
                pane_tty, columns, rows = subprocess.check_output(
                    ["tmux", "display-message", "-p", "#{pane_tty}\t#{client_width}\t#{client_height}"],
                    text=True).strip().split("\t")
                # An existing mail popup has its own tty. Draw there directly:
                # tmux cannot open a second popup inside the first one.
                if pane_tty == os.ttyname(terminal.fileno()):
                    args = ["tmux", "display-popup", "-E", "-B",
                            "-w", str(min(86, int(columns) - 2)), "-h", str(min(24, int(rows) - 2)),
                            "-x", "C", "-y", "C", *args]
            result = subprocess.run(args, stdin=terminal, stdout=terminal, stderr=terminal)
        if result.returncode not in (0, 1, 130):
            result.check_returncode()
        answer = folder / "answer"
        return answer.read_text() if answer.exists() else None


def notice(message):
    choose("Invitation", message, [("close", "󰅖  Close")])


def run(raw, client=None):
    request = invitation(raw)
    client = client or configured_client()
    href, etag, calendar = client.locate(request)
    event = matching_event(request, calendar, client.account)
    header = details(event, client.account)
    choice = choose("Invitation", header, [
        ("ACCEPTED", "  Accept"),
        ("TENTATIVE", "󰔛  Tentative"), ("DECLINED", "  Decline"),
    ])
    if choice not in RESPONSES:
        return
    confirmation = choose("Send response", header + "\n\nSend this response to the organizer?", [
        ("cancel", "󰅖  Cancel"), ("send", "  Send: " + RESPONSES[choice]),
    ])
    if confirmation == "send":
        notice(reply(client, request, href, etag, calendar, choice))
