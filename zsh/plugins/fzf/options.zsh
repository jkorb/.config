# Shared by the shell and the khal contact picker.
FZF_DEFAULT_OPTS+="
  -i
  --no-info
  --no-bold
  --prompt=' '
  --pointer=''
  --marker=' '
  --no-height
  --layout=reverse
  --cycle
  --tabstop=2
  --height=40%
  --bind=tab:down,btab:up,alt-space:toggle,ctrl-n:down,ctrl-p:up"

mkdir -p "$XDG_CACHE_DIR/fzf"

FZF_DEFAULT_OPTS+="
  --history=$XDG_CACHE_DIR/fzf/history
  --history-size=1000000000"

export FZF_DEFAULT_OPTS
