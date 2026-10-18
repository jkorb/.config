# Programs

[Guide](README.md) · [Installed versions](packages.md)

## Terminal and files

| Program | Job in this setup | Configuration |
| --- | --- | --- |
| WezTerm | Terminal windows, font, ANSI colors, clipboard, and key translation | [wezterm.lua](../wezterm/wezterm.lua) |
| tmux, tmuxp | Panes and named sessions; session layouts saved per host | [tmux.conf](../tmux/tmux.conf), [scripts](../tmux/scripts) |
| zsh, Zinit, Pure | Interactive shell, plugin loading, prompt | [.zshrc](../zsh/.zshrc), [plugins](../zsh/plugins/plugins.zsh) |
| fzf, fd, tree | File completion and the shared directory picker with a tree preview | [fzf settings](../zsh/plugins/fzf/conf.zsh), [picker](../zsh/scripts/fzf-goto-dir) |
| nnn | File manager; installed as the `nnn-nerd` formula | [shell settings](../zsh/plugins/nnn/conf.zsh), [opener](../nnn/scripts/nnn-open) |
| Glow, less | Render and page Markdown through `md-read` | [Glow](../glow), [reader](../glow/scripts/md-read) |
| Plannotator TUI | Comments attached to selected passages | [UI settings](../plannotator-tui/config.toml) |
| Pandoc | Math conversion and local-link parsing for the reader | [math filter](../glow/terminal-math.lua), [link picker](../glow/scripts/md-links) |
| bat | Source reader via `bat-read`; highlighting for manual pages | [reader](../bat/scripts/bat-read), [config](../bat/config), [generated theme](../bat/themes/shared-onedark.tmTheme) |
| GNU coreutils, trash | Colored `gls`; interactive copy/move; shell `rm` alias sends files to trash | [shell aliases](../zsh/core/core.zsh) |

Zinit loads syntax highlighting, completions, fzf tab completion, autosuggestions,
history substring search, autopair, and Pure. fzf tab completion also needs
`gawk`. TPM loads tmux-thumbs, easy-motion, fzf-url, nerd-font-window-name,
tmux-yank, and tmux-open. Their bindings are separate from the base tmux table.

Easy-motion launches `python` by name. On this Mac, `/opt/homebrew/bin/python`
links to `/opt/homebrew/opt/python@3/libexec/bin/python`. A missing
`/opt/homebrew/bin/python3` left the previous link dangling, even though Python
remained available in the installed formula's `libexec/bin`.

## Writing, code, and logic

Neovim uses LazyVim and lazy.nvim. The local `nvim/lazyvim.json` enables the
Markdown and Copilot extras; that file and `lazy-lock.json` are ignored. The
tracked configuration therefore does not fully specify the installed editor.

| Tool or plugin | Configured use | Source |
| --- | --- | --- |
| Blink, blink.compat, LuaSnip | Completion and snippets, with extra priority for TeX environments and symbols | [coding.lua](../nvim/lua/plugins/coding.lua), [latex.lua](../nvim/lua/plugins/latex.lua) |
| Texlab, latexmk, MacTeX | TeX completion, build commands, and SyncTeX positions | [lsp.lua](../nvim/lua/plugins/lsp.lua), [latexmkrc](../latexmk/latexmkrc) |
| Zathura, nvr | PDF reading and returning to the matching editor instance | [zathurarc](../zathura/zathurarc), [scripts](../zathura/scripts) |
| Marksman | Markdown and mail LSP configuration | [markdown.lua](../nvim/lua/plugins/markdown.lua) |
| clangd, yamlls, lua_ls, bashls, pyright | Language servers declared in the editor config | [lsp.lua](../nvim/lua/plugins/lsp.lua) |
| Treesitter | Syntax parsing, including TeX and a locally developed mail parser | [treesitter.lua](../nvim/lua/plugins/treesitter.lua) |
| lean.nvim, elan | Lean editing and toolchains | [lean.lua](../nvim/lua/plugins/lean.lua) |
| Prover9, prover9.nvim | Automated theorem proving and its editor support | [thm.lua](../nvim/lua/plugins/thm.lua) |
| ZenMode | Centered, 82-column editing window | [editor.lua](../nvim/lua/plugins/editor.lua) |
| Copilot | Editor completion; explicitly disabled for `mail` and `csv` | [ai.lua](../nvim/lua/plugins/ai.lua) |
| OpenAI translation command | Replace selected text with a Dutch translation | [implementation](../nvim/lua/config/openai_translate.lua), [prompt](../nvim/prompts/openai_translate_dutch.txt) |
| Pandoc | Markdown conversion, including HTML mail | [neomutt-html](../neomutt/scripts/neomutt-html) |
| Chawan (`cha`) | Optional interactive HTML mail viewer and terminal browser, with Sixel images in tmux/WezTerm | [config](../chawan/config.toml), [mailcap](../neomutt/core/mailcap) |

