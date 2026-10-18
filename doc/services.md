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
no space. Internal `@uu.nl` senders show ``; student senders show `󰸐`.
Both provenance markers have trailing padding; terminal spacing moves in whole cells.
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

### Reading messages

Readers fill the current pane. In the default text mode, `l` or
Enter opens NeoMutt's pager, with w3m rendering HTML as text and no mini-index
above the message. `H` opens Chawan. Toggle HTML mode with `gh`: then `l` and
Enter open Chawan, and `H` opens text instead.

Inside Chawan's mail view, `A` opens NeoMutt's attachment list directly, `H`
switches to text, and `q` returns to where the view was opened. The
[viewer helper](../neomutt/scripts/neomutt-view) extracts embedded images into
a private temporary directory, removing those viewing copies when Chawan exits.
Remote images remain enabled in this view. Text viewing still provides all the
usual NeoMutt actions, including replies and `A` for attachments.
Chawan also passes `cr`, `ca`, `cc`, `cf`, `sa`, `si`, `sj`, and `ss` to the
existing NeoMutt compose and account bindings. Notification mail has its own
one-key exit, described below.

The HTML reader uses a generated One Dark stylesheet: muted foreground, cyan
links, subdued quotes, and a dark background. This changes the local view only;
stored messages and outgoing HTML retain their own styles.

### Saving attachments

Open the attachment list with `A`, then press `s` to save the current attachment.
For several attachments, tag each with `Space Space`, then press `s`. The
[save helper](../neomutt/scripts/neomutt-save) exports them into `~/Downloads`
and opens nnn with those new files selected. Existing names get numbered copies;
existing files are never overwritten by the export or the managed move command.

In this picker:

- `Space` toggles a file's selection.
- Navigate to a destination and press `v` to move the selected attachments there.
  Collisions get numbered names. Reselect the moved files with `Space`.
- `;r` renames the hovered attachment, numbering collisions. Reselect it afterward.
  Native `Ctrl-R` still uses nnn's own overwrite prompt; use `;r` for numbered names.
- `q` finishes. Selected attachments keep their current names and locations;
  unselected copies created by this save are sent to macOS Trash.
- `Ctrl-G` cancels cleanup and leaves all exported files where they are.

nnn clears selection after moves, so **reselect before quitting**. The helper
tracks the created files by their filesystem identity, including across renames,
and never cleans up unrelated files merely because they are unselected. If the
picker fails or a file cannot be identified safely, it is retained. Only regular
attachment files created by the current run are eligible for automatic cleanup.
The managed move currently stays on the same volume; moving to another volume
fails without removing the source. Normal nnn commands remain available, so their
own prompts still apply to manual operations on other files.

Private export/recovery metadata lives under `$XDG_CACHE_DIR/neomutt-save/save-*`.
If Trash fails, the diagnostic names the retained file in that run's `discarded`
directory. Compose-mode `ca` continues to use the existing attachment picker.

### Starting the mail editor

