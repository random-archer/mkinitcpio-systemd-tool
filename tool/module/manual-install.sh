#!/usr/bin/env bash

#
# runs inside machine, imitates:
#
# pacman -S mkinitcpio-systemd-tool
#

set -e

echo "### manual-install.sh::backup"

cp -f -r /etc/mkinitcpio-systemd-tool/. /etc/mkinitcpio-systemd-tool.bak/

echo "### manual-install.sh::install"

# code repository bind
cd /repo

# conde install from repository
make PREFIX=/usr install

echo "### manual-install.sh::restore"

cp -f -r /etc/mkinitcpio-systemd-tool.bak/. /etc/mkinitcpio-systemd-tool/
