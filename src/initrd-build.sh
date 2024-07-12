# This file is part of https://github.com/random-archer/mkinitcpio-systemd-tool

# mkinitcpio build time functions for X-SystemdTool/InitrdBuild
# can use mkinitcpio /usr/lib/initcpio/functions.sh, for example :
#   $BUILDROOT - mkinitcpio image build destination dir
#   quiet() - output to console, depending on mkinitcpio "-v" option
#   plain() - output to console, always

# load configuration file
source /etc/mkinitcpio-systemd-tool/mkinitcpio-systemd-tool.conf

# enforce specific login shell in /etc/passwd
do_root_shell() {
    local shell="/bin/sh"
    local search="(root):([^:]*):([^:]*):([^:]*):([^:]*):([^:]*):([^:]*)"
    local replace="\1:\2:\3:\4:\5:\6:${shell}"
    local target="$BUILDROOT/etc/passwd"
    run_command sed -i -r -e "s|${search}|${replace}|" "$target"
}

# remove optional entries form /etc/{group,passwd,shadow} 
do_secret_clean() {
    local core=("root" "systemd-.*")
    local udev=("tty" "uucp" "kmem" "input" "video" "audio" "lp" "disk" "optical" "storage")
    local all_users=("${core[@]}" "${udev[@]}" "${preserve_additional_accounts[@]}")
    local user_regex
    for user in "${all_users[@]}" ; do
	user_regex+="|^${user}:.*"
    done
    # Delete the leading |
    user_regex="${user_regex:1:${#user_regex}}"
    local target
    for target in $BUILDROOT/etc/{group,passwd,shadow} ; do
	run_command sed -i -r -e "/${user_regex}/!d" "${target}"
    done
}

# re-enable root login via password for initramfs only
do_root_login_enable() {
    run_command sed -i -r -e 's/(^root:)!(.*)/\1\2/' $BUILDROOT/etc/shadow
}

# ensure dropbear server host keys
do_dropbear_keys() {

    quiet "provide host server ssh keys"

    mkdir -p "/etc/dropbear"
    
    local keytype_list="rsa ecdsa"
    local keytype= source= target=
    for keytype in $keytype_list ; do
        source=$(keypath_openssh   "$keytype")
        target=$(keypath_dropbear  "$keytype")
        if [[ -f "$target" ]] ; then
            quiet "use existing dropbear host key: $target"
        else
            if [[ -f "$source" ]] ; then
                plain "convert openssh to dropbear host key: $target"
                run_command   dropbearconvert openssh dropbear "$source" "$target"
            else
                plain "generate brand new dropbear host key: $target"
                run_command   dropbearkey -t "$keytype" -f "$target"
            fi
        fi
    done

}

# ensure tinyssh server host keys
do_tinysshd_keys() {
	
    quiet "provide host server ssh keys"
    
    local keydir=/etc/tinyssh/sshkeydir
    local open_ssh_key=/etc/ssh/ssh_host_ed25519_key
    
    if [[ $openssh_key_convert == "true"  ]]; then
        if ! [[ -f  "$open_ssh_key" ]]; then
            plain "OpenSSH key not found in $open_ssh_key"
            plain "Aborting OpenSSH key conversion"  
            return
        fi

        if [[ -d "$keydir" ]]; then
            plain "remove existing $keydir"
            rm -rf "$keydir"
        fi
    
        plain "convert openssh to tinysshd host key ed25519"
    
        run_command tinyssh-convert $keydir < $open_ssh_key	
        chmod go-rwx "$keydir"
    else 
        plain "converting openssh keys disabled!"
    fi

}

# location of server host keys used by openssh
keypath_openssh() {
    local type=$1
    echo "/etc/ssh/ssh_host_${type}_key"
}

# location of server host keys used by dropbear
keypath_dropbear() {
    local type="$1"
    echo "/etc/dropbear/dropbear_${type}_host_key"
}

# safety wrapper for external commands
run_command() {
    local command="$@"
    local result ; result=$(2>&1 $command) ; status=$?
    case "$status" in
         0) quiet "command success: $command\n$result\n" ; return 0 ;;
         *) error "command failure ($status): $command \n$result\n" ; return 1 ;;  
    esac
}

do_secret_clean
