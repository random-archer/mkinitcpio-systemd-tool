#!/usr/bin/env bash

set -e

#
# verify scripts
#

repo_src="$BUILD_SOURCESDIRECTORY"/src

echo "### script list"
ls -las "$repo_src"/*.sh

echo "### shell check"
shellcheck "$repo_src"/initrd-shell.sh
