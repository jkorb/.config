export HISTSIZE=100000   # Max events to store in internal history.
export SAVEHIST=100000   # Max events to store in history file.
export HISTFILE=~/.zsh_history

# For gpg-agent
export GPG_TTY=$(tty)

setopt AUTO_CD
setopt AUTO_PUSHD

setopt INC_APPEND_HISTORY
# setopt APPEND_HISTORY
setopt BANG_HIST                 # Don't treat '!' specially during expansion.
setopt EXTENDED_HISTORY          # Include start time in history records
# setopt APPEND_HISTORY            # Appends history to history file on exit
setopt INC_APPEND_HISTORY        # Write to the history file immediately, not when the shell exits.
# setopt SHARE_HISTORY             # Share history between all sessions.
setopt HIST_EXPIRE_DUPS_FIRST    # Expire a duplicate event first when trimming history.
setopt HIST_IGNORE_DUPS          # Do not record an event that was just recorded again.
setopt HIST_IGNORE_ALL_DUPS      # Remove old events if new event is a duplicate
setopt HIST_FIND_NO_DUPS         # Do not display a previously found event.
setopt HIST_IGNORE_SPACE         # Do not record an event starting with a space.
setopt HIST_SAVE_NO_DUPS         # Do not write a duplicate event to the history file.
setopt HIST_REDUCE_BLANKS        # Minimize unnecessary whitespace
setopt HIST_VERIFY               # Do not execute immediately upon history expansion.


# Aliases
# ----------------------------------------

alias cp='command cp -vi'
alias mv='command mv -vi'
alias rm='command rm -vi'

if uname | grep -q Darwin &> /dev/null; then
  alias ll='command gls -A --color=auto --group-directories-first'
  alias ls='command gls -A --color=auto --group-directories-first --time-style="+"'
else
  alias ll='command ls -A --color=auto --group-directories-first'
  alias ls='command ls -A --color=auto --group-directories-first --time-style="+"'
fi

alias lsp='command stat -c "%A %a %N"'

alias grep="grep --color=auto"

# Custom

alias N='sudo nnn'

# Arch

alias pkg_purge='sudo pacman -Rns $(pacman -Qtdq)'

alias tmux="tmux -2"

alias mk=make

alias mail=neomutt

bindkey -v

# Cursor modes
cursor_mode

# ESC-ESC to switch from ins to normal
bindkey -rpM viins '^[^['

# eval "$(_KHAL_COMPLETE=zsh_source khal)"

# Put in command mode
# zle-line-init() { zle -K vicmd; }
# zle -N zle-line-init
