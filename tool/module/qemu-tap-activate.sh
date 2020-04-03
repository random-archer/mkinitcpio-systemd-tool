#!/usr/bin/env bash

#
# runs on host
#

set -e

echo "### qemu tap: activate"

sudo ip link add QBRI type bridge

sudo ip tuntap add dev QTAP mode tap

sudo ip link set QTAP master QBRI

sudo ip link set dev QBRI up

sudo ip link set dev QTAP up
