
### nspawn privileged 

cannot create a device node inside systemd-nspawn containers
https://github.com/kinvolk/kube-spawn/issues/324

https://github.com/systemd/systemd/commit/4f086aab52812472a24c9b8b627589880a38696e

```
[Unit]
Description=Container %i
Documentation=man:systemd-nspawn(1)
PartOf=machines.target
Before=machines.target
After=network.target systemd-resolved.service
RequiresMountsFor=/var/lib/machines

[Service]
ExecStart=/home/dpark/Dev/systemd/build/systemd-nspawn --capability=cap_audit_control,cap_audit_read,cap_audit_write,cap_audit_control,cap_block_suspend,cap_chown,cap_dac_override,cap_dac_read_search,cap_fowner,cap_fsetid,cap_ipc_lock,cap_ipc_owner,cap_kill,cap_lease,cap_linux_immutable,cap_mac_admin,cap_mac_override,cap_mknod,cap_net_admin,cap_net_bind_service,cap_net_broadcast,cap_net_raw,cap_setgid,cap_setfcap,cap_setpcap,cap_setuid,cap_sys_admin,cap_sys_boot,cap_sys_chroot,cap_sys_module,cap_sys_nice,cap_sys_pacct,cap_sys_ptrace,cap_sys_rawio,cap_sys_resource,cap_sys_time,cap_sys_tty_config,cap_syslog,cap_wake_alarm --bind=/sys/fs/cgroup --bind-ro=/boot --bind-ro=/lib/modules --boot --notify-ready=yes --keep-unit --machine=mknodtest --directory=/srv/fc29
KillMode=mixed
Type=notify
RestartForceExitStatus=133
SuccessExitStatus=133
WatchdogSec=3min
Slice=machine.slice
Delegate=yes
TasksMax=16384
Environment=SYSTEMD_NSPAWN_API_VFS_WRITABLE=1 SYSTEMD_NSPAWN_USE_CGNS=0

# Enforce a strict device policy, similar to the one nspawn configures when it
# allocates its own scope unit. Make sure to keep these policies in sync if you
# change them!
DevicePolicy=closed
DeviceAllow=/dev/net/tun rwm
DeviceAllow=char-pts rw

# nspawn itself needs access to /dev/loop-control and /dev/loop, to implement
# the --image= option. Add these here, too.
DeviceAllow=/dev/loop-control rw
DeviceAllow=block-loop rw
DeviceAllow=block-blkext rw

# nspawn can set up LUKS encrypted loopback files, in which case it needs
# access to /dev/mapper/control and the block devices /dev/mapper/*.
DeviceAllow=/dev/mapper/control rw
DeviceAllow=block-device-mapper rw

## mknod test inside systemd-nspawn
DeviceAllow=/dev/port rwm

[Install]
WantedBy=machines.target
```
