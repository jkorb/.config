FZF_DEFAULT_OPTS=$FZF_DEFAULT_OPTS

FZF_DEFAULT_OPTS+="
  -i
  --no-info
  --no-bold
  --prompt='▶ '
  --pointer=' '
  --marker='▶ '
  --no-height
  --layout=reverse
  --cycle
  --tabstop=2
  --height=40%
  --bind=tab:down,btab:up,alt-space:toggle,ctrl-n:down,ctrl-p:up"

  # ",alt-space:clear-selection"

[[ ! -d $XDG_CACHE_DIR/fzf ]] && mkdir $XDG_CACHE_DIR/fzf

FZF_DEFAULT_OPTS+="
  --history=$XDG_CACHE_DIR/fzf/history
  --history-size=1000000000"

# FZF_DEFAULT_OPTS+=" \
# --color=bg+:-1,bg:-1,spinner:#f5e0dc,hl:#f38ba8 \
# --color=fg:#cdd6f4,header:#f38ba8,info:#cba6f7,pointer:#f5e0dc \
# --color=marker:#b4befe,fg+:#cdd6f4,prompt:#cba6f7,hl+:#f38ba8 \
# --color=selected-bg:#45475a \
# "

 FZF_DEFAULT_OPTS+="
   --color bg:-1,fg:7,hl:5
   --color bg+:4,fg+:0,hl+:2
   --color preview-bg:-1,preview-fg:7
   --color border:-1,gutter:-1,header:8
   --color info:8,marker:5,pointer:-1
   --color prompt:2,spinner:-1"

export FZF_DEFAULT_OPTS

export FZF_DEFAULT_COMMAND='fd --type file --follow --hidden --exclude .git'
export FZF_CTRL_T_COMMAND=$FZF_DEFAULT_COMMAND

export FZF_ALT_C_OPTS="--preview 'tree -C {} | head -200'"

if uname | grep -q Darwin &> /dev/null; then
  source /opt/homebrew/Cellar/fzf/$(fzf --version | cut -d " " -f 1)/shell/key-bindings.zsh
  source $HOME/.local/share/zinit/plugins/lincheney---fzf-tab-completion/zsh/fzf-zsh-completion.sh
fi

if uname | grep -q Linux &> /dev/null; then
  source /usr/share/fzf/key-bindings.zsh
  source $HOME/.local/share/zinit/plugins/lincheney---fzf-tab-completion/zsh/fzf-zsh-completion.sh
fi

zle     -N            fzf-goto-dir-widget

bindkey -M vicmd '^_' fzf-goto-dir-widget
bindkey -M viins '^_' fzf-goto-dir-widget

bindkey -M viins '^I' fzf_completion
bindkey -M vicmd '^I' fzf_completion

