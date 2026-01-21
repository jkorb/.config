fpath+=/opt/homebrew/share/zsh/site-functions
fpath+=$ZDOTDIR/autoloads
autoload -Uz $ZDOTDIR/autoloads/*

export ZCOREDIR=$ZDOTDIR/core
export ZTHEMEDIR=$ZDOTDIR/theme
export ZPLUGINDIR=$ZDOTDIR/plugins

source "$ZCOREDIR/core.zsh"
source "$ZPLUGINDIR/plugins.zsh"
