#! /usr/bin/env zsh

. $ZDOTDIR/plugins/fzf/conf.zsh

session="$(tmux list-sessions -F '#{session_name}' | fzf-tmux -p --prompt="🔎 ")"

if [[ -n $session ]]; then
  tmux switch -t $session
fi
