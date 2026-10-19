# Khal

`khal` and `ikhal` in new shells use [khal-personal](scripts/khal-personal).
The tmux calendar shortcut uses the same launcher. It runs Homebrew's khal
with two local additions, without changing the installed package.

Press Tab in the attendee field to open fzf, even when empty. It uses your
usual keys and One Dark colors: Tab/Ctrl-N move down, Shift-Tab/Ctrl-P move
up, Ctrl-U clears the search, and Escape cancels. Enter adds the highlighted
contact; Alt-Space marks several contacts to add together.

The initial list puts recent personal contacts first. Typing fuzzy-searches
names and addresses, with directory results from `fetch_contacts` added as
they arrive. A trailing comma leaves room for another attendee. Use Down
or Shift-Tab to leave the attendee field.

New UU events get your address as organizer. DavMail needs this to create
meetings with attendees and add a Teams link. Imported invitations retain
their organizer. Private and deadline calendars stay local.

Sync uses `vdirsyncer sync uu_graph`. Reopen the calendar after changing its
configuration; start a new shell to pick up the aliases.
