#!/usr/bin/env bash

#
# runs on host
#

#set -e

echo "### qemu tap: deactivate"

sudo ip link set dev QTAP down

sudo ip link set dev QBRI down

sudo ip link del QTAP

sudo ip link del QBRI
