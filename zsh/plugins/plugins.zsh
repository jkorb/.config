export ZINIT_HOME=$ZDOTDIR/zinit

if [[ ! -f $ZINIT_HOME/zinit.zsh ]]; then
  echo "Installing zdharma-continuum/zinit."
  git clone https://github.com/zdharma-continuum/zinit.git "$ZINIT_HOME"
fi

source $ZDOTDIR/zinit/zinit.zsh

zinit load zsh-users/zsh-syntax-highlighting

zinit ice wait lucid atload="zicompinit; zicdreplay" blockf 
zinit load zsh-users/zsh-completions

zinit ice wait lucid 
zinit load lincheney/fzf-tab-completion

zinit ice wait lucid atload="!_zsh_autosuggest_start" 
zinit load zsh-users/zsh-autosuggestions

zinit ice wait lucid
zinit load zsh-users/zsh-history-substring-search 

zinit ice wait lucid
zinit load hlissner/zsh-autopair 

zinit ice compile'(pure|async).zsh' pick'async.zsh' src'pure.zsh'
zinit light sindresorhus/pure

for conf in $ZPLUGINDIR/*/conf.zsh; do

  source "$conf"

done
