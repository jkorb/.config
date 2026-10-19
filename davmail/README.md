# DavMail

DavMail connects the personal UU account to Microsoft Graph so NeoMutt and
khal can keep using IMAP, SMTP and CalDAV. Graph replaces EWS and supports
Teams meetings. Shared mailboxes and calendars are disabled.

The `davmail-graph` launchd service starts at login and restarts if it exits.
Its settings come from `private/graph.properties`, based on
[graph.properties.template](graph.properties.template). Login uses Microsoft
Office device authentication. The encrypted refresh token and logs stay in
the gitignored `private/` directory.

All listeners bind to `127.0.0.1`:

| Port | Client |
|------|--------|
| 2143 | mbsync (IMAP) |
| 2025 | msmtp (SMTP) |
| 2080 | vdirsyncer (CalDAV) |
| 2389 | fetch_contacts (LDAP) |

```sh
lctl info davmail-graph
lctl enable davmail-graph   # start or restart
mbsync uu
vdirsyncer sync uu_graph
```

Graph saves sent mail; NeoMutt leaves UU's `record` empty to avoid duplicates.
Events with attendees get a Teams link. Use `khal-personal` (also the shell's
`khal`/`ikhal` aliases and tmux calendar shortcut) to supply the organizer for
new UU events. In ikhal's attendee field, press Tab to search for contacts.
Khal uses Europe/Amsterdam; DavMail's fallback stays UTC to avoid
a timestamp conversion bug.

Migration notes and backups are kept locally under `private/`.
