#!/usr/bin/env bash

#
# runs inside machine
#

set -e

source="/repo"
target="/tmp/repo"

rm -r -f $target

mkdir -p $target

cp -f -a $source/. $target

chown -R nobody  $target

cd $target

sudo -u nobody makepkg -e

pacman --noconfirm -U *.pkg.tar.xz
