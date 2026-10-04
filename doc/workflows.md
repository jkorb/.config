# Daily workflows

[Guide](README.md) · [Keybindings](keybindings.md) · [Mail and calendar jobs](services.md)

## Jumping to directories

Ctrl-G opens the same fuzzy directory picker in zsh and nnn, with shared history,
colors, and tree preview. Search covers the home directory, follows symlinks, and
uses the exclusions in `zsh/plugins/fzf/fdignore`. Enter jumps to the selected
directory; Escape cancels. In nnn it changes the current context; `-` goes back.

nnn's native binding is Alt-G (or `;g`). tmux and WezTerm translate Ctrl-G to that
binding when nnn is active; other programs keep their normal Ctrl-G behavior.
This avoids a custom nnn build. Outside tmux/WezTerm, use `;g`.
Reload tmux with prefix then `r`, and start a new shell to load the updated widget
and nnn plugin configuration. WezTerm reloads its config automatically.

## Reading and editing

In nnn, `l`, Right, or Enter reads a file; `e` edits it in Neovim.
Markdown uses `md-read` (Glow with a custom One Dark palette, paged through less).
The reading column is centered, at most 80 columns wide, with no trailing tildes.
Other text uses `bat-read`: bat highlighting in a centered column of at most
100 characters, including line numbers, with a filename header and soft wrapping.
It has no trailing tildes. Other file types use the macOS default application.

Press `e` inside the reader to edit the source in Neovim. Save and quit to return;
the reader renders it again and restores your place as closely as the changed
layout allows. Editing can make existing annotation line references stale.

In the Markdown reader, press `o` to show colored letter hints on local file
links in the current screen. The rendered document stays visible. Type a hint
to open its file; Escape cancels. Hints sit just before a link where there is
space, otherwise over its opening letters. Repeated targets share one hint.
Busy screens use two-letter hints; Backspace removes a typed letter.

Press `O` (Shift-o) for the full list of links from the document and its notes,
with fzf search; Enter opens the selection and Escape cancels. Both modes use
the same reader as nnn. Quit a linked reader to return to your place in the parent.
Links resolve relative to the document, including its companion notes in the
same directory. Reference-style links, URL-encoded spaces, and local `file:` URLs
work. Web links and links within the same document are omitted;
`other.md#heading` opens the other file at its beginning. PDFs and other non-text
files use their usual macOS application.

Wiki links work in both modes: `[[paper.md]]`, `[[ paper ]]`, and
`[[paper|Display label]]`. An extensionless target tries the exact path first,
then a sibling `.md` file if one exists. Paths are relative to the document;
there is no vault-wide filename search. `[[paper#Heading]]` opens the file at
its beginning, like an ordinary link with a fragment. Links inside code remain
literal. The [wiki-link filter](../glow/wikilinks.lua) normalizes these links
during the existing Pandoc pass without modifying the source.

Hints read Glow's existing terminal hyperlink targets from the visible lines
supplied by less; they do not parse or render the Markdown again. Their color
comes from the generated Glow theme. Resizing cancels hint mode; press `r` to
recenter before reopening it. The helper is [md-hints](../glow/scripts/md-hints).
Bare Escape is left to less because arrow keys also begin with Escape.

In the Markdown reader, `a` opens the original in Plannotator TUI for comments
attached to selected passages. Use `i` to position the cursor, then `v` and movement
keys to select text, and `c` to comment; mouse selection works too. Comments save
automatically. Press `q` to return to reading at your previous position.
Saved comments also render after the document, with source line references and
quoted text, whenever you open it in `md-read`.

Plannotator stores annotations under `$XDG_DATA_HOME/plannotator` (normally
`~/.local/share/plannotator`; an existing `~/.plannotator` takes precedence).
It leaves the Markdown source untouched. Its `d` action records a deletion
suggestion; it does not delete source text. Moving a file changes its annotation
identity because storage is keyed by its path.

For general notes, `s` opens the companion notes file in Neovim:
`paper.md` has `paper.notes.md`. Save and quit to return to the reader;
the notes are rendered after the document under **Reading notes**.
No notes file is created until you save one. These general notes are independent
of Plannotator's passage comments.

