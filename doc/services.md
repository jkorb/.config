# Mail and background jobs

[Guide](README.md) · [Keys](keybindings.md#pdfs-mail-and-feeds) · [Audits](audits.md)

## Mail and calendars

NeoMutt reads local Maildirs. `mbsync` downloads mail, mu indexes it, and
`msmtp` sends outgoing messages. Institutional accounts use DavMail as a local
gateway. Account-specific NeoMutt files select the sender and msmtp account;
the main config selects a default account and changes it through folder hooks.

```text
Mail service → mbsync → ~/.mail → mu index → NeoMutt search
                                  └──────→ mail notifications
NeoMutt → msmtp → outgoing mail service

Calendar service → vdirsyncer → local calendar files → khal
                                                       └→ upcoming alerts
```

DavMail sits between the institutional services and their sync/send clients.
Passwords are fetched through pass by command hooks. Its live
`davmail.properties` is ignored; the repo contains a template. These docs omit
account addresses and password contents.

Sources: [isyncrc](../isyncrc), [msmtp](../msmtp/config),
[NeoMutt](../neomutt/muttrc), [DavMail template](../davmail/davmail.properties.template),
[vdirsyncer](../vdirsyncer/config), [khal](../khal/config).

### Mail index in narrow panes

The index keeps the status and sender icons, an 18-column sender field, and a
three-space gap before the subject. The subject takes the remaining width.
The attachment marker, sender label, and date
stay on the right using NeoMutt's
[soft-fill format](https://neomutt.org/guide/reference#index-format), so a long
subject does not push them off-screen. Empty attachment and label fields take
no space. Internal `@uu.nl` senders show ``; student senders retain `studi`.
An extra two spaces separate these markers from the date.
Four spaces after the date keep it away from the pane's right edge.

The date field shows `HH:MM` for today, `MM/DD` for earlier mail in the current
calendar year, and `MM/DD/YY` for previous years. The full timestamp is still
available in the message headers.

The avatar becomes `` for flagged mail, `` for mail from you, or `` for known
mailing lists, in that order of priority. Press `!` to toggle the star. The
separate status column still shows tagged, deleted, unread, or replied, in
that order of priority; ordinary read mail leaves it blank.

The existing status bar sits above the list and doubles as a column header:
bold cyan `From:`, `Subject:`, and `Date:` labels. Mailbox names and counts are
omitted to keep this row clear. `From:` starts above the sender icon, and the
date heading shares the rows' right margin. This uses no extra row.

This layout adjusts when the pane is resized. Long subjects are clipped in
narrow panes and get more room on wide screens; the full subject remains in
the message headers. The layout was checked at 60, 80, and 120 columns. Reload
with `Space r`, or restart NeoMutt. The format and icon hooks live in
[core/settings](../neomutt/core/settings), separately from the generated theme.

## launchd jobs

| Job | Schedule | Script behavior |
| --- | --- | --- |
| `davmail` | Run at load, keep alive | Start Homebrew DavMail with the private properties file |
| `mail-sync` | Run at load and at minutes 00, 05, …, 55 | Check connectivity and DavMail, run `mbsync -a`, index mu, then run mail notifications |
| `vdirsyncer-sync` | Run at load and at minutes 00, 05, …, 55 | Discover/sync when online with DavMail running; check upcoming local events either way |

The connectivity probe opens a TCP connection to `1.1.1.1:53`. It is a gate for
these scripts, not a check of the mail or calendar server. The mail script skips
all accounts when DavMail is absent, including accounts that do not use it.

[lctl](../launchd/scripts/lctl) accepts short service names:

```sh
lctl info
lctl info mail-sync
lctl enable mail-sync
lctl disable mail-sync
```

`info` reads launchd state. `enable` copies the source plist into
`~/Library/LaunchAgents`, reloads it, and enables it. `disable` unloads the job
and removes that installed copy. After editing a source plist, run `enable`
again to install the change. Editing a script takes effect on its next run.
The old `launchd-service` command is a compatibility wrapper around `lctl`.

The [plists](../launchd/services) contain absolute paths for this user and an
explicit PATH/XDG environment. Porting them to another machine requires those
paths to be checked. Linux service files in [systemd](../systemd) are separate.

## Notifications and troubleshooting

[mail-notify](../launchd/scripts/mail-notify) uses mu's JSON output and a cached
last-run time. It checks today's mail on the first run and groups notifications
by message ID. Its query is limited to the `uu/Inbox` Maildir, so the other
accounts do not receive these alerts. The sync script uses
`$XDG_CACHE_DIR/mu` as the mu home.

[vdirsyncer-sync](../launchd/scripts/vdirsyncer-sync) asks khal for events in the
next 15 minutes and stores a daily notification cache under
`$XDG_CACHE_DIR/vdirsyncer`. Notifications include a start time and event title.
Both notification paths use terminal-notifier and activate the Tmux app when
clicked.

Start diagnosis with `lctl info`. The sync scripts suppress command output
unless passed `--debug`. A debug invocation still performs sync and may display
notifications; it is not a dry run. The scripts currently discard several child
exit codes, so launchd reporting a successful exit does not establish that sync
worked. [Audit A2](audits.md#a2-sync-failures-can-look-successful) records this.

## Writing HTML mail

NeoMutt starts in ordinary compose mode. From its index or pager, `gh` loads the
HTML settings. The editor then starts Neovim with the mail filetype and
`MarkdownPreview`. After editing, `ch` runs Pandoc to create HTML and plain text
alternatives using [the mail template](../neomutt/shared/email.html).

The conversion script writes NeoMutt commands under
`$XDG_CACHE_DIR/neomutt-html/commands` and attachments in a temporary subdirectory.
It also handles local Markdown images as related attachments. In HTML mode,
`cc` removes the first Markdown body attachment before sending; `cC` removes it
without sending. Check the attachment structure in the compose screen before
sending. `gh` returns to ordinary mode from the index or pager.

Sources: [html_on](../neomutt/dynamic/html_on), [html_off](../neomutt/dynamic/html_off),
[convert_email](../neomutt/scripts/convert_email). The fixed command-file path
and repeated conversion behavior are candidates for a focused mail audit.
