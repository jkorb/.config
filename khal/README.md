# Khal

`khal` and `ikhal` in new shells use [khal-personal](scripts/khal-personal).
The tmux calendar shortcut uses the same launcher. It runs Homebrew's khal
with local additions, without changing the installed package.

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

Select an event in the event list and press `J` (Shift-J) to open its Teams
meeting. Clicking a Teams reminder does the same. Teams opens the pre-join
screen; you choose when to join. If the app cannot open, the meeting opens
in your browser. Links in the URL, location, description, Outlook fields,
and Microsoft Safe Links are supported.

Sync uses `vdirsyncer sync uu_graph`. Reopen the calendar after changing its
configuration; start a new shell to pick up the aliases.
