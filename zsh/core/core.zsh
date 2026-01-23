export HISTSIZE=100000   # Max events to store in internal history.
export SAVEHIST=100000   # Max events to store in history file.
export HISTFILE=~/.zsh_history

# For gpg-agent
export GPG_TTY=$(tty)

setopt AUTO_CD
setopt AUTO_PUSHD

setopt INC_APPEND_HISTORY
setopt BANG_HIST                 # Don't treat '!' specially during expansion.
setopt EXTENDED_HISTORY          # Include start time in history records
setopt INC_APPEND_HISTORY        # Write to the history file immediately, not when the shell exits.
setopt HIST_EXPIRE_DUPS_FIRST    # Expire a duplicate event first when trimming history.
setopt HIST_IGNORE_DUPS          # Do not record an event that was just recorded again.
setopt HIST_IGNORE_ALL_DUPS      # Remove old events if new event is a duplicate
setopt HIST_FIND_NO_DUPS         # Do not display a previously found event.
setopt HIST_IGNORE_SPACE         # Do not record an event starting with a space.
setopt HIST_SAVE_NO_DUPS         # Do not write a duplicate event to the history file.
setopt HIST_REDUCE_BLANKS        # Minimize unnecessary whitespace
setopt HIST_VERIFY               # Do not execute immediately upon history expansion.

alias xs="sudo shutdown -s now"
alias xr="sudo shutdown -r now"
alias xh="sudo shutdown -h now"

alias cp='command cp -vi'
alias mv='command mv -vi'
alias rm='trash'

alias ll='command gls -A --color=auto --group-directories-first'
alias ls='command gls -A --color=auto --group-directories-first --time-style="+"'

alias lsp='command stat -c "%A %a %N"'

alias grep="grep --color=auto"

alias N='sudo nnn'

alias tmux="tmux -2"

alias mk=make

alias music=cmus

alias mail=neomutt

bindkey -v

cursor_mode

bindkey -rpM viins '^[^[' # ESC-ESC to switch from ins to normal
