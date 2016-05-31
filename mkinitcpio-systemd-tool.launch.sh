#! /bin/bash

# This file is part of https://github.com/random-archer/mkinitcpio-systemd-tool

# build package automation

location=$(cd "$(dirname "${BASH_SOURCE[0]}" )" && pwd)
cd $location

is_root() {
    [[ $(id -u) == 0 ]]
}

do_commit() {
    echo "// do_commit"
    
    git add --all  :/
    git status 

    local message=$(git status --short)
    git commit --message "$message"
                                                
    git push
    
}

do_commit
