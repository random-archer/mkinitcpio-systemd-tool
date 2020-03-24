#!/usr/bin/env python

#
# TODO produce sysroot disk for cryptsetup
#

import os
import time

this_dir = os.path.dirname(os.path.abspath(__file__))

loop_path = f"/dev/loop7"
file_path = f"{this_dir}/sysroot.disk"

disk_guid = "00000000-feed-face-0000-added0facade"
disk_link = f"/dev/disk/by-uuid/{disk_guid}"
disk_size = 128  # MB

mapper_name = "booter_root"
mapper_path = f"/dev/mapper/{mapper_name}"

entry_list = [
    f"sudo modprobe loop",
    f"sudo cryptsetup luksClose {mapper_name}",
    f"sudo rm {disk_link}",
    f"sudo losetup -d {loop_path}",
    f"sudo dd if=/dev/zero of={file_path} bs=1M  count={disk_size}",
    f"sudo losetup {loop_path} {file_path}",
    f"sudo losetup",
#     f"sudo ln -s {loop_path} {disk_link}",
    f"printf test | sudo cryptsetup luksFormat --iter-time 100 --uuid {disk_guid} {loop_path}",
#     f"sudo cryptsetup luksDump {loop_path}",
    f"printf test | sudo cryptsetup luksOpen {loop_path} {mapper_name}",
    f"sudo mkfs.ext4 {mapper_path}",
    f"sudo cryptsetup luksClose {mapper_name}",
]

for entry in entry_list:
    print(f"### {entry}")
    time_start = time.time()
    os.system(entry)
    time_finish = time.time()
    time_diff = (time_finish - time_start)
    print(f"--- @ {time_diff:.2f} sec")
