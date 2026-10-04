# Weekly updates

[Guide](README.md) · [Programs](programs.md)

Run this from a terminal:

```sh
update
```

The command prints one progress line per step and lists changed package versions
or Git revisions. It keeps full output under
`~/.local/state/config-update/`, in a separate directory for each run. If a step
fails, it prints the last 60 log lines and the full log's path, continues with
the remaining steps, and exits with a failure status. A successful run ends
with a party popper.

## What it updates

| Step | Work performed |
| --- | --- |
| Homebrew | Refresh package definitions, then upgrade formulae and eligible casks |
| Zinit | Update the manager, installed shell plugins, and snippets; check Git fetches and upstream revisions |
| tmux | Update installed plugin repositories with fast-forward pulls and their submodules |
| Neovim plugins | Run Lazy's update operation and check its task errors |
| Mason | Refresh the registry, then update installed language servers, formatters, and other tools whose versions differ |
| Treesitter | Update installed parsers and wait for compilation to finish |

Homebrew covers the executables themselves, including Neovim, tmux, Glow,
Plannotator, and the Homebrew copy of TPM. Plugin managers cover a different
set of files, so updating Homebrew alone does not replace their update steps.
The tmux step also updates the plugin copy of TPM if it is installed there.

Each Neovim step uses a fresh headless process, started from the config directory.
Mason and Treesitter therefore
load the plugin code installed by the Lazy step. Their asynchronous work must
finish before the helper reports success. Lazy updates existing plugins; this
command does not run Lazy's cleanup operation.

## TeX packages

To include packages inside the installed TeX Live distribution:

```sh
update --tex
```

This adds `tlmgr update --self --all` with machine-readable output for the change
summary. The MacTeX installation is system-owned, so this step uses sudo and
may ask for a password. It updates the installed TeX Live release; moving to a
new annual release is separate maintenance.

## Scope and reloads

Homebrew runs its normal `upgrade` policy. The script does not force upgrades
of casks marked as self-updating or using a `latest` version. GUI apps with their
own updaters, App Store software, and macOS updates retain their own update paths.

Lean toolchains selected by a project's `lean-toolchain` file, project package
locks, the English dictionary submodule, and locally developed plugins stay at
their chosen revisions. The local mail plugin/parser source trees and custom
macOS app builds are maintained separately. There are no additional global npm
tools in the reviewed installation beyond Homebrew's npm itself.

After a successful run, restart Neovim and open a new shell to load updated code.
For tmux plugin changes, reload with Prefix then `r`; an already running plugin
process may need a new tmux session. The updater does not restart your sessions.

Only one copy of `update` can run at a time. If a process is killed before
its cleanup runs, the next invocation reports the lock directory and PID file.
Check that PID before removing the stale lock. Per-run logs are retained; old
run directories can be deleted when no longer needed.

## Implementation and checks

The command is [zsh/scripts/update](../zsh/scripts/update).
The Neovim helper is [nvim/update.lua](../nvim/update.lua). The old
[bootstrap update script](../.bootstrap/scripts/update.zsh) forwards to this
command. The scripts directory is already on the shell PATH.
The command was renamed from `config-update`; its log and lock directory keeps
the old name so existing history remains in one place. Run `rehash` if an existing
shell does not find `update` yet.

Tests used isolated fixtures for changed/unchanged packages, failures in each
step, continued execution after failure, the optional TeX step, and duplicate-run
locking. Headless Neovim tests checked asynchronous completion and error exits
with fixture manager APIs. These tests did not upgrade the live installation.
Zinit and tmux plugin updates were also exercised with real Git repositories
and temporary local remotes.

The manager behavior was checked against installed source and the upstream
[Lazy usage guide](https://lazy.folke.io/usage) and
[Zinit update instructions](https://github.com/zdharma-continuum/zinit#updating-zinit-and-plugins).
