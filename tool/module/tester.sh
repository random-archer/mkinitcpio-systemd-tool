#!/usr/bin/env bash

set -e

echo "### tester"

verify_local_parms() {

    local param_list=(var_head=1 var_main=2 var_tail=3)
    local param_size="${#param_list[@]}"

    [[ "$param_size" != "0" ]] && local "${param_list[@]}"

    # report local vars
    local

}

verify_local_parms
