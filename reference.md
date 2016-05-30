#### This file is part of https://github.com/random-archer/mkinitcpio-systemd-tool

### password agent ask file format

file location `/run/systemd/ask-password`

name pattern `ask.TNdKGj` and `sck.50eaa4fca00c5cbc`

content

```
[Ask]
PID=181
Socket=/run/systemd/ask-password/sck.50eaa4fca00c5cbc
AcceptCached=1
Echo=0
NotAfter=0
Message=Please enter passphrase for disk VBOX_HARDDISK (root)!
Icon=drive-harddisk
Id=cryptsetup:/dev/block/8:3
```

### password agent specification and implementation

https://www.freedesktop.org/wiki/Software/systemd/PasswordAgents/

https://www.freedesktop.org/software/systemd/man/systemd-ask-password.html

https://github.com/systemd/systemd/blob/master/src/shared/ask-password-api.h

https://github.com/systemd/systemd/blob/master/src/ask-password/ask-password.c

https://github.com/systemd/systemd/blob/master/src/reply-password/reply-password.c

https://www.freedesktop.org/software/systemd/man/systemd-tty-ask-password-agent.html

### enable / disable net device with busybox

#### required to recover from emergency service
ExecStart=/bin/sh -c "echo '%N: enalbe network devices'"
ExecStart=/bin/sh -c "for dev in $(ls /sys/class/net) ; do iplink set "$dev" up   ; done"
#### required for interface renaming after root switch
ExecStop=/bin/sh -c  "echo '%N: disable network devices'"
ExecStop=/bin/sh -c  "for dev in $(ls /sys/class/net) ; do iplink set "$dev" down ; done"

### verify rules in /usr/lib/udev/rules.d/80-net-setup-link.rules

udevadm test-builtin path_id /sys/class/net/eth0
```
calling: test-builtin
hwdb.bin does not exist, please run udevadm hwdb --update
Load module index
timestamp of '/etc/systemd/network' changed
Created link configuration context.
ID_PATH=pci-0000:00:03.0
ID_PATH_TAG=pci-0000_00_03_0
Unload module index
Unloaded link configuration context.
```

udevadm test-builtin net_setup_link /sys/class/net/eth0
```
calling: test-builtin
hwdb.bin does not exist, please run udevadm hwdb --update
Load module index
timestamp of '/etc/systemd/network' changed
Created link configuration context.
ID_NET_DRIVER=e1000
No matching link configuration found.
Unload module index
Unloaded link configuration context.
```
 
udevadm info -e | grep eth0
```
P: /devices/pci0000:00/0000:00:03.0/net/eth0
E: DEVPATH=/devices/pci0000:00/0000:00:03.0/net/eth0
E: INTERFACE=eth0
E: SYSTEMD_ALIAS=/sys/subsystem/net/devices/eth0
```
