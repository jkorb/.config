# DavMail

DavMail connects UU mail, calendars and contacts to Microsoft Graph.
Homebrew manages the package; the `davmail-graph` launchd job starts it at login.

NeoMutt opens UU folders over live IMAP. Reading and filing these folders
requires an internet connection. Large folders can take a long time to open
while NeoMutt downloads their headers. UU drafts are saved on this Mac in
`~/.mail/uu/LocalDrafts`.

Every five minutes, `mail-sync` downloads new UU mail for mu search and syncs
Gmail both ways. It backs up both accounts before and after each run.
Use `sa`, `si` and `sj` to file UU messages in the live folders. The downloaded
copy is for reading. `ga` opens the downloaded Archive read-only; `gA` opens
the live Archive for moving or deleting messages.

UU downloads are retained even after server filing or deletion; their flags
reflect the time they were downloaded. `/` searches the local copies, with
duplicate results hidden. Notifications follow newly downloaded mail and open
the live Inbox when clicked.
Gmail finishes its sync and notifications before the UU download starts.

This is temporary while the Graph [UID changes](https://github.com/mguessan/davmail/issues/570)
and [message uploads](https://github.com/mguessan/davmail/issues/572) remain unresolved.
Returning to two-way sync requires reconciling retained copies with the server first.

```sh
lctl info
mail-sync
vdirsyncer sync uu_graph
```

Calendar sync, Teams links and contacts use DavMail. `ci` reviews a UU invitation
and offers Accept, Tentative or Decline, followed by a Send confirmation.
Calendar attachments open as readable previews. Responses update through DavMail;
khal picks them up on the next calendar sync.

Settings are in the gitignored `graph.properties`, based on
[graph.properties.template](graph.properties.template). The encrypted token and
log are in `~/.local/state/davmail/`. Local ports:
IMAP 2143, SMTP 2025, CalDAV 2080 and LDAP 2389.

Backups in `~/Backups/Mail/uu/` and `~/Backups/Mail/gmail/` retain deleted mail
and older versions. Recovery records are in `~/Backups/Mail/recovery/`.
Include `~/Backups/Mail/` in an external backup.
Sync errors are recorded in `~/.cache/mail-sync/last-error.log`.
