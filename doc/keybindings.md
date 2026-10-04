# Keybindings

[Guide](README.md) · [Workflows](workflows.md)

`Prefix` means press Ctrl-A, release, then press the next key. Neovim's leader
is Space. Keys separated by spaces form a sequence; a plus sign means hold the
modifier. Uppercase letters are distinct from lowercase letters.

This page covers custom bindings and the few application defaults needed for
the documented workflows. Plugin defaults can change. For a Neovim conflict,
use `:verbose nmap KEY` or `:verbose imap KEY` to see the effective mapping.

## Terminal and shell

| Where | Key | Action |
| --- | --- | --- |
| zsh; idle nnn in tmux or WezTerm | Ctrl-G | Shared directory picker |
| zsh insert or command mode | Tab | fzf completion |
| fzf | Tab / Shift-Tab; Ctrl-N / Ctrl-P | Next / previous candidate |
| fzf | Alt-Space | Toggle selection when multiple selection is enabled |
| WezTerm | Ctrl-Shift-C / Ctrl-Shift-V | Copy / paste clipboard |
| WezTerm | Ctrl-0 | Reset font size |
| WezTerm | Ctrl-= / Ctrl-- | Increase / decrease font size |
| WezTerm | Cmd-Ctrl-F | Toggle macOS fullscreen |

WezTerm also sends control codes for Ctrl-/, Ctrl-;, Ctrl-,, and Ctrl-.:
respectively `0x1f`, `0x1c`, `0x1e`, and `0x1a`. Their action depends on the
application receiving them. Both Option keys send composed characters, which
can interfere with terminal Alt bindings; nnn's `;g` is a fallback.

Sources: [WezTerm](../wezterm/wezterm.lua), [fzf](../zsh/plugins/fzf/conf.zsh),
[zsh core](../zsh/core/core.zsh).

## tmux

| Key | Action |
| --- | --- |
| Ctrl-H / J / K / L, without prefix | Move left / down / up / right across panes and Neovim splits |
| Ctrl-arrow, without prefix | Resize pane in that direction |
| Prefix Ctrl-A | Send Ctrl-A to the application |
| Prefix 0…9 | Select numbered window |
| Prefix o / p, or Ctrl-O / Ctrl-P | Previous / next window |
| Prefix Tab | Next window |
| Prefix v / s | Split side by side / above and below, at the current directory |
| Prefix Ctrl-N | New window at the session home directory |
| Prefix Ctrl-_ | Fuzzy session switcher |
| Prefix Ctrl-C | Open `khal interactive` in a popup |
| Prefix z or Ctrl-Z | Toggle pane zoom |
| Prefix Ctrl-W | Last pane |
| Prefix Ctrl-J / Ctrl-K | Rotate panes forward / backward |
| Prefix - / = / + | Tiled / even-vertical / even-horizontal layout |
| Prefix m / M | Mark pane / clear mark |
| Prefix ' | Switch to the marked target |
| Prefix b | Toggle status bar |
| Prefix Enter | Enter copy mode |
| Copy mode: v / Ctrl-V | Begin selection / toggle rectangular selection |
| Copy mode: Escape / Ctrl-G | Cancel |
| Copy mode: H / L | Start / end of line |
| Prefix f | tmux-thumbs hints; selected text goes to `pbcopy` |
| Prefix u | fzf URL picker |
| Prefix Space | Configured easy-motion prefix |
| Prefix r | Reload tmux config |
| Prefix : | tmux command prompt |
| Prefix Ctrl-S | Confirm and save the tmuxp session layout |
| Prefix Ctrl-X | Confirm and kill the session |

The config starts by clearing the base bindings, then TPM plugins install their
own. It also contains Ctrl-backslash mappings for last-pane navigation and
sending Ctrl-L; inspect the live table if those keys behave unexpectedly.

Sources: [keybinds](../tmux/conf/keybinds.conf), [options](../tmux/conf/options.conf),
[plugin keys](../tmux/tmux.conf). Inspect a running session with
`tmux list-keys -T prefix` and `tmux list-keys -T root`.

## nnn and the readers

| Where | Key | Action |
| --- | --- | --- |
| nnn | l / Right / Enter | Enter a directory or open a file for reading |
| nnn | e | Edit the selected file in Neovim |
| nnn | Ctrl-G | Shared picker, through the terminal/tmux translation |
| nnn | ; g, or Alt-G | Run the directory-picker plugin directly |
| nnn | - | Return to the previous directory |
| nnn | ; x | Run the configured executable-bit action |
| `md-read` | a | Open Plannotator on the source file |
| `md-read` | s | Edit the companion `.notes.md` file |
| `md-read` | e | Edit the source in Neovim; save and quit to resume reading |
| `md-read` | o | Show letter hints on visible local file links; type a hint to open |
| Link hints | Escape / Backspace | Cancel / remove a typed hint letter |
| `md-read` | O (Shift-o) | Search all local links with fzf; Enter opens, Escape cancels |
| `md-read` | r | Reload source/comments/notes and recenter |
| `md-read` | /; n / N | Search; next / previous match |
| `md-read` | g / G | Beginning / end |
| `md-read` | m b; ' b | Set mark b / return to it |
| `md-read` | q | Leave the reader |
| `bat-read` | e | Edit the source in Neovim; save and quit to resume reading |
| `bat-read` | r | Reload and recenter after resizing |
| `bat-read` | /; n / N | Search; next / previous match |
| `bat-read` | g / G; q | Beginning / end; leave the reader |
| Plannotator | i, then v and movement keys | Position cursor, then select a passage |
| Plannotator | c, then Enter | Write and save a comment on the selection |
| Plannotator | q | Return to the reader |

