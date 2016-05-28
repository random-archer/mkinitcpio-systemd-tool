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
