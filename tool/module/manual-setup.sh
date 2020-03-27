#!/usr/bin/env bash

#
# runs inside machine
#

set -e

echo "### install::backup"

cp -v -f -r /etc/mkinitcpio-systemd-tool/. /etc/mkinitcpio-systemd-tool.bak/

echo "### install::install"

cd /repo
make PREFIX=/usr install

echo "### install::restore"

cp -v -f -r /etc/mkinitcpio-systemd-tool.bak/. /etc/mkinitcpio-systemd-tool/
