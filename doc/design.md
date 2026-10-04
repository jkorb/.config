# Design and layout

[Guide](README.md) · [Workflows](workflows.md) · [Audit starting points](audits.md)

## One shell environment

[zsh/.zshenv](../zsh/.zshenv) defines the directories and defaults used by the
shell scripts. `EDITOR`, `VISUAL`, and `SUDO_EDITOR` all select `nvim`; manual
pages go through bat. The `path` array is deduplicated and includes each
`.config/*/scripts/` directory, plus `~/.local/bin` and `~/.cargo/bin`.
On macOS, Homebrew's `/opt/homebrew/bin` and `sbin` take precedence.

| Variable | Value | Use |
| --- | --- | --- |
| `XDG_CONFIG_HOME` | `~/.config` | Configuration and these scripts |
| `XDG_DATA_HOME` | `~/.local/share` | Application data, including calendars and annotations |
| `XDG_STATE_HOME` | `~/.local/state` | State such as Neovim's server map |
| `XDG_CACHE_DIR` | `~/.cache` | Local convention used by sync and picker scripts |
| `ZDOTDIR` | `~/.config/zsh` | Shell startup files |
| `GNUPGHOME` | `~/.config/gnupg` | GnuPG home |
| `MAILDIR` | `~/.mail` | Downloaded mail |

`XDG_CACHE_DIR` is this setup's variable name. Programs that use
`XDG_CACHE_HOME` do not learn its value from that export. Many still end up in
`~/.cache` through their own defaults or explicit settings.

The shell's [.zshrc](../zsh/.zshrc) registers autoloaded functions, then loads
[core settings](../zsh/core/core.zsh) and [plugins](../zsh/plugins/plugins.zsh).
The outer home-directory startup links are outside this repository; a fresh
installation needs to arrange for zsh to read these files.

## Shared actions, separate applications

The directory picker is one [executable](../zsh/scripts/fzf-goto-dir). The zsh
widget consumes its selected path and runs `cd`; the nnn plugin sends that path
through nnn's control pipe. Both use the same exclusions and history. tmux and
WezTerm translate Ctrl-G only when nnn has no child program running, so an
editor or picker launched from nnn keeps its own Ctrl-G behavior.

Reading follows the same approach. nnn delegates file opening to
[nnn-open](../nnn/scripts/nnn-open), while its editor command remains Neovim.
Markdown is rendered by Glow and paged by less. Plannotator supplies passage
comments, and Neovim edits general notes in a companion file. Returning from
either annotation tool rebuilds the reading view. The source document is not
changed by adding comments.

```text
WezTerm
  tmux → zsh → nnn
                ├─ l / Right / Enter → nnn-open
                │                       ├─ Markdown → md-read → Glow + less
                │                       │                ├─ a → Plannotator
                │                       │                └─ s → Neovim notes
                │                       ├─ text → bat
                │                       └─ other → macOS open
                └─ e → Neovim source file
```

tmux is optional for the reader and file manager. `n`, the shell wrapper for
nnn, also changes the shell directory to the last directory visited on exit.

## Writing without hard line breaks

Prose and TeX buffers use soft wrapping with `linebreak`, `breakindent`, and
`textwidth=0`. The screen wraps a long paragraph without rewriting its source
lines. ZenMode narrows the editing window to 82 columns. The Markdown reader
has an independent maximum width of 80 columns.

TeX completion puts snippets and symbols ahead of general suggestions. Inside
recognized citation and reference commands, the completion configuration
leaves the lookup to the language server. Texlab calls latexmk for builds and
the Zathura wrapper for forward search. Neovim records sockets, working
directories, and process IDs so PDF callbacks can find the relevant editor
and tmux pane.

Sources: [autocmds](../nvim/lua/config/autocmds.lua),
[completion](../nvim/lua/plugins/coding.lua), [editor view](../nvim/lua/plugins/editor.lua),
[server map](../nvim/lua/config/options.lua), [Zathura scripts](../zathura/scripts).

## Local files and remote services

Mail is stored in Maildirs and searched through mu. Calendars are local files
read by khal. launchd runs the sync scripts; those jobs have explicit environment
variables because they do not start through an interactive shell. Credentials
are retrieved through pass. The [services page](services.md) traces those paths.

There are two editor features that call external AI services. Copilot is enabled
through LazyVim, with `mail` and `csv` disabled in the local override. The
translation command sends the selected text and a saved instruction prompt to
the OpenAI API, then replaces the selection if the buffer has not changed. Its
request sets `store=false`; this describes the request, not a general privacy
guarantee. Plannotator comments in the reading workflow stay in local files;
the wrapper uses its export command and does not send them to an agent.

Sources: [Copilot override](../nvim/lua/plugins/ai.lua),
[translation](../nvim/lua/config/openai_translate.lua), [reader](../glow/scripts/md-read).

## What a clone contains

The root [.gitignore](../.gitignore) ignores top-level entries by default, then
allows named config directories. A new directory needs an explicit exception.
Application caches, plugin installations, generated apps, and private files
have additional exclusions.

Some exclusions affect reproducibility: bat's config, LazyVim's extras and lock
file, tmux session layouts, and mail aliases are local. The mail plugin and its
Treesitter parser come from projects under `~/Dropbox/Projects`, outside this
repo. The English dictionary is a Git submodule. A clone alone therefore needs
both package installation and local files before it can reproduce this Mac.

Spell additions are an exception to ordinary manual commits: the Neovim
`zg` helper schedules a commit of the configured spell files after adding a word.
It targets this repo and skips in-progress Git operations. See
[autocmds.lua](../nvim/lua/config/autocmds.lua) before changing that behavior.
