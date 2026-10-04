# Colors and typography

[Guide](README.md) · [Theme design](theme-design.md) · [Theme sources](../themes/README.md)

[themes/palette.json](../themes/palette.json) is the color source for the core
terminal apps. It starts from the existing WezTerm One Dark palette. The
background is a neutral dark gray; blue marks focus, cyan marks links, green
marks success, orange marks warnings, and red marks errors. Syntax uses purple
keywords, green strings, and orange numbers.

The palette contains the normal and bright ANSI colors, plus text, background,
surface, border, and comment colors. Its `roles` section assigns names such as
`accent`, `selection_bg`, and `error` to those colors. See the
[design document](theme-design.md#palette-and-template-format) for the distinction.

## Change colors

Edit the palette, then run:

```sh
theme-build --diff
theme-build
bat cache --build
theme-build --check
```

`--diff` previews the changes without writing. Both `--diff` and `--check` exit 1
when generated files differ from their sources. A validation error exits 2.
The normal build changes only files whose contents differ.

The command is available in new shells through the existing `*/scripts` PATH
setup. In an older shell, use `~/.config/themes/scripts/theme-build`.
The generated files are kept in Git, so apps work on a fresh checkout before
Python or the generator has been run. bat also needs its local theme cache built.

If bat 0.26.1 warns `Unknown theme 'shared-onedark'` when showing its own help,
use `bat --theme=TwoDark --help`. Its
[help renderer skips custom themes](https://github.com/sharkdp/bat/blob/v0.26.1/src/bin/bat/app.rs#L181)
even though it reads the configured theme name. This does not affect ordinary
file viewing, and rebuilding the cache does not fix the help warning. If the
warning occurs while viewing a file instead, check `bat --list-themes` and rebuild
with `bat cache --build` if the shared theme is missing.

Edit [templates](../themes/templates) when changing which UI element uses which
color. Edit the app's normal config for keybindings, fonts, spacing, or behavior.
Direct edits to generated output are reported by `--check` and replaced by the
next build.

## App coverage and reloads

| App | Color source and behavior | Apply to a running app |
| --- | --- | --- |
| WezTerm | [theme.lua](../wezterm/theme.lua), loaded by the main config; includes ANSI colors, selection, cursor, and tab bar | Watches the generated file and reloads it |
| Neovim | [theme.lua](../nvim/lua/config/theme.lua) overrides the onedark.nvim palette, lualine, and embedded terminal colors | Restart Neovim |
| tmux | [colors.conf](../tmux/conf/colors.conf), including thumbs and easy-motion hints | `tmux source-file "$XDG_CONFIG_HOME/tmux/conf/colors.conf"` |
| zsh, Pure, fzf | [theme.zsh](../zsh/theme.zsh), sourced after plugin configuration; includes syntax highlighting, suggestions, file-list colors, and picker colors | Start a new shell |
| nnn | `NNN_COLORS` and `NNN_FCOLORS` select terminal ANSI slots for contexts and file types | Restart from a new shell |
| Glow | [onedark.json](../glow/onedark.json); the layout and transparent background are preserved | Reopen the reader, or press `r` in `md-read` |
| bat | [shared-onedark.tmTheme](../bat/themes/shared-onedark.tmTheme), selected in tracked [config](../bat/config) | `bat cache --build`, then reopen the reader |
| Zathura | [theme](../zathura/theme), included by zathurarc | Reopen Zathura |
| NeoMutt | [colors](../neomutt/core/colors), with an additional [HTML mode theme](../neomutt/core/colors-html); ANSI slots inherit WezTerm's palette | Restart; HTML mode still has its red status indicator |
| Newsboat | [colors](../newsboat/configs/colors), using the terminal's 16 named color slots | Restart Newsboat |
| khal / ikhal | Generated `[palette]` section in [config](../khal/config); calendar identity colors still use terminal color names | Restart ikhal; CLI commands read the config each time |
| cmus | [shared.theme](../cmus/shared.theme), selected by [rc](../cmus/rc) after saved state loads | `:colorscheme shared`, or restart |
| btop | [shared.theme](../btop/themes/shared.theme), with the terminal background visible | Restart; if an older instance saved its old choice, select `shared` in options |
| Codex CLI | [shared-onedark.tmTheme](../codex/themes/shared-onedark.tmTheme), selected by `tui.theme` | Start a new session, or select `shared-onedark` with `/theme` |
| Plannotator | Built-in dark UI; document text inherits the terminal palette | Restart if the terminal palette changed |

Existing tmux servers may retain the old fzf options captured at startup. After
opening a new shell, update the URL picker with:

```sh
tmux set -g @fzf-url-fzf-options "$FZF_DEFAULT_OPTS"
```

## What uniform means here

Apps with RGB support receive the same colors. NeoMutt, Newsboat, cmus, nnn, and colored
file listings refer to ANSI slots and inherit their RGB values from WezTerm.
In another terminal, those apps follow that terminal's palette. Their selection
text uses ANSI black, which is lighter than the exact background used by RGB apps.

Neovim retains onedark.nvim's syntax rules and derives dark diagnostic and diff
backgrounds from the palette. Its main window stays transparent; popups and
lualine use the shared surface colors. The editor's warning highlight uses the
bright orange variant so it remains distinct from numbers and constants.

Codex's custom theme covers syntax and diff highlighting, as described in the
[official CLI documentation](https://learn.chatgpt.com/docs/cli-customization).
Its remaining interface colors and Plannotator's built-in dark UI are controlled
by those programs. This setup does not replace their renderers.

PDF page colors remain the document's own until Zathura recolor is toggled.
Websites, macOS controls, received HTML, and outgoing email styling are outside
this theme. Old Linux desktop configs and unused alternate cmus/btop themes are
also outside the generated set.

## Typography and spacing

WezTerm still uses ComicShannsMono Nerd Font at 20 pt, background opacity 0.9,
and macOS blur 10. Padding remains 5 pixels at the sides, 80 at the top, and 30
at the bottom. A single tab hides the tab bar. These settings belong in
[wezterm.lua](../wezterm/wezterm.lua), separately from the palette.

`md-read` centers a column up to 80 characters wide. Press `r` after resizing.
Its less pager has no trailing tilde filler. Plain `glow` does not add the
centering or annotation wrapper.

Neovim's `Space u W` opens an 82-column ZenMode window with soft wrapping and
hidden line numbers. tmux keeps its status bar at the top, followed by a blank
line. The theme generator does not change these layouts.
