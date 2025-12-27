export LANG=en_US.UTF-8

export XDG_CONFIG_HOME="$HOME/.config"
export XDG_CACHE_DIR="$HOME/.cache"
export XDG_DATA_HOME="$HOME/.local/share"
export XDG_STATE_HOME="$HOME/.local/state"

export GNUPGHOME="${XDG_CONFIG_HOME}/gnupg"

export BASH_ENV="$HOME/.bashrc"

export MAILDIR="$HOME/.mail"

export ZDOTDIR="${XDG_CONFIG_HOME}/zsh"

export SUDO_EDITOR="nvim"
# export EDITOR="tmux split-window nvim"
export EDITOR="nvim"
# export VISUAL="nvimwrap"

export ELECTRON_OZONE_PLATFORM_HINT="wayland"

# export NVIM_LISTEN_ADDRESS="/tmp/nvimsocket"

for dir in $XDG_CONFIG_HOME/*/scripts/; do
  path+=("$dir")
done

path+=$HOME/.cargo/bin

export BROWSER='firefox'

typeset -U path
path+=$HOME/.local/bin

if uname | grep -q Darwin &> /dev/null; then
  PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"
  path+=("/Library/Tex/texbin")
fi

fpath+=$ZDOTDIR/autoloads
autoload -Uz $ZDOTDIR/autoloads/*
