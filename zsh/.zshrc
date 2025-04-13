export ZCOREDIR=$ZDOTDIR/core
export ZTHEMEDIR=$ZDOTDIR/theme
export ZPLUGINDIR=$ZDOTDIR/plugins

source "$ZCOREDIR/core.zsh"
# source "$ZTHEMEDIR/theme.zsh"
source "$ZPLUGINDIR/plugins.zsh"

if uname | grep -q Darwin &> /dev/null; then
  PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"
  path+=("/Library/Tex/texbin")
fi

