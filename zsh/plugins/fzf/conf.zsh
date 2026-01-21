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

[[ ! -d $XDG_CACHE_DIR/fzf ]] && mkdir $XDG_CACHE_DIR/fzf

FZF_DEFAULT_OPTS+="
  --history=$XDG_CACHE_DIR/fzf/history
  --history-size=1000000000"

 FZF_DEFAULT_OPTS+="
   --color bg:-1,fg:7,hl:5
   --color bg+:4,fg+:0,hl+:2
   --color preview-bg:-1,preview-fg:7
   --color prompt:2,spinner:-1"

export FZF_DEFAULT_OPTS

export FZF_DEFAULT_COMMAND='fd --type file --follow --hidden --exclude .git'
export FZF_CTRL_T_COMMAND=$FZF_DEFAULT_COMMAND

export FZF_ALT_C_OPTS="--preview 'tree -C {} | head -200'"

export FZF_TAB_COMPLETION_PROMPT="󰌒  "

if [[ -r /opt/homebrew/opt/fzf/shell/key-bindings.zsh ]]; then
  source /opt/homebrew/opt/fzf/shell/key-bindings.zsh
fi
source $HOME/.local/share/zinit/plugins/lincheney---fzf-tab-completion/zsh/fzf-zsh-completion.sh

zle     -N            fzf-goto-dir-widget

bindkey -M vicmd '^g' fzf-goto-dir-widget
bindkey -M viins '^g' fzf-goto-dir-widget

bindkey -M viins '^I' fzf_completion
bindkey -M vicmd '^I' fzf_completion
