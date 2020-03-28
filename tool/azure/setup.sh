#!/usr/bin/env bash

set -e

#
# prepare azure environment
#

echo "### ubuntu refresh"
sudo apt-get -y update

#echo "### setup qemu"
sudo apt-get -y install qemu-system-x86 cpu-checker

#echo "### report qemu/kvm"
sudo kvm-ok || true

echo "### setup systemd"
sudo apt-get -y install attr pigz systemd-container

echo "### setup python"
pip install nspawn tox

echo "### report home"
echo $HOME

echo "### report work"
echo $(pwd)

echo "### report uname"
uname -a

echo "### report ip addr"
ip addr

echo "### report python"
python --version

echo "### report file-attr"
getfattr --dump /home

echo "### report systemd"
systemctl --version

echo "### report container"
systemd-detect-virt
