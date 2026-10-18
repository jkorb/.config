# Chawan in tmux

`cha https://chawan.net` opens a browser in the current pane. The config enables
images through Sixel, which the installed tmux and WezTerm support. No Kitty
graphics setting or separate window is needed. JavaScript and cookies are off.

For an offline image check:

```sh
cha ~/.config/chawan/test.html
```

The page contains a blue image. Use `j`/`k` to scroll, `/` to search, and `q` to
quit. Test scrolling, pane resizing, and switching away and back: a successful
first image does not guarantee every redraw works in every terminal version.

## Navigation and appearance

`h`/`j`/`k`/`l` scroll the page directly. Chawan normally uses these keys to
move a cursor; arrow keys still do that here. `Ctrl-d`/`Ctrl-u` scroll half a
page. To follow links, use `f` and type a hint, then Enter, or use `[`/`]` to
select the previous/next link and Enter to open it.

For a search box or other text field, select it with `f` and its hint (or
`[`/`]`), then press Enter to activate it. Type in the editor at the bottom of
the screen. Enter accepts the text and may submit the form; Ctrl-G cancels
editing. Merely moving onto a field does not put you into an insert mode.

For a quick web search, Ctrl-L opens the address bar: enter `ddg:search terms`
to search DuckDuckGo Lite without navigating a site's search form.

The bottom status bar uses bold text on the terminal's normal background,
inheriting the shared One Dark colors. Cursor coordinates are hidden; page
titles, messages and hovered link destinations remain. Chawan's status settings
offer text attributes, but no separate color palette or custom layout.
These settings apply when Chawan next opens. Mail views also load the generated
[One Dark reader stylesheet](mail.css), with cyan links and subdued quotes.
It overrides viewing colors without changing stored or outgoing messages.
Ordinary web browsing keeps website colors.

## Neovim live preview

Keep `MarkdownPreview` in Firefox for now, including when composing HTML mail.
Chawan 0.4.4 can display the plugin's initial page with JavaScript enabled and
the HTML content type forced, but the live-update test kept displaying old
text after unsaved edits. The plugin's Socket.IO stream did deliver those
edits; Chawan did not show them. One test also hit an internal Chawan assertion.

No browser selector is installed yet. Recheck this with a newer Chawan before
adding one. The intended workflow is a remembered Firefox/Chawan choice for
the existing live preview, with Chawan beside the editor in a tmux pane.

## Email

NeoMutt defaults to text viewing, with w3m rendering HTML. Both readers fill
the current pane. `H` opens Chawan; `gh` toggles HTML mode, where Enter
and `l` open Chawan and `H` opens text. In the text pager, `H` opens Chawan in
either mode.

Inside Chawan's mail view, `A` opens NeoMutt's attachment list, `H` switches to
the text view, and `q` returns to the index or message that opened it. HTML
attachments opened from the attachment list also use Chawan; `A` or `q` returns
to that list.
The `cr`, `ca`, `cc`, `cf`, `sa`, `si`, `sj`, and `ss` sequences return control
to the corresponding NeoMutt binding: replies, composition, forwarding, and
account-specific filing work directly from the HTML reader.

Clicking a mail notification opens NeoMutt in a temporary tmux window and starts
this HTML view automatically when the notified message has an HTML body. Press
`q` once to close notification mail and return to your previous window. Plain-text messages,
or notifications whose source file is no longer available, use the normal pager.
The centered popup was replaced because tmux discards Sixel output in popups;
the identical image renders in a normal pane. See the
[upstream popup report](https://github.com/tmux/tmux/issues/4867).

This mail view allows remote image requests, so opening it can notify the
sender that you read the message. This permission is scoped to that Chawan
process, and browsing history is disabled there. Ordinary `cha` sessions keep
the default restriction on HTTP requests from local files.

The [mail viewer](../neomutt/scripts/neomutt-view) reads the complete MIME
message and resolves embedded `cid:` images to private temporary files. Those
viewing copies are removed when Chawan exits. An attached HTML document is not
mistaken for the message body.
Extracted image files retain a MIME-appropriate extension so Chawan can decode them.

For HTML composition, `ch` previews the generated reply without adding parts
to the outgoing message. Conversion itself happens automatically after editing
Markdown. See [Writing HTML mail](../doc/services.md#writing-html-mail).
Newly composed math uses Unicode output; existing MathML source annotations are
hidden in the reader so they do not appear beside the rendered symbols.

The [mailcap entries](../neomutt/core/mailcap) take effect on the next HTML view.
Restart NeoMutt, or reload with Space then `r`, to use the new mode bindings.

References: [Chawan image support](https://chawan.net/doc/cha/image.html),
[configuration](https://chawan.net/doc/cha/config.html), and
[NeoMutt MIME viewers](https://neomutt.org/guide/mimesupport.html#mailcap).
