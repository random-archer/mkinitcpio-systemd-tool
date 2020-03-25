```diff
- WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING
- WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING
- WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING
```

You will experience problems due to migration of this project form "aur" to "community" repository.

Please track problems/solutions here: https://github.com/random-archer/mkinitcpio-systemd-tool/issues/32

```diff
- WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING
- WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING
- WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING
```

##### This file is part of https://github.com/random-archer/mkinitcpio-systemd-tool

## mkinitcpio-systemd-tool

Never write another mkinitcpio hook again, use systemd-tool.

### Summary 

Provisioning tool for systemd in initramfs (systemd-tool)

mkinitcpio hook name: `systemd-tool`

Core features provided by the hook:
* unified systemd + mkinitcpio configuration
* automatic provisioning of binary and config resources
* on-demand invocation of mkinitcpio scripts and in-line functions 

Features provided by the included service units:
* initrd debugging
* early network setup
* interactive user shell
* remote ssh access in initrd
* cryptsetup + custom password agent 

### Issues

[Useful issues](https://github.com/random-archer/mkinitcpio-systemd-tool/wiki)

### Example

Basic usage steps:

1) activate required hooks in `/etc/mkinitcpio.conf`:
```
HOOKS="base systemd systemd-tool"
```

2) review, change and enable/disable provided default files:
```
[PREFIX]/network/initrd-*.network
[PREFIX]/system/initrd-*.service
[PREFIX]/system/initrd-*.sh
```

3) build/review initrd and reboot
```
mkinitcpio -v -p linux > build.log
lsinitcpio -x /boot/initramfs-linux.img
systemctl reboot
```

### Details

`makepkg/pacman` install actions:
* take a look in [arch repo](https://git.archlinux.org/svntogit/community.git/tree/trunk/PKGBUILD?h=packages/mkinitcpio-systemd-tool) 
  and [make file](https://github.com/random-archer/mkinitcpio-systemd-tool/blob/master/Makefile)
* provision default files included in this package into the `/etc,/usr/lib`
* specific folders are `/etc/mkinitcpio-systemd-tool` and  `[PREFIX]/systemd/system`

`mkinitcpio` install hook actions:
* look for enabled units in the `/etc/systemd/system`
* include in initrd units containing marker `/etc/initrd-release`
* activate transitively in initrd any discovered systemd service units
* auto provision into initramfs resources declared inside initrd service units  

### Provisioning Questions and Answers

what is the mkinitcpio hook entry provided by this package?
* hook name: `systemd-tool`
* required hooks are: `base systemd systemd-tool`
* recommended hooks are: `base autodetect modconf block filesystems keyboard fsck systemd systemd-tool`

how can I customize installed service units?
* follow regular approaches to [editing provided units](https://wiki.archlinux.org/index.php/systemd#Editing_provided_units)
* create service unit override with `systemctl edit $unit_name`
* enable/disable with `systemctl enable $unit_name` / `systemctl disable $unit_name`

how can I review generated `/boot/initramfs-linux.img`?
* to review `initramfs.img` after `mkinitcpio` but before `reboot`, use:
* visually, with [midnight commander](https://www.archlinux.org/packages/community/x86_64/mc/) 
  or scripted, with [mkinitcpio lsinitcpio](https://wiki.archlinux.org/index.php/Mkinitcpio#Extracting_the_image) 

how systemd unit transitive dependency provisioning works?
* see `mkinitcpio-install.sh/add_systemd_unit_X()`
* units found in `[Unit]/Requires|OnFailure` are recursively installed 

what is the purpose of `[X-SystemdTool]` section in service unit files?
* see https://github.com/systemd/systemd/issues/3340
* this section provides configuration interface for `mkinitcpio` provisioning actions
* supported directives: `InitrdPath` `InitrdLink` `InitrdBinary` `InitrdBuild` `InitrdCall`

how can I auto-provision my custom service unit binaries into initramfs?
* use `InitrdBinary=/path/target-exec` to provision service binary
* also will be provisioned all `Exec*` entries such as `ExecStart=/usr/bin/program`

how can I auto-provision my custom service unit resources into initramfs?
* use `InitrdPath=/path/to/host/folder-or-file`

how can I relocate folder during provisioning?
* not implemented, source and target folder must use the same location

how can I relocate file and/or change file mode during provisioning?
* use `InitrdPath=/target-file source=/source-file mode=NNN` 

how can I filter directory content during provisioning?
* use `InitrdPath=/target-folder glob=*.example` 

how can I provision optional folder or file?
* use `InitrdPath=/target-file source=/source-file optional=yes`

is there a way to create empty folder or file?
* for empty dir, use `InitrdPath=/path/target-dir/ create=yes` note trailing SLASH
* for empty file, use `InitrdPath=/path/target-file create=yes` note NO trailing slash

how can I provision a symbolic link?
* use `InitrdLink=/path-to-link/link-name /path-to-target/target-name`
* note that `/path-to-target/target-name` must be provisioned separately

can I invoke a provisioning script related to my service during mkinitcpio build time?
* use `InitrdBuild=/path-to/script.sh command=function_name` 

can I call a little provisioning script snippet during mkinitcpio build time?
* check for available `mkinitcpio` functions in `/usr/lib/initcpio/functions.sh`
* use `InitrdCall=inline-bash-code-here` to call these functions 

how can I provide custom interactive user shell for ssh client
* change sample shell file located in `/etc/systemd/system/initrd-shell.sh`  

which ssh user keys are used by initramfs sshd server(s)?
* they come from host `/root/.ssh/authorized_keys`

### Shell Script Questions and Answers

there is a `initrd-shell.sh` script provided, what does it do?
* it is used as both interactive login shell and as a systemd service 
* when crypto disks are present, it acts as password agent
* when in ssh console, it offers simple interactive menu
* when in systemd service mode, it acts as service 

how can I review `initrd-shell.sh` actions during last boot?
* use `journalctl -b -t shell`

what does `CTRL-C` do to `initrd-shell.sh` in different modes?
* `initrd-shell.sh` provides appropriate reaction to interrupt, depending on the context
* while in `ssh` terminal password agent prompt, it will start a menu form `initrd-shell.sh`
* while in `/dev/tty` local debug console, it will exit from `initrd-shell.sh` 
* while in `/dev/console` password agent prompt, it will restart the `initrd-shell.sh` service

is there a silent or no-echo mode during password entry in `initrd-shell.sh`?
* there are two ways to enter silent mode (see `systemd-ask-password.c`):
* either by pressing `BACKSPACE` as first key or by pressing `TAB` at any time
* then the prompt will show extra text: `(no echo)`  
