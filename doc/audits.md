# Audit starting points

[Guide](README.md) · [Design](design.md) · [Installed packages](packages.md)

This is the record of the documentation review on 2026-10-03. It identifies
specific follow-up work. Application settings were left unchanged during this
review; the new docs and their Git ignore exception are the only setup changes.

## Evidence and limits

The review read shell startup files, custom scripts, keybindings, editor plugin
specs, themes, mail settings, app wrapper sources, and launchd plists. It also
checked Git tracking rules, selected dependency paths, and the local Homebrew
inventory. It did not test mail delivery, calendar sync, notification delivery,
every effective editor mapping, or macOS app registration.

Earlier work exercised directory jumping and the Markdown reader with temporary
fixtures. Those results are recorded in the local agent log; this review did
not rerun the interactive tests. Configuration and runtime behavior remain
separate kinds of evidence.

## Findings

### A1. NeoMutt's manual sync still calls systemd

Confirmed in [core/mappings](../neomutt/core/mappings): `gr` runs
`systemctl --user start isync.service`. The Mac's scheduled sync lives in
[launchd/scripts/mail-sync](../launchd/scripts/mail-sync). Manual and scheduled
sync therefore use different platform assumptions. A follow-up should choose
the intended Mac command and check that returning to NeoMutt refreshes the
mailbox. Do not test this by sending mail.

The same config sets its spellchecker to `/usr/bin/hunspell` in
[core/settings](../neomutt/core/settings); that path is absent on this Mac.
Neovim's own spelling is a separate path and is not evidence that NeoMutt's
spellchecker command works.

### A2. Sync failures can look successful

[mail-sync](../launchd/scripts/mail-sync) calls `mbsync`, mu, and the notifier
without checking their returned status, then exits zero. Output is suppressed
outside debug mode. [vdirsyncer-sync](../launchd/scripts/vdirsyncer-sync) also
continues after failed discover/sync commands. `lctl info` can report a successful
job exit after a child command failed.

[mail-notify](../launchd/scripts/mail-notify) advances its last-run timestamp
even when the mu query fails. A later successful query can therefore skip the
failed interval. Include this case when testing notification recovery.

The follow-up is to decide which failures should stop the job and how they
should be reported. Test offline behavior, a failed child command, and a
successful run with command stubs before trying live sync. Also review the
DavMail gate: mail sync currently skips every account when that process is absent.

### A3. A clone does not reproduce the editor and theme

Git ignores `nvim/lazyvim.json` and `nvim/lazy-lock.json`.
The local files select the Markdown/Copilot extras for LazyVim. bat's config and
shared theme are now included in the repo; a new installation also needs
`bat cache --build`. [mail.lua](../nvim/lua/plugins/mail.lua) and
[treesitter.lua](../nvim/lua/plugins/treesitter.lua) point to two source trees
under `~/Dropbox/Projects`; both paths exist here, but are outside this repo.

The [Brewfile](../.bootstrap/macOS/Brewfile) lists an older terminal, font, and
Zathura setup. The [installed snapshot](packages.md) documents the current
Homebrew state without resolving which packages should belong in a rebuild.
Decide which local choices should be versioned, then document the remaining
installation steps. Include the English dictionary submodule and the external
mail projects in that decision.

### A4. Some editor mappings depend on load order

[custom_map](../nvim/lua/config/utils.lua) declines to create a mapping if
lazy.nvim has a handler for that key. The custom `Space c f` definition is
therefore not proof that `gw` wins over LazyVim's formatter mapping.

The TeX FileType callback also installs its `Space m …` mappings globally.
Open a TeX buffer, inspect those mappings, then switch to Markdown and inspect
them again. Disabled vim-pandoc mappings in
[markdown.lua](../nvim/lua/plugins/markdown.lua) should not be counted as active.
A useful result would record the final mapping and defining file for each
disputed key.

### A5. Session save guard needs correction

[zsh/autoloads/:w](../zsh/autoloads/:w) contains
`if [[ ! validate-session ]]; then`. That tests a string instead of invoking
the [validation function](../zsh/autoloads/validate-session). Its intended guard
does not run before the script backs up and freezes a session layout.