The public [mail.nvim](https://github.com/jkorb/mail.nvim) plugin starts replies
at the first body line when an `In-Reply-To` header is present. Fresh mail starts
at `To:`. This runs once per buffer and also handles a plugin loaded after the
buffer was opened; returning to a draft preserves the current cursor position.

[mail.lua](../nvim/lua/plugins/mail.lua) installs the plugin through lazy.nvim
and registers [tree-sitter-mail](https://github.com/jkorb/tree-sitter-mail) from
GitHub. Neither needs a local development checkout. On a fresh setup, run
`:TSInstall mail`; after a grammar change, `:TSInstall! mail` rebuilds it.
The plugin supplies mail highlighting and spell-check captures.

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
Both notification paths use terminal-notifier. Calendar alerts activate the Tmux
app. New mail notifications run
[neomutt-notification](../neomutt/scripts/neomutt-notification): activate Tmux,
then open NeoMutt in a temporary tmux window in the active client's session.
The helper uses the notified Maildir and limits the index to the exact Message-ID
before displaying the message. If the notified file has an HTML body, it then
opens Chawan automatically, just like pressing `H`, including loading remote
images. Press `q` once in either reader to close notification mail and return
to your previous tmux window. `cr` replies, `ca` replies to all, and `sa` archives
through the current account's normal binding. Plain-text messages use the normal
pager. Use
`?` with `~A` from its index to show the rest of the mailbox.

The former centered popup could not display Sixel images: tmux's popup renderer
discards them. A local test with identical image output confirmed that a normal
pane renders the image while a popup drops it. Notification windows close when
NeoMutt exits; existing windows and panes are not resized or replaced.

If the message path has disappeared, the helper opens `uu/Inbox` and searches
there by ID. A message moved elsewhere may therefore show an empty index. Alerts
already posted with this helper also pick up script changes when clicked;
older alerts that only activated the Tmux app retain that old action. No
launchd reload is needed.

Start diagnosis with `lctl info`. The sync scripts suppress command output
unless passed `--debug`. A debug invocation still performs sync and may display
notifications; it is not a dry run. The scripts currently discard several child
exit codes, so launchd reporting a successful exit does not establish that sync
worked. [Audit A2](audits.md#a2-sync-failures-can-look-successful) records this.

## Writing HTML mail

From the index or text pager, `gh` enables HTML reading and composition. Use
`cc` for a new message, `cr` to reply, or `ca` to reply to all. Write Markdown
in Neovim, then save and quit. The editor wrapper automatically generates both
HTML and plain text with Pandoc; ordinary line breaks are preserved.
Simple LaTeX math uses Pandoc's Unicode output, avoiding the MathML source
annotation that Chawan displayed beside the symbols. Expressions that Pandoc
cannot represent this way remain as TeX.

The sender's account selects its existing `*_html_signature.html` footer.
It replaces the native plain signature and appears in the Markdown source between
`<!-- neomutt-signature -->` markers, so live preview can show the formatted footer.
Keep the marked block intact, or remove it completely to omit the signature.
The outgoing HTML preserves that footer; its text alternative gets a readable
conversion of the same content. Re-editing does not duplicate the signature.

In the compose screen:

- `ce` reopens the Markdown source and regenerates both versions when you finish.
- `ch` previews the generated HTML in Chawan, including embedded images. It is
  optional, repeatable, and does not add attachments. `q` returns to compose.
- `ca` attaches documents as usual.
- `cc` assembles the text/HTML alternatives and sends through the existing mail
  transport. Attached documents stay separate; inline images become related
  parts. Retrying a failed send does not add duplicate alternatives.

For replies, the original HTML is kept separately. The editor shows its readable
text between `<!-- neomutt-quote -->` and `<!-- /neomutt-quote -->`. Leave that
block unchanged, or remove the entire block to omit the quote. Editing within
it stops conversion and sending, rather than silently replacing the original
HTML. New text before or after the block is converted from Markdown; the quoted
body markup, inline styles, style blocks, and embedded images are retained.
Rendering may still differ between mail clients.

The existing live `MarkdownPreview` remains available in Firefox while editing.
It shows the Markdown representation; `ch` shows the generated HTML with the
original quote. Conversion errors block the normal `cc` send action. Fix the
source with `ce`, then send again. The old manual conversion and `cC` body-removal
steps are no longer used.

Each composition has a private `$XDG_CACHE_DIR/neomutt-html/draft-*` directory
containing `source.md`, the last edited `recovery.eml`, generated alternatives,
and quote resources. These files
remain available for recovery. Use this workflow for messages started through
the HTML compose/reply bindings; restoring Markdown from a postponed message
after restarting NeoMutt is not integrated yet. `gh` returns to ordinary text
mode from the index or pager.

Sources: [html_on](../neomutt/dynamic/html_on), [html_off](../neomutt/dynamic/html_off),
[neomutt-html](../neomutt/scripts/neomutt-html).
