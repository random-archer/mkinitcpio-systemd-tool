#!/usr/bin/env bash

# This file is part of https://github.com/random-archer/mkinitcpio-systemd-tool

# Provides https://wiki.archlinux.org/index.php/Mkinitcpio#Build_hooks

# Using shell linter: https://github.com/koalaman/shellcheck
# shellcheck shell=bash

# mkinitcpio entry point
help() {
    local pkgname="mkinitcpio-systemd-tool"
    local readme_file="/usr/share/$pkgname/README.md"
    [[ -f "$readme_file" ]] && cat "$readme_file"
}

# mkinitcpio entry point
build() {
    #
    # systemd service unit selection logic:
    #
    # 1. "proper" symlinks in /etc/systemd/system
    # mostly represent aliased/enabled service units;
    # therefore look for links in that folder tree
    #
    # 2. /etc/initrd-release marker is required
    # for most initramfs service units;
    # therefore apply that filter always
    #
    # 3. collect only from second-level folders
    # links placed in /unit.wants/, /unit.requires/, etc;
    # therefore select only enabled units
    #

    quiet "provisioning initrd systemd units"

    # marker for inclusion into initramfs
    local marker="ConditionPathExists=/etc/initrd-release"

    # location of user-enabled service units links
    local folder="/etc/systemd/system"
    # note: non-recursive
    add_dir "$folder"

    # locate units marked for inclusion into initramfs
    # -R : find files recursive, including symlinks
    # -l : print the name of each input file when matching content
    # -F : interpret PATTERN as a list of fixed strings, not as regex
    # -x : select only those matches that match the whole line
    # -m : stop reading a file after NUM matching lines
    # /*/: search second level folders, i.e. /unit.wants/ /unit.requires/, etc.
    local unit_list=""
    unit_list=$(2>/dev/null grep -R -l -F -x -m1 "$marker" "$folder"/*/)
    [[ "$unit_list" ]] || warning "Missing enabled units in $folder with entry $marker"

    # process service unit candidates
    local unit_task=""
    for unit_task in $unit_list ; do
        if [[ -L "$unit_task" ]] ; then
            # found a symlink, i.e. enabled service unit
            add_systemd_unit_X "$unit_task"
        fi
    done

}

# concatenate units and their potential drop-in files
# we do this manually, as in a chroot `systemctl cat` will not work
plain_unit_concat() {
    local unit_name="$1"
    local unit_content=""
    local service_path=""
    local override_path=""
    # add the top-most service
    for service_path in {/usr/lib,/etc}/systemd/system ; do
        if [[ -f "${service_path}/${unit_name}" ]] ; then
          unit_content=""
          unit_content+="# ${service_path}/${unit_name}\n"
          unit_content+="$(cat "${service_path}/${unit_name}")\n\n"
        fi
    done
    # add any existing drop-in file for the unit
    for service_path in {/usr/lib,/etc}/systemd/system ; do
        if [[ -d "${service_path}/${unit_name}.d" ]] ; then
            for override_path in "${service_path}/${unit_name}.d/"*.conf ; do
                if [[ -f "$override_path" ]] ; then
                    unit_content+="# ${override_path}\n"
                    unit_content+="$(cat "${override_path}")\n\n"
                fi
            done
        fi
    done
    echo -e "$unit_content"
}

# detect if running inside chroot
# https://www.freedesktop.org/software/systemd/man/systemd-detect-virt.html
# -r, --chroot : Return value indicates whether the process was invoked in a chroot() environment or not
has_virt_chroot() {
    local result=""
    result=$(systemd-detect-virt --chroot 2>/dev/null)
    return $?
}

# detect if running inside container that supports `systemctl cat`
# https://www.freedesktop.org/software/systemd/man/systemd-detect-virt.html
# -c, --container : Only detects container virtualization
has_virt_support() {
    local result=""
    result=$(systemd-detect-virt --container 2>/dev/null)
    case "$result" in
        none) return 0 ;;
        systemd-nspawn) return 0 ;;
        *) return 1 ;;
    esac
}

# detect if environment provides working `systemctl cat`
has_virt_systemctl_cat() {
    ! has_virt_chroot && has_virt_support
}

# use `systemctl cat` only in proper environment,
# otherwise, fall back to own concatenation implementation
smart_unit_concat() {
    local unit_name="$1"
    if has_virt_systemctl_cat ; then
        systemctl cat "$unit_name" 2>/dev/null
    else
        plain_unit_concat "$unit_name"
    fi
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
    #   $1: service unit candidate: either symlink to a unit or a real unit file

    local unit_task="" unit_name="" unit_path="" unit_target="" symlink_name=""

    # absolute path to the unit candidate
    unit_task="$1"

    # Extract the basename of the symlink. This may be an instanciated service
    # with an argument, e.g. my-fancy-tool@my-arg.service.
    symlink_name=$(basename "$unit_task")
    # Extract the name of the service template, e.g. my-fancy-tool@my-arg.service
    # becomes my-fancy-tool@.service.
    unit_name=$(sed 's/@.\+\./@\./g' <<< "$symlink_name")

    quiet "processing systemd unit $unit_name"

    # resolve unit task into absolute service unit path, returns first match
    unit_path=$(PATH=/etc/systemd/system:/usr/lib/systemd/system type -P "$unit_name")
    if [[ -z "$unit_path" ]] ; then
        error "can not find service unit: %s" "$unit_name"
        return 1
    else
        quiet "resolved service unit path: %s" "$unit_path"
    fi

    # generated result unit file inside initramfs
    unit_target="$BUILDROOT$unit_path"
    if [[ -e "$unit_target" ]] ; then
      plain "replacing initramfs unit file: %s" "$unit_path"
    else
      quiet "producing initramfs unit file: %s" "$unit_path"
    fi

    # concatenate unit with overrides into a single unit file inside initramfs
    smart_unit_concat "$unit_name" | install -Dm644 /dev/stdin "$unit_target"

    # process configuration directives provided by the service unit
    # https://www.freedesktop.org/software/systemd/man/systemd.unit.html#%5BUnit%5D%20Section%20Options
    local directive="" entry_list=""
    while IFS='=' read -r directive entry_list ; do

        # produce entry array
        read -ra entry_list <<< "$entry_list"

        # extract leading scalar parameter
        local param_head="${entry_list[0]}"

        # extract trailing 'key=value' parameter array
        local param_list=("${entry_list[@]:1}")

        # trailing parameter array length
        local param_size="${#param_list[@]}"

        case "$directive" in
            Requires|OnFailure|Unit|InitrdUnit)
                # only add hard dependencies (not wants)
                # from [section] / directive:
                # [Unit] / Requires=
                # [Unit] / OnFailure=
                # [Path] / Unit=
                # [X-SystemdTool] / InitrdUnit= provision units as is
                map add_systemd_unit_X "${entry_list[@]}"
                ;;
            Exec*)
                # skip empty values (overrides), add only required binaries
                # format:
                # ExecStart=/path/prog [...]
                # ExecStart=-/path/prog [...]
                # ExecStart=!/path/prog [...]
                # ExecStart=!!/path/prog [...]
                local target=""
                if [[ -n "${param_head}" && ${param_head:0:1} != '-' ]] ; then
                    target="${param_head#\!\!}"
                    if [[ -f "$BUILDROOT$target" ]] ; then
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
                local source="" target="" replace="" optional=""
                [[ "$param_size" != "0" ]] && local "${param_list[@]}"
                target="${param_head#\!\!}"
                [[ -n "$source" ]] || source="$target"
                if [[ -f "$BUILDROOT$target" ]] ; then
                    if [[ "$replace" == "yes" ]] ; then
                        quiet "replace present binary $target"
                        add_binary "$source" "$target"
                    else
                        quiet "reuse present binary $target"
                    fi
                elif [[ -f "$source" ]] ; then
                    quiet "provision new binary $target"
                    add_binary "$source" "$target"
                elif [[ "$optional" == "yes" ]] ; then
                    quiet "skip optional binary $target"
                else
                    error "invalid source binary $source"
                    return 1
                fi
                ;;
            InitrdPath)
                # provision dir/file
                # format:
                # InitrdPath=/path/dir [glob=*.sh]
                # InitrdPath=/path/file [source=/lib/file]
                # arguments: [mode=755] [create=yes] [replace=yes] [optional=yes]
                local source="" target="" mode="" glob="" optional="" create="" replace=""
                [[ "$param_size" != "0" ]] && local "${param_list[@]}"
                target="${param_head}"
                [[ -n "$source" ]] || source="$target"
                if [[ "$replace" == "yes" ]] ; then
                    quiet "replace path $target"
                    rm -f -r "$BUILDROOT$target"
                fi
                if [[ -e "$BUILDROOT$target" ]] ; then
                    quiet "reuse path $target"
                elif [[ "$create" == "yes" ]] ; then
                    if [[ "${target: -1}" == "/" ]] ; then
                        quiet "create empty dir $target $mode"
                        add_dir "$target" "$mode"
                    else
                        quiet "create empty file $target $mode"
                        source=$(mktemp)
                        add_file "$source" "$target" "$mode"
                        rm -f "$source"
                    fi
                elif [[ -d "$source" ]] ; then
                    quiet "provision new dir $source $glob"
                    add_full_dir "$source" "$glob"
                elif [[ -f "$source" ]] ; then
                    quiet "provision new file $source -> $target $mode"
                    add_file "$source" "$target" "$mode"
                elif [[ "$optional" == "yes" ]] ; then
                    quiet "skip optional path $target"
                else
                    error "invalid source path $source"
                    return 1
                fi
                ;;
            InitrdLink)
                # provision symbolic link
                # format:
                # InitrdLink=/link-path target=/target-path
                local link="" target=""
                [[ "$param_size" != "0" ]] && local "${param_list[@]}"
                link="${param_head}"
                if [[ -z "$link" ]] ; then
                    error "missing link for InitrdLink in unit $unit_path"
                    return 1
                elif [[ -z "$target" ]] ; then
                    error "missing target for InitrdLink in unit $unit_path"
                    return 1
                else
                    quiet "make symbolic link $link -> $target"
                    add_symlink "$link" "$target"
                fi
                ;;
            InitrdBuild)
                # invoke build time function form script file
                # format:
                # InitrdBuild=/path/script.sh command=function-name
                local script="" command=""
                [[ "$param_size" != "0" ]] && local "${param_list[@]}"
                script="${param_head}"
                if [[ -z "$script" ]] ; then
                    error "missing InitrdBuild script in unit $unit_path"
                    return 1
                elif [[ -z "$command" ]] ; then
                    error "missing command for script $script in unit $unit_path"
                    return 1
                else
                    quiet "invoke command [$command] for script $script in unit $unit_path"
                    # use sub shell for safety
                    # shellcheck disable=SC1090 # Can't follow non-constant source
                    (source "$script" ; "$command")
                fi
                ;;
            InitrdCall)
                # invoke build time code in-line
                # format:
                # InitrdCall=bash-code-in-line
                local inline_code=("${entry_list[@]}")
                if [[ -z "${inline_code[*]}" ]] ; then
                    error "missing InitrdCall code in unit $unit_path"
                    return 1
                else
                    quiet "call in-line [${inline_code[*]}] in unit $unit_path"
                    # FIXME needs sub shell, but that breaks some of `/usr/lib/initcpio/functions.sh`
                    "${inline_code[@]}"
                fi
                ;;
            Initrd*)
                error "invalid [X-SystemdTool] directive: $directive"
                return 1
                ;;
        esac

    done < "$unit_target"

    # handle external-to-unit, i.e. folder-based "Forward" and "Reverse" dependencies:
    # https://www.freedesktop.org/software/systemd/man/systemd.unit.html#Mapping%20of%20unit%20properties%20to%20their%20inverses

    # preserve "Forward" dependency configured from "this_unit.requires/" into "other_unit":
    local unit_forward=""
    if [[ -d "$unit_path".requires ]] ; then
        for unit_forward in "$unit_path".requires/* ; do
            add_systemd_unit_X "${unit_forward##*/}"
        done
    fi

    # preserve "Reverse" dependency configured from "this_unit" into "other_unit", after enable:
    # this_unit/[Install]/WantedBy=  other_unit   -> enable ->   /other.unit.wants/   this_unit
    # this_unit/[Install]/RequiredBy=other_unit   -> enable ->   /other.unit.requires/this_unit
    local unit_reverse=""
    for unit_reverse in {/etc,/usr/lib}/systemd/system/*{.wants,.requires}/"$symlink_name" ; do
        if [[ -L "$unit_reverse" ]] ; then
            add_symlink "$unit_reverse"
        fi
    done

}
