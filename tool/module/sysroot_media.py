#!/usr/bin/env python

#
# produce cryptsetup sysroot disk(s)
# these disk(s) are mounted as /sysroot inside initramfs container
#
# note:
# * using azure cache, update `azure.yml/.../cache_version` when changing this file

import os
import time

from arkon_config import host_user
from arkon_config import media_store


class SimpleSysroot:
    "basic luks root"

    # loop device needed for disk build
    loop_path = f"/dev/loop7"

    # uuid for external/plain filesystem
    ext4_guid = "00000000-feed-face-1111-added1facade"

    # uuid for internal/encrypted filesystem
    luks_guid = "00000000-feed-face-0000-added0facade"

    # location of luks disk device
    luks_link = f"/dev/disk/by-uuid/{luks_guid}"

    # location of luks disk file
    disk_path = f"{media_store}/simple-sysroot.disk"

    # fixed luks disk device file size
    disk_size = 128  # MB

    # cryptsetup password
    disk_pass = "test"

    # cryptestup mapper name
    mapper_name = "booter_root"

    # cryptsetup mapper location
    mapper_path = f"/dev/mapper/{mapper_name}"

    # luks root disk build comman sequence
    command_list = [
        # ensure /dev/loop support
        f"sudo modprobe loop",
        # ensure disk is not in use
        f"sudo cryptsetup luksClose {mapper_name}",
        f"sudo rm {luks_link}",
        f"sudo losetup -d {loop_path}",
        # produce disk and mappers
        f"sudo mkdir -p {media_store} ",
        f"sudo dd if=/dev/zero of={disk_path} bs=1M  count={disk_size}",
        f"sudo chown {host_user}:{host_user} {disk_path}",
        f"sudo losetup {loop_path} {disk_path}",
        f"sudo losetup",
        f"sudo ln -s {loop_path} {luks_link}",
        f"printf {disk_pass} | sudo cryptsetup luksFormat --iter-time 1 --uuid {luks_guid} {loop_path}",
        f"sudo cryptsetup luksDump {loop_path}",
        f"printf {disk_pass} | sudo cryptsetup luksOpen {loop_path} {mapper_name}",
        f"sudo mkfs.ext4 -U {ext4_guid} {mapper_path}",
        # populate image content
        # TODO
        # release crypto mapper
        f"sudo cryptsetup luksClose {mapper_name}",
    ]

    def remove_media(self) -> None:
        print(f"### remove luks root:")

        if os.path.exists(self.disk_path):
            os.system(f"sudo rm -f {self.disk_path}")

    def produce_media(self) -> None:
        print(f"### produce luks root:")

        if os.path.exists(self.disk_path):
            print(f"### sysroot media present: reuse")
            return
        else:
            print(f"### sysroot media missing: build")

        for command in self.command_list:
            print(f"### {command}")
            time_start = time.time()
            os.system(command)
            time_finish = time.time()
            time_diff = (time_finish - time_start)
            print(f"--- @ {time_diff:.2f} sec")


# rebuild sysroot disk file manually
if __name__ == "__main__":
    sysroot = SimpleSysroot()
    sysroot.remove_media()
    sysroot.produce_media()
