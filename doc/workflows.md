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
Other text uses bat; other file types use the macOS default application.

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
annotation keys, and included comments/notes belong to `md-read`.

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
closes the preview. Glow still shows the LaTeX source. The math-enabled Glow
fork uses image placement that the current WezTerm release does not support.

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
