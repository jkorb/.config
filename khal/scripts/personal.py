"""UU meeting organizers and contact completion for khal."""

import subprocess

from contacts import pick_contacts

from icalendar import vCalAddress
from khal.khalendar import CalendarCollection
from khal.khalendar.event import Event
from khal.ui.editor import EventEditor, ExtendedEdit


def update_attendees(event, addresses):
    # khal 0.13 keeps whitespace-only entries and treats a single existing
    # attendee as a string. Preserve invitation parameters while editing.
    vevent = event._vevents[event.ref]
    existing = vevent.get("ATTENDEE", [])
    if not isinstance(existing, list):
        existing = [existing]
    known = {str(item).split(":", 1)[-1].casefold(): item for item in existing}
    selected = []
    for address in dict.fromkeys(a.strip().casefold() for a in addresses if a.strip()):
        if address in known:
            selected.append(known[address])
        else:
            item = vCalAddress("MAILTO:" + address)
            item.params.update(ROLE="REQ-PARTICIPANT", PARTSTAT="NEEDS-ACTION",
                               CUTYPE="INDIVIDUAL", RSVP="TRUE")
            selected.append(item)
    if selected:
        vevent["ATTENDEE"] = selected
    else:
        vevent.pop("ATTENDEE", None)


def attendee_span(text, cursor):
    left = text.rfind(",", 0, cursor) + 1
    right = text.find(",", cursor)
    return left, len(text) if right == -1 else right


class AttendeesEdit(ExtendedEdit):
    def __init__(self, editor, **kwargs):
        super().__init__(**kwargs)
        self.editor = editor

    def keypress(self, size, key):
        left, right = attendee_span(self.edit_text, self.edit_pos)
        query = self.edit_text[left:right].strip()
        if key != "tab":
            return super().keypress(size, key)

        window = self.editor.pane.window
        excluded = [part.strip() for part in
                    (self.edit_text[:left] + self.edit_text[right:]).split(",")]
        screen = window.loop.screen
        screen.stop()
        try:
            addresses = pick_contacts(query, excluded)
        except (OSError, subprocess.SubprocessError, ValueError, TypeError) as error:
            window.alert(f"Contact search failed ({type(error).__name__}); attendees unchanged.")
        else:
            if addresses:
                self.insert_address(left, right, ", ".join(addresses))
        finally:
            screen.start()
            screen.clear()
        return None

    def insert_address(self, left, right, address):
        prefix = self.edit_text[:left] + (" " if left else "")
        suffix = self.edit_text[right:]
        if not suffix:
            suffix = ", "
        self.set_edit_text(prefix + address + suffix)
        self.set_edit_pos(len(prefix + address) + (2 if suffix == ", " else 0))


def install():
    Event.update_attendees = update_attendees
    create = CalendarCollection.create_event_from_dict
    insert = CalendarCollection.insert

    def create_event(self, *args, **kwargs):
        event = create(self, *args, **kwargs)
        event._personal_new = True
        return event

    def insert_event(self, event, collection=None):
        calendar = collection or event.calendar
        # Imported invitations never pass through create_event_from_dict.
        if getattr(event, "_personal_new", False) and calendar == "uu":
            address = self._calendars[calendar]["addresses"][0]
            for vevent in event._vevents.values():
                if "ORGANIZER" not in vevent:
                    vevent.add("organizer", vCalAddress("mailto:" + address))
        return insert(self, event, collection)

    CalendarCollection.create_event_from_dict = create_event
    CalendarCollection.insert = insert_event

    initialize_editor = EventEditor.__init__

    def initialize(self, *args, **kwargs):
        initialize_editor(self, *args, **kwargs)
        field = self.attendees.original_widget
        self.attendees.original_widget = AttendeesEdit(
            self, caption=("caption", field.caption), edit_text=field.edit_text, multiline=True,
        )

    EventEditor.__init__ = initialize