Check the helper with a missing session variable and with a valid temporary
session layout. The related [tmux-new-window](../tmux/scripts/tmux-new-window)
reads `TMUX_SESSION_HOME`, while the main helpers use `TMUXP_SESSION_HOME`.
Establish whether that script has callers before changing or removing it.

### A6. Shared theme generation added

The 2026-10-04 theme change replaces the separate RGB palettes with
[shared sources](../themes/README.md) and generated native files. See the
[design document](theme-design.md) for ownership and validation. Run
`theme-build --check` to detect drift. Visual review should still check contrast,
ANSI-only consumers, and the app-controlled portions of Codex and Plannotator.

### A7. Repository contents mix config and older state

Git currently tracks `btop/btop.log`, `cmus/lib.pl_bak`, and
`.bootstrap/systemd/applications/mimeinfo.cache`. Several Linux directories
remain alongside the Mac setup. Their presence does not prove they are unused,
but they should be classified before a cleanup or a portability audit.

Use file names and Git metadata first. Logs, mail, aliases, and agent histories
can contain personal content and are not needed to decide which directories
belong in a configuration repository.

### A8. Multi-process behavior needs focused checks

The Markdown reader uses a temporary directory per run, but several other
helpers use shared paths: nnn's `.lastd` and the Neovim app socket.
Neovim also rewrites its server map on startup, directory
changes, and exit. These are observations from source, not demonstrated races.

Open two instances with temporary fixtures and check whether they overwrite
each other's state. For annotations, test what happens when source lines change
and when the document moves: Plannotator's storage identity is based on the
file path.

NeoMutt's active HTML workflow now uses a private directory per composition.
Isolated tests capture outgoing MIME to local files and cover repeated editing,
previews, quoted markup/images, ordinary attachments, and failed-send retries.
The old shared-command-file converter is no longer bound. Markdown restoration
from postponed drafts after restarting NeoMutt remains a follow-up.

## Review prompts

These prompts keep an AI review tied to evidence and a defined area:

> Audit the directory-jump workflow from WezTerm/tmux through zsh and nnn.
> Read doc/workflows.md and the linked implementations. Check cancellation,
> paths with spaces, child processes, and missing environment variables.
> Report observed bugs separately from untested concerns, with file references
> and a way to reproduce each finding. Do not change the setup yet.

> Audit whether this repo can reproduce the current Neovim setup on another Mac.
> Start with doc/programs.md and finding A3. Trace plugin loading, ignored files,
> external source directories, dictionaries, language servers, and keymap order.
> Produce a list of missing inputs and the smallest changes that would cover them.

> Audit the launchd mail and calendar scripts for failure handling. Use local
> fixtures and stub commands. Check exit codes, offline behavior, scheduling,
> and notification deduplication. Do not run live sync or send notifications.

## Recording the next audit

Record the date, scope, source revision or working-tree state, and commands
actually run. Each finding should include a location, observed behavior,
consequence, and a proposed check or fix. Mark inferences and untested cases.
Close a finding only after the relevant behavior has been checked, and update
the guide if that behavior changes.

Useful read-only starting commands, run from the repo root:

```sh
git status --short
git ls-files
git check-ignore -v nvim/lazyvim.json nvim/lazy-lock.json
themes/scripts/theme-build --check
brew list --formula --versions
brew list --cask --versions
tmux list-keys -T prefix
tmux list-keys -T root
lctl info
```

Use `rg --hidden` with named config directories when looking for definitions.
A recursive search of the whole `.config` tree also reaches caches, plugin
installations, and private state that are outside most config audits.

## Documentation checks

The initial guide received one factual revision pass after drafting. All pages
were parsed with Pandoc's GitHub Markdown reader, and relative file links and
heading anchors were checked. Git's whitespace check passed.

The Avoid AI Writing detector ran in technical context. Its strict zero-finding
gate reported three matches: the noun "features" in the design page, the valid
"picker" link in the programs table, and the root README's navigation list.
These are intentional reference material, not prose problems. A manual review
found no further style edits to make. Quote normalization ran and made no changes.
The paired preservation validator was not run: these pages are newly authored
documentation, with facts checked against the linked config sources.
