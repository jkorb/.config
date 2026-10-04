# The toolbox

This is a guide to the configuration on this Mac: how the programs fit together,
where their settings live, and which parts still need attention.

The daily path runs through WezTerm, tmux, zsh, nnn, and Neovim. Markdown has its
own reading workflow with Glow and Plannotator. Mail, calendars, and PDFs also
have terminal tools, with small scripts connecting them to macOS.

## Find a setting

| Page | Contents |
| --- | --- |
| [Programs](programs.md) | Main tools, package managers, and older configs |
| [Design and layout](design.md) | Startup, directory conventions, shared scripts, and local state |
| [Daily workflows](workflows.md) | Jumping directories, reading and commenting, writing, and PDF navigation |
| [Keybindings](keybindings.md) | Custom keys, grouped by program and mode |
| [Colors and typography](themes.md) | Shared palette, generated themes, fonts, and reload instructions |
| [Theme design](theme-design.md) | Source format, generation, ownership, tests, and adding an app |
| [Mail and background jobs](services.md) | Sync, notifications, HTML mail, and service management |
| [Weekly updates](updates.md) | One command for packages, plugins, language tools, and parsers |
| [Audit starting points](audits.md) | Findings from this review, open questions, and checks for later reviews |
| [Installed packages](packages.md) | Dated Homebrew inventory, including dependencies |

## Common changes

- Change colors in the [shared palette](../themes/palette.json), then run `theme-build`.
- Change the terminal font in [WezTerm](../wezterm/wezterm.lua).
- Change the directory search exclusions in [fzf's fdignore](../zsh/plugins/fzf/fdignore).
- Change Markdown color assignments in the [Glow template](../themes/templates/glow.json).
- Change shell shortcuts in [zsh core](../zsh/core/core.zsh) or [autoloads](../zsh/autoloads).
- Change tmux keys in [keybinds.conf](../tmux/conf/keybinds.conf).
- Change editor behavior in [Neovim's config](../nvim/lua/config) and [plugin settings](../nvim/lua/plugins).
- Check background jobs with `lctl info`; their sources are in [launchd](../launchd).
- Run `update` for [weekly maintenance](updates.md).

## Scope of this guide

Reviewed on 2026-10-03 against the working tree, including the recent reader and
directory-picker changes. Linked config files are the source of truth. These
pages describe configured behavior; they do not establish that every service,
plugin, or macOS association is active in a running session.

The package inventory records what Homebrew has installed. Older Linux configs
remain in the repository, and several settings used on this Mac are ignored by
Git. Those distinctions are called out where they affect rebuilding or auditing
the setup. Private account contents, credentials, histories, and agent sessions
are outside this guide.

For an AI-assisted review, start with [the audit page](audits.md), then read the
linked sources for the chosen area. Update the relevant page when behavior
changes; keep one-off test results in the audit record.
