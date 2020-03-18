#!/bin/bash

# This file is part of https://github.com/random-archer/mkinitcpio-systemd-tool

# provides https://wiki.archlinux.org/index.php/Mkinitcpio#Build_hooks

# mkinitcpio entry point
help() {
    local pkgname="mkinitcpio-systemd-tool"
    local readme="/usr/share/$pkgname/README.md"
    [[ -f "$readme" ]] && cat "$readme" 
}

# mkinitcpio entry point
build() {
    
    quiet "provision initrd systemd units"

    # initramfs inclusion marker
    local tag="ConditionPathExists=/etc/initrd-release"
                
    # user provided system units
    local dir="/etc/systemd/system"
    add_dir $dir
    
    # locate units marked for inclusion into initramfs
    local unit_list=$(2>/dev/null grep -R -l -F "$tag" "$dir"/*)
    [[ $unit_list ]] || error "Missing any units in $dir with entry $tag"

    local unit
    for unit in $unit_list ; do
        add_systemd_unit_X "$unit"
    done
    
}

# safety wrapper for external commands
run_command() {
    local command="$@"
    local result; result=$(2>&1 $command); status=$?
    case "$status" in
         0) quiet "Invoke success: $command\n$result\n"; return 0 ;;
         *) error "Invoke failure ($status): $command \n$result\n" ; return 1 ;;  
    esac
}

# function add_systemd_unit with extra bug fixes for:
# https://bugs.archlinux.org/task/42396
# https://bugs.archlinux.org/task/49458
# https://bugs.archlinux.org/task/49460

# original source:
# https://git.archlinux.org/svntogit/packages.git/tree/trunk/initcpio-install-systemd?h=packages/systemd

add_systemd_unit_X() {
    # Add a systemd unit file to the initcpio image. Hard dependencies on binaries
    # and other unit files will be discovered and added.
    #   $1: path to rules file (or name of rules file)

    local unit= rule= entry= key= value= binary= dep=

    # use simple unit name
    unit=$(basename $1)
    quiet "add systemd unit $unit"
    
    # search in all standard locations
    unit=$(PATH=/etc/systemd/system:/usr/lib/systemd/system:/lib/systemd/system type -P "$unit")
    if [[ -z $unit ]]; then
        # complain about not found unit file
        return 1
    fi

    add_file "$unit"

    while IFS='=' read -r key values; do
        read -ra values <<< "$values"

        case $key in
            Requires|OnFailure)
                # only add hard dependencies (not Wants)
                map add_systemd_unit_X ${values[*]}
                ;;
            Exec*)
                # don't add binaries unless they are required
                if [[ ${values[0]:0:1} != '-' ]]; then
                    local target=
                    target=${values[0]#\!\!} 
                    if [[ -f $BUILDROOT$target ]] ; then
                         quiet "reuse present binary $target"
                    else
                         quiet "provision new binary $target"
                         add_binary "$target"
                    fi
                fi
                ;;
            InitrdBinary)
                # provision binaries
                # format:
                # InitrdBinary=/path/exec [source=/host/exec] [replace=yes] [optional=yes]
                local source= target= args= replace= optional=
                target=${values[0]#\!\!} ; args=${values[@]:1:9}
                [[ $args ]] && local ${args[*]}
                [[ $source ]] || source="$target"
                if [[ -f $BUILDROOT$target ]] ; then
                    if [[ $replace == "yes" ]] ; then 
                        quiet "replace present binary $target"
                        add_binary "$source" "$target"
                    else 
                        quiet "reuse present binary $target"
                    fi
                elif [[ -f $source ]] ; then
                    quiet "provision new binary $target"
                    add_binary "$source" "$target"
                elif [[ $optional = "yes" ]] ; then
                    quiet "skip optional binary $target"
                else
                    error "invalid source binary $source"
                fi
                ;;
            InitrdPath)
                # provision dir/file
                # format:
                # InitrdPath=/path/dir [glob=*.sh] 
                # InitrdPath=/path/file [source=/lib/file]
                # arguments: [mode=755] [create=yes] [replace=yes] [optional=yes]
                local source= target= args= mode= glob= optional= create= replace=
                target=${values[0]} ; args=${values[@]:1:9}
                [[ $args ]] && local ${args[*]}
                [[ $source ]] || source="$target"
                if [[ $replace == "yes" ]] ; then
                    quiet "replace path $target"
                    rm -f -r "$BUILDROOT$target"
                fi                
                if [[ -e $BUILDROOT$target ]] ; then
                    quiet "reuse path $target"
                elif [[ $create == "yes" ]] ; then
                    if [[ ${target: -1} == "/" ]] ; then
                        quiet "create empty dir $target $mode"
                        add_dir "$target" "$mode"
                    else
                        quiet "create empty file $target $mode"
                        source=$(mktemp)
                        add_file "$source" "$target" "$mode"
                        rm -f "$source"
                    fi  
                elif [[ -d $source ]] ; then 
                    quiet "provision new dir $source $glob"
                    add_full_dir "$source" "$glob"
                elif [[ -f $source ]] ; then
                    quiet "provision new file $source -> $target $mode"
                    add_file "$source" "$target" "$mode"
                elif [[ $optional = "yes" ]] ; then
                    quiet "skip optional path $target"
                else
                    error "invalid source path $source"
                fi
                ;;
            InitrdLink)
                # provision symbolic link
                # format:
                # InitrdLink=/link-path /target-path
                local link= target=
                link=${values[0]}
                target=${values[1]}
                if [[ -z $link ]] ; then
                    error "missing link for InitrdLink in unit $unit"
                elif [[ -z $target ]] ; then
                    error "missing target for InitrdLink in unit $unit"
                else
                    quiet "make symbolic link $link -> $target"
                    add_symlink "$link" "$target"
                fi
                ;;
            InitrdBuild)
                # invoke build time function form script file
                # format: 
                # InitrdBuild=/path/script.sh command=function-name 
                local script= command= args= 
                script=${values[0]} ; args=${values[@]:1:9} 
                [[ $args ]] && local ${args[*]}
                if [[ -z $script ]] ; then
                    error "missing InitrdBuild script in unit $unit"
                elif [[ -z $command ]] ; then
                    error "missing command for script $script in unit $unit"
                else
                    quiet "invoke command [$command] for script $script in unit $unit"
                    # use sub shell for safety
                    (source "$script" ; "$command")
                fi
                ;;
            InitrdCall)
                # invoke build time code in-line
                # format: 
                # InitrdCall=bash-code-in-line 
                local code= 
                code=${values[*]}
                if [[ -z $code ]] ; then
                    error "missing InitrdCall code in unit $unit"
                else
                    quiet "call in-line [$code] in unit $unit"
                    # FIXME needs sub shell, but that breaks some of `/usr/lib/initcpio/functions.sh`
                    $code 
                fi
                ;;
            InitrdService)
                # invoke service configuration action
                # format:
                # InitrdService=enable|disable|mask|unmask
                local action= name=
                action=${values[0]}
                name="$(basename $unit)"
                case "$action" in
                    enable|disable|mask|unmask)
                        quiet "apply [$action] for unit [$name]"
                        run_command systemctl --root "$BUILDROOT" "$action" "$name"
                        ;;
                    *)
                        error "invalid InitrdService action: $action"
                        ;;
                esac
                ;; 
            Initrd*)
                error "invalid [X-SystemdTool] directive: $key"
                ;; 
        esac

    done <"$unit"

    # preserve reverse soft dependency
    for dep in {/etc,/usr/lib}/systemd/system/*.wants/${unit##*/}; do
        if [[ -L $dep ]]; then
            add_symlink "$dep"
        fi
    done

    # add hard dependencies
    if [[ -d $unit.requires ]]; then
        for dep in "$unit".requires/*; do
            add_systemd_unit_X ${dep##*/}
        done
    fi
}
