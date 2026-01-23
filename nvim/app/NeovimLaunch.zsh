#!/bin/zsh

PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin

exec /opt/homebrew/bin/alacritty -e /bin/zsh -lc "nvim --listen $HOME/.cache/nvim/nvim-neovim-app.sock"

