#!/usr/bin/env python

#
# produce sysroot disk for cryptsetup
#

# TODO populate sysroot

import os
import time

host_user = os.environ['USER']

this_dir = os.path.dirname(os.path.abspath(__file__))

loop_path = f"/dev/loop7"
file_path = f"{this_dir}/sysroot.disk"

luks_guid = "00000000-feed-face-0000-added0facade"
disk_link = f"/dev/disk/by-uuid/{luks_guid}"
disk_size = 128  # MB

disk_pass = "test"

mapper_name = "booter_root"
mapper_path = f"/dev/mapper/{mapper_name}"

sysroot_step_list = [
    f"sudo modprobe loop",
    f"sudo cryptsetup luksClose {mapper_name}",
    f"sudo rm {disk_link}",
    f"sudo losetup -d {loop_path}",
    f"sudo dd if=/dev/zero of={file_path} bs=1M  count={disk_size}",
    f"sudo chown {host_user}:{host_user} {file_path}",
    f"sudo losetup {loop_path} {file_path}",
    f"sudo losetup",
#     f"sudo ln -s {loop_path} {disk_link}",
    f"printf {disk_pass} | sudo cryptsetup luksFormat --iter-time 1 --uuid {luks_guid} {loop_path}",
#     f"sudo cryptsetup luksDump {loop_path}",
    f"printf {disk_pass} | sudo cryptsetup luksOpen {loop_path} {mapper_name}",
    f"sudo mkfs.ext4 {mapper_path}",
    # TODO populate image
    f"sudo cryptsetup luksClose {mapper_name}",
#     f"sudo losetup -d {loop_path}",
]


def produce_sysroot():
    print(f"### produce sysroot with luks")

    for command in sysroot_step_list:
        print(f"### {command}")
        time_start = time.time()
        os.system(command)
        time_finish = time.time()
        time_diff = (time_finish - time_start)
        print(f"--- @ {time_diff:.2f} sec")


if __name__ == "__main__":
    produce_sysroot()
