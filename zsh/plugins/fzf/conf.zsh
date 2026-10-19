source "$XDG_CONFIG_HOME/zsh/plugins/fzf/options.zsh"

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
