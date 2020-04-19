#!/usr/bin/env bash

#
# Developer support: allow local install
#

set -e

this_repo=$(dirname "$0")

# manual package build and install steps:
cd "$this_repo"
rm -r -f  pkg/ *.pkg.tar.xz
makepkg -e
sudo pacman -U *.pkg.tar.xz --noconfirm
