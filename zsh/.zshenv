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
export EDITOR="nvim"
export VISUAL="nvim"

export BROWSER='firefox'

typeset -U path

for dir in $XDG_CONFIG_HOME/*/scripts/; do
  path+=("$dir")
done

path+=("$HOME/.local/bin" "$HOME/.cargo/bin")
if [[ $(uname) == "Darwin" ]]; then
  path=("/opt/homebrew/bin" "/opt/homebrew/sbin" $path)
  path+=("/Library/Tex/texbin")
fi
