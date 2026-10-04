#!/bin/zsh
# Compatibility entry point; the maintained updater is on the shell PATH.
exec "${XDG_CONFIG_HOME:-$HOME/.config}/zsh/scripts/update" "$@"