Plannotator also accepts mouse selection. Its `d` action records a deletion
suggestion without changing source text. Both readers disable less's `v` editor
action because less is displaying a generated file. They reserve mark `z` for
restoring position after a reload.

Sources: [nnn settings](../zsh/plugins/nnn/conf.zsh), [reader keys](../glow/lesskeys),
[Markdown reader](../glow/scripts/md-read), [source reader](../bat/scripts/bat-read),
[source reader keys](../bat/lesskeys). nnn bookmarks are `h` for home, `d` for
Downloads, `t` for Teaching, and `c` for `.config` in its bookmark menu.

## Neovim

| Mode / file type | Key or command | Action |
| --- | --- | --- |
| Normal | [ Space / ] Space | Insert blank line above / below |
| Normal | gt / gT | Previous / next buffer, as configured here |
| Normal | Space u W | Toggle centered prose-width view |
| Normal | Space u ; | Toggle visible whitespace |
| Normal / visual | Space c f | Custom `gw` text-format mapping; a LazyVim lazy key can take precedence |
| Visual | Space t r | Translate the selection to Dutch and replace it |
| Prose / TeX | zg | Choose English, German, or Dutch spell file for the word |
| Prose / TeX | :SpellAddLang en, de, or nl | Add word to a specified spell file |
| TeX normal | Space i | Insert a new list item below |
| TeX insert | Ctrl-T | Insert a new list item below |
| TeX normal | Space m c | Texlab build |
| TeX normal | Space m v | Forward search to PDF |
| TeX normal | Space m x / Space m X | Clean auxiliary files / build artifacts |
| Completion | Ctrl-Space | Show / hide completion documentation |

The custom mapping helper skips a mapping if lazy.nvim already has a key handler
for it. Treat the table as the local definitions, and check effective mappings
when auditing. The TeX `Space m …` calls use the global helper inside a FileType
callback, so those mappings can remain after leaving the TeX buffer.

Sources: [keymaps](../nvim/lua/config/keymaps.lua), [autocmds](../nvim/lua/config/autocmds.lua),
[helper](../nvim/lua/config/utils.lua), [completion](../nvim/lua/plugins/coding.lua).

## PDFs, mail, and feeds

| Program / mode | Key | Action |
| --- | --- | --- |
| Zathura | Ctrl-T | Return to the matching editor/tmux pane |
| Zathura | Ctrl-click | Inverse SyncTeX to the clicked source location |
| Zathura | b / f | Toggle status bar / fullscreen |
| Zathura | i / r / Ctrl-R | Toggle recolor / reload / recolor then reload |
| Zathura | J / K; R; p | Zoom out / in; rotate; print |
| NeoMutt index | l / Enter | Read message |
| NeoMutt index/pager | cc / cr / cf / ca | Compose / reply / forward / group reply |
| NeoMutt compose | ce / ca | Edit message / attach with picker |
| NeoMutt compose | cc | Send; in HTML mode, first remove the Markdown body |
| NeoMutt index/pager | gh | Toggle HTML mode |
| NeoMutt HTML compose | ch / cC | Convert Markdown to alternatives / remove Markdown body without sending |
| NeoMutt index/pager | /; gi; gf | Custom mu search; inbox; choose folder |
| NeoMutt index | ? / ss | Limit messages / save message |
| NeoMutt index | dd / du / D | Delete current or tagged messages / undelete / purge |
| NeoMutt index/pager | Space Space; Tab | Tag message; toggle sidebar |
| NeoMutt index/pager | ! | Toggle the important flag (star) |
| NeoMutt | Space r; q / Q | Reload; sync mailbox and exit / exit |
| Newsboat lists | j / k; g / G; l / h | Move; first / last; open / back |
| Newsboat | Ctrl-H | Back |
| Newsboat lists | u | Toggle showing read feeds or articles |
| Newsboat articles | J / K; m; dd | Next / previous unread; toggle read; delete |
| Newsboat articles | ' d | Delete and purge via macro |

NeoMutt's `gr` currently calls `systemctl`; it needs a macOS replacement.
See [audit A1](audits.md#a1-neomutts-manual-sync-still-calls-systemd).

Sources: [Zathura](../zathura/zathurarc), [NeoMutt](../neomutt/core/mappings),
[HTML mode](../neomutt/dynamic/html_on), [Newsboat](../newsboat/configs/bindings).

## Amethyst

| Key | Action |
| --- | --- |
| Cmd-J / Cmd-K | Focus previous / next window |
| Cmd-, / Cmd-Shift-, | Move window to next / previous screen |
| Cmd-Shift-Left / Right | Throw window to adjacent Space |
| Cmd-Shift-1…5 | Throw window to numbered Space |
| Cmd-Shift-Y | Relaunch Amethyst |

Only the floating layout is configured. Most tiling and screen-focus bindings
are explicitly disabled. Source: [amethyst.yml](../amethyst/amethyst.yml).
