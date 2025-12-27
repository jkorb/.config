#! /usr/env bash

yay -Syu
zinit self-update && zinit update
$XDG_CONFIG_HOME/tmux/plugins/tpm/bin/update_plugins all
