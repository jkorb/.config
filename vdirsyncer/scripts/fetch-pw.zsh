#! /usr/bin/env zsh

pass login.uu.nl | sed -n 's/^pass: //p'