Neovim also uses spelling and dictionary completion for prose, Tabular for
alignment, vim-gnupg for encrypted files, Cutlass for cut/delete behavior, and
nvim-tmux-navigation for moving between editor splits and terminal panes.
The English completion dictionary comes from the [english-words submodule](../.gitmodules).
Spell additions for English, German, and Dutch live in [nvim/spell](../nvim/spell).

The vim-pandoc, headlines, render-markdown, and nvim-lint specs in
[markdown.lua](../nvim/lua/plugins/markdown.lua) are disabled. Their commented or
disabled mappings should not be treated as available commands.

## Mail, calendars, and the desktop

| Program | Job | Configuration |
| --- | --- | --- |
| NeoMutt | Read and compose mail in local Maildirs | [muttrc](../neomutt/muttrc), [core](../neomutt/core) |
| isync (`mbsync`), mu | Download mail and index it for search | [isyncrc](../isyncrc), [mail-sync](../launchd/scripts/mail-sync) |
| msmtp | Send outgoing mail for the selected account | [config](../msmtp/config) |
| DavMail | Local gateway for institutional mail and calendars | [template](../davmail/davmail.properties.template) |
| vdirsyncer, khal | Sync calendar files, show the agenda, and edit events | [vdirsyncer](../vdirsyncer/config), [khal](../khal/config) |
| terminal-notifier, launchd | Notifications and scheduled jobs | [services guide](services.md) |
| Newsboat | RSS reading; automatic reload every 60 minutes | [config](../newsboat/config) |
| cmus | Music player, also available as shell command `music` | [cmus](../cmus) |
| btop | Process and resource monitor | [btop.conf](../btop/btop.conf) |
| Amethyst | Focus and window movement, with a floating layout | [amethyst.yml](../amethyst/amethyst.yml) |
| pass, GnuPG, pinentry-mac | Password retrieval and GPG prompts | [gpg-agent.conf](../gnupg/gpg-agent.conf), [passcopy](../zsh/autoloads/passcopy) |
| Git, Git Credential Manager | Version control and credential handling | [git/config](../git/config) |
| Firefox | Shell's preferred browser; other openers can use macOS associations | [.zshenv](../zsh/.zshenv) |
| Codex | Coding agent with local config and plugins | [codex/config.toml](../codex/config.toml) |

The app wrappers in [nvim/app](../nvim/app), [neomutt/app](../neomutt/app), and
[tmux/app](../tmux/app) launch terminal programs through WezTerm. The Neovim
wrapper sends opened files to a named Neovim socket. NeoMutt's wrapper handles
`mailto:` links. These source directories do not prove which app bundle macOS
currently has registered.

## Installation sources and older files

Homebrew supplies most executables and GUI apps. The [installed inventory](packages.md)
includes personal formulas for nnn, khal, Lua, browserpass, and the Zathura PDF
plugin, as well as separate Zathura and Plannotator taps. Neovim plugins use
lazy.nvim; shell plugins use Zinit; tmux plugins use TPM. Language servers and
language toolchains may have their own installers and are not covered by the
Homebrew list.

The [macOS Brewfile](../.bootstrap/macOS/Brewfile) is an older installation list.
It still names Alacritty, Brave, a different font, and earlier Zathura formulas.
Use it as a reference until it has been reconciled with this machine.

[systemd](../systemd), [dunst](../dunst), [wlogout](../wlogout), [yay](../yay),
and the Linux parts of [.bootstrap](../.bootstrap) describe Linux components.
They are retained files, not the scheduler or desktop stack described here.
[qmk/qmk.ini](../qmk/qmk.ini) selects a Planck keyboard and keymap; it does not
contain the keyboard's key layout. [despell](../despell/config.toml) contains
program icon choices; its current consumer was not established in this review.