Use `/` to search, `n`/`N` for matches, `g`/`G` for the beginning/end,
`r` to reload after external edits or recenter after resizing, and `q` to return to nnn.
To mark your place before jumping to the notes, press `mb`; return with `'b`.
Run `md-read FILE.md` directly for the same reading and annotation workflow.
Plain `glow FILE.md` uses the theme and its own pager settings; the centering,
editing/link/annotation keys, math conversion, and included comments/notes belong
to `md-read`.

Run `bat-read FILE` for the source reader outside nnn. Its `e` key edits the
original in Neovim; save and quit to resume reading. `r` reloads and recenters,
`/` searches, and `q` exits. Plain `bat` keeps its usual command-line behavior.
Start a new shell to put the new `bat-read` command on PATH; nnn can use it immediately.

The bat config maps `.latex` to LaTeX and `.tmTheme` to XML. This gives Pandoc's
LaTeX templates basic highlighting, though their `$if(...)$` directives are not
a separate syntax. The reader checks `.theme` files for valid JSON before
selecting JSON highlighting, since other programs use that extension too.
For an unrecognized filename, choose explicitly: `bat-read -l JSON FILE`.
See [bat's syntax mapping documentation](https://github.com/sharkdp/bat#syntax-highlighting)
and the [reader script](../bat/scripts/bat-read).

### Logic and proofs in the reader

`md-read` uses Pandoc to turn `$…$` and `$$…$$` math into Unicode before Glow
renders the document. This runs locally in WezTerm and tmux, without image
rendering or network requests. The Markdown source is never rewritten by this
step. Code spans and fenced code examples remain literal.

Ordinary formulas use Pandoc's TeX math conversion: Greek letters, quantifiers,
connectives, relations, arrows, and common scripts. Display math gets a fixed
spacing block. The local filter adds `proof.sty` rules written as
`\infer[label]{conclusion}{premise & premise}`, including nested rules and
axioms with empty premises. Try [the logic example](examples/logic.md).

Display math also supports `array` with `l`, `c`, and `r` columns, vertical
rules (`|`), and `\hline`; `aligned`, `align`, `align*`, and `split` align equation
pairs; `gathered`, `gather`, and `gather*` center separate lines. Matrix forms
include `matrix`, `pmatrix`, `bmatrix`, `Bmatrix`, `vmatrix`, and `Vmatrix`;
`cases` adds a left brace. Use `&` between columns and `\\` between rows, inside
`$$…$$`. Arrays may be enclosed by `\left(…\right)` or matching brackets/braces.
Automatic equation numbering is omitted.

Unknown commands, unsupported proof variants, and grids or trees wider than the reading
column show their complete TeX source. This is a reading aid, not a TeX engine:
it does not load packages or expand your own macros. `\infer*`, `\infer=`, and
proofs mixed with surrounding math in one display are not supported. Fractions
use Pandoc's linear representation; there is no general two-dimensional math
renderer. Nested grids, custom column types, row-height adjustments, and grids
mixed with surrounding math in one display remain TeX. Proof labels and grid
cells with wide characters also fall back to TeX.

Math blocks carry no syntax-language label: Pandoc's lookup for the unrecognised
language `text` added about 250 ms per render. Plain-text code fences are treated
the same way, while actual programming-language labels are kept. Notes and their
heading share a render pass. There is no persistent render cache; edits, comments,
and theme changes are read again whenever the view refreshes.

Pandoc 3.8 or newer is required. The filter and checks are in
[glow/terminal-math.lua](../glow/terminal-math.lua) and
[glow/tests/test_reader.py](../glow/tests/test_reader.py).

Install the annotation reader with `brew install plannotator/tap/plannotator-tui`
(Homebrew may first require `brew trust --formula plannotator/tap/plannotator-tui`).

After changing the nnn configuration, start a new shell or run
`source ~/.config/zsh/plugins/nnn/conf.zsh`, then restart nnn.

## Shell and tmux sessions

Run `n` to open nnn and return the shell to its last directory when you leave.
`nnn` by itself opens the file manager without the shell wrapper. Run `home`
to return to the tmuxp session home, or to your home directory outside a session.

`ta` loads a tmuxp session for the current directory; `ta PATH` uses the given
directory. The script creates a YAML layout if needed under
`tmux/sessions/$HOST`. These layouts are local and ignored by Git. `:w` saves
the current layout, `:q` exits the shell, and `:qa` asks to kill the tmux session
when running inside tmux. The save helper has a guard that needs review; see
[audit A5](audits.md#a5-session-save-guard-needs-correction).

The shell uses vi editing, `AUTO_CD`, and a directory stack. `cp` and `mv` are
interactive aliases; `rm` is aliased to `trash` in an interactive shell. Scripts
can call different commands and should not assume those aliases apply.

Sources: [autoloads](../zsh/autoloads), [ta](../tmux/scripts/ta),
[shell settings](../zsh/core/core.zsh).

## Prose and Markdown in Neovim

Long paragraphs wrap on screen without inserting line breaks. Press `Space u W`
for an 82-column centered window. Press it again to return to the normal layout.
The terminal font stays the same.

Spell checking covers English, German, and Dutch in prose and TeX buffers.
`zg` asks which language should receive the word. The helper then schedules a
Git commit of the spell files in this config repo, so adding a word can create
a commit without leaving the editor.

To translate a passage, select it and press `Space t r`. The command sends the
selection and [Dutch translation prompt](../nvim/prompts/openai_translate_dutch.txt)
to the configured OpenAI endpoint and replaces the selection. It refuses to
apply a response if the buffer changed while waiting. Block selections are
unsupported. This command is an explicit network operation, separate from
ordinary editing and from local reading annotations.

The local LazyVim Markdown extra supplies Markdown tooling. The repo also sets
`MarkdownPreview` options for Markdown and mail, including rendering single
line breaks. It disables in-buffer render-markdown and headlines plugins.

For Markdown with equations, run `:MarkdownPreview` in Neovim. The installed
preview plugin renders math with KaTeX in the browser; `:MarkdownPreviewStop`
closes the preview. The terminal reader handles the subset described above;
plain Glow still shows the LaTeX source. KaTeX has its own command limits and
does not load `proof.sty`; use the TeX/PDF workflow for full proof typesetting.

Sources: [editor view](../nvim/lua/plugins/editor.lua),
[prose settings](../nvim/lua/config/autocmds.lua),
[translation](../nvim/lua/config/openai_translate.lua),
[preview options](../nvim/lua/config/options.lua).

## TeX and PDFs

In a TeX buffer, `Space m c` requests a Texlab build through latexmk.
`Space m v` forwards the current source position to Zathura. Builds are not
configured to run on every save, and a build does not automatically trigger
forward search.

Ctrl-click in Zathura requests inverse SyncTeX. The return scripts look for a
live Neovim server and use its recorded process ID to find a tmux pane. Ctrl-T
in Zathura returns to the relevant editor without selecting an exact source
position. The scripts can open a new editor when inverse search has no matching
instance. They also activate the Tmux app.

The list-item shortcut is Ctrl-T in insert mode or `Space i` in normal mode.
Custom snippets include `thm`, `lem`, `prop`, `cor`, `def`, `ex`, and `prf`;
variants ending in `T`, `L`, or `TL` add a title, label, or both where configured.
Direct triggers such as `\begin{itemize}` also insert environment bodies.

For a PDF navigation problem, inspect the socket map at
`~/.local/state/nvim/servers`, the SyncTeX output from the build, and the selected
Zathura binary/app. The shell binary and macOS app need compatible SyncTeX and
PDF plugin support; the repo does not build the Zathura app itself.

Sources: [Texlab](../nvim/lua/plugins/lsp.lua), [snippets](../nvim/lua/plugins/latex.lua),
[forward](../zathura/scripts/zathura-forward), [inverse](../zathura/scripts/zathura-inverse),
[return](../zathura/scripts/zathura-return).
