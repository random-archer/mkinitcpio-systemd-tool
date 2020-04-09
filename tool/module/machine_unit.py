#!/usr/bin/env python

#
# provide host/guest conatainer manager
#

import os
import abc
import time
import shutil
import pathlib
import difflib
import threading
from dataclasses import dataclass

from arkon_config import host_user
from arkon_config import has_ci_azure
from arkon_config import project_repo
from arkon_config import project_boot
from arkon_config import project_data

from sysroot_media import SimpleSysroot

# well known system path
linux_kernel = f"/boot/vmlinuz-linux"

# well known system path
linux_initrd = f"/boot/initramfs-linux.img"

# location of this file
this_dir = os.path.dirname(os.path.abspath(__file__))


class HostAny(abc.ABC):
    "conatainer manager prototype"

    def __init__(self, guest_name:str, sysroot_path:str) -> None:
        self.guest_name = guest_name
        self.sysroot_path = sysroot_path

    @abc.abstractmethod
    def command_initiate(self) -> str:
        "start guest instance"

    @abc.abstractmethod
    def command_terminate(self) -> str:
        "finish guest instance"


# FIXME barely usable
# https://wiki.archlinux.org/index.php/systemd-nspawn#Run_docker_in_systemd-nspawn
# https://www.freedesktop.org/software/systemd/man/systemd.exec.html#System%20Call%20Filtering
# https://github.com/systemd/systemd/blob/master/units/systemd-nspawn%40.service.in
class HostSYSD(HostAny):
    "systemd-nspawn container host"

    def command_initiate(self) -> str:
        proc_cmdline = (
            f"TERM=xterm "
#             "systemd.log_level=debug "
#             "systemd.log_target=console "
#             "systemd.journald.forward_to_console=1 "
        )
        return (
            f"sudo "
            #
            # elevate privilege
            f"SYSTEMD_NSPAWN_LOCK=0 "
            f"SYSTEMD_NSPAWN_USE_CGNS=0 "
            f"SYSTEMD_NSPAWN_API_VFS_WRITABLE=1 "
            #
            f"systemd-nspawn "
            #
            # elevate privilege
            f"--capability=CAP_MKNOD "
            f"--system-call-filter='@mount @keyring @privileged' "
            #
            f"--bind=/dev/disk "
            f"--bind=/dev/block "
            f"--bind=/dev/mapper "
            f"--bind=/dev/loop-control "
            f"--bind=/dev/loop7 "  # sysroot.disk
            #
            f"--property='DevicePolicy=auto' "
            f"--property='DeviceAllow=/dev/loop-control rw' "
            f"--property='DeviceAllow=block-loop rw' "
            f"--property='DeviceAllow=block-blkext rw' "
            f"--property='DeviceAllow=/dev/mapper/control rw' "
            f"--property='DeviceAllow=block-device-mapper rw' "
            #
            f"-E SYSTEMD_COLORS=0 "  # suppress colors
            f"-E SYSTEMD_IN_INITRD=1 "  # imitate initramfs
            f"-E SYSTEMD_PROC_CMDLINE='{proc_cmdline}' "  # imitate kernel command line
            f"-D {project_data} "  # image folder
            f"-M {self.guest_name} "  # container name
            f"/init "  # /init is /usr/lib/systemd/systemd
        )

    def command_terminate(self) -> str:
        return (
            f"sudo SYSTEMD_COLORS=0 "
            f"machinectl terminate {self.guest_name} "
        )


# note: ensure virtio drivers are present in the guest
class HostQEMU(HostAny):
    "quemu container host"

    command = "qemu-system-x86_64"
    kernel = f"{project_repo}{linux_kernel}"
    initrd = f"{project_repo}{linux_initrd}"
    link_addr = "52:54:12:34:56:78"
    monitor_addr = "127.0.0.1"
    monitor_port = "51234"

    def has_manager(self) -> bool:
        "detect quemu manager present"
        return shutil.which(self.command) is not None

    def has_kernel_kvm(self) -> bool:
        "detect kernel has kvm support"
        return os.path.exists("/dev/kvm")

    def command_action(self, action:str) -> str:
        return (
            f"printf '{action}\n' | telnet {self.qemu_monitor_addr} {self.qemu_monitor_port} "
        )

    def command_initiate(self) -> str:
        qemu_cpu_mode = f"-cpu host -enable-kvm " if self.has_kernel_kvm() else ""
        return (
            f"sudo "
            f"{self.command} "
            f"{qemu_cpu_mode} "
            f"-name {self.guest_name} "
            f"-runas {host_user} "
            f"-kernel {self.kernel} "
            f"-initrd {self.initrd} "
            f"-m 512 -smp 2 "

            f"-device e1000,netdev=net0,mac={self.link_addr} "
            f"-netdev user,id=net0,net=192.168.123.0/24,hostfwd=tcp::22022-:22 "

# TODO
#             f"-device virtio-net,netdev=net1 "
#             f"-netdev tap,id=net1,ifname=QTAP,script=no,downscript=no "

            f"-drive if=virtio,cache=none,format=raw,file={self.sysroot_path} "
            f"-append 'edd=off console=ttyS0 TERM=xterm SYSTEMD_COLORS=0' "
            f"-nographic -serial mon:stdio "
            f"-monitor telnet:{self.monitor_addr}:{self.monitor_port},server,nowait "
        )

    def command_terminate(self) -> str:
        # FIXME use self.guest_name
        return f"sudo killall {self.command}"


class Support:

    service_path_list_udev = [
        "/etc/systemd/system/systemd-udevd.service",
        "/etc/systemd/system/systemd-udevd-control.socket",
        "/etc/systemd/system/systemd-udevd-kernel.socket",
    ]

    @classmethod
    def service_mask(cls, service_path:str) -> None:
        print(f"### service: prohibit {service_path}")
        os.system(f"sudo ln -s /dev/null {project_data}/{service_path}")

    @classmethod
    def service_mask_list(cls, service_path_list:list) -> None:
        for service_path in service_path_list:
            cls.service_mask(service_path)


@dataclass
class MachineUnit:
    "container host/guest operator"

    machine:str  # container name
    image_root:str  # absolute path to resource folder

    def __post_init__(self):
        if has_ci_azure():
            print(f"### settle machine state")
            time.sleep(3)
        self.sysroot = SimpleSysroot()
        self.host_qemu = HostQEMU(self.booter_machine, self.sysroot.disk_path)
        self.host_sysd = HostSYSD(self.booter_machine, self.sysroot.disk_path)

    @property
    def test_base(self) -> str:
        "location of test resources"
        return f"{self.image_root}/test_base"

    # https://www.freedesktop.org/software/systemd/man/systemd-run.html
    def run(self, command:str, machine:str=None) -> None:
        "invoke command inside machine"
        if machine is None:
            machine = self.machine
        invoke = f"sudo systemd-run --wait -G -P -M {machine} {command}"
        result = os.system(invoke)
        assert result == 0, f"result: {result}, command: {command}"

    def report_machine(self) -> None:
        print(f"### report active machines")
        os.system(f"sudo machinectl --all --full")

    def install_this_tool(self) -> None:
        print(f"### install systemd-tool")
        self.run(f"/repo/tool/module/manual-install.sh")

    def service_enable(self, service:str) -> None:
        print(f"### service enable : {service}")
        self.run(f"/usr/bin/systemctl enable {service}")

    def service_disable(self, service:str) -> None:
        print(f"### service disable: {service}")
        self.run(f"/usr/bin/systemctl disable {service}")

    def service_mask(self, service:str) -> None:
        print(f"### service mask  : {service}")
        self.run(f"/usr/bin/systemctl mask {service}")

    def service_unmask(self, service:str) -> None:
        print(f"### service unmask: {service}")
        self.run(f"/usr/bin/systemctl unmask {service}")

    def service_enable_list(self, service_list:list) -> None:
        for service in service_list:
            self.service_enable(service)

    def service_disable_list(self, service_list:list) -> None:
        for service in service_list:
            self.service_disable(service)

    def share_folder_clear(self):
        print(f"### share folder clear")
        os.system(f"sudo rm -rf {project_boot}/*")
        os.system(f"sudo rm -rf {project_data}/*")

    def share_folder_review(self):
        print(f"### share folder review")
        os.system(f"ls -las {project_boot}")
        os.system(f"ls -las {project_data}")

    def initrd_image_produce(self):
        print(f"### produce machine initrd")
        self.run(f"/usr/bin/mkinitcpio -p linux")

    def initrd_image_extract(self):
        print(f"### extract machine initrd")
        self.run(f"/usr/bin/cp -f {linux_kernel} {linux_initrd} /repo/boot/")
        self.run(f"/usr/bin/bash -c 'cd /repo/data; lsinitcpio -x {linux_initrd}' ")
        os.system(f"sudo chown -R {host_user}:{host_user} {project_boot} ")
        os.system(f"sudo chown -R {host_user}:{host_user} {project_data} ")

    def perform_make_boot(self) -> None:
        "produce boot image extract on the host"
        self.report_machine()
        self.share_folder_clear()
        self.initrd_image_produce()
        self.initrd_image_extract()
        self.share_folder_review()

    def assert_has_link(self, path:str) -> None:
        print(f"### assert link present: {path}")
        full_path = f"{project_data}/{path}"
        assert pathlib.Path(full_path).is_symlink(), f"no link: {full_path}"

    def assert_has_path(self, path:str) -> None:
        print(f"### assert path present: {path}")
        full_path = f"{project_data}/{path}"
        assert pathlib.Path(full_path).exists(), f"no path: {full_path}"

    def assert_has_text(self, path:str) -> None:
        print(f"### assert text matches: {path}")
        boot_path = f"{project_data}/{path}"
        test_path = f"{self.test_base}/{path}"
        boot_list = pathlib.Path(boot_path).read_text().split("\n")
        test_list = pathlib.Path(test_path).read_text().split("\n")
        diff_list = difflib.unified_diff(test_list, boot_list, lineterm='')
        diff_text = "\n".join(diff_list)
        assert boot_list == test_list, f"no match:\n{diff_text}\n"

    def assert_has_link_list(self, path_list:list) -> None:
        for path in path_list:
            self.assert_has_link(path)

    def assert_has_path_list(self, path_list:list) -> None:
        for path in path_list:
            self.assert_has_path(path)

    def assert_has_text_list(self, path_list:list) -> None:
        for path in path_list:
            self.assert_has_text(path)

    @property
    def booter_machine(self) -> str:
        "name of boot container instance"
        return f"{self.machine}-boot"

    def booter_run(self, command:str) -> None:
        "invoke command inside booter"
        self.run(command, self.booter_machine)

    def booter_disable_udev(self) -> None:
        print(f"### booter: disable udev")
        Support.service_mask_list(Support.service_path_list_udev)

    def booter_ensure_loop(self):
        print(f"### booter: ensure loop")
        os.system("sudo modprobe loop")
        os.system("sudo losetup")

    def booter_sysd_prepare(self):
        print(f"### booter: sysd: prepare")
        self.booter_ensure_loop()
        self.booter_disable_udev()

    def booter_initiate_thread(self, command:str) -> None:
        "start process in parallel"
        print(command)

        def booter_task() -> None:
            try:
                print(f"### booter start  : {self.booter_machine}")
                os.system(command)
            finally:
                print(f"### booter finish : {self.booter_machine}")

        booter_thread = threading.Thread(target=booter_task)
        booter_thread.setDaemon(True)
        booter_thread.start()

    def booter_sysd_initiate(self) -> None:
        self.booter_sysd_prepare()
        print(f"### initrd image: sysd: activate")
        command = self.host_sysd.command_initiate()
        self.booter_initiate_thread(command)

    # mavual stop: keyboard terminate: CTRL+]]]
    def booter_sysd_terminate(self) -> None:
        print()
        print(f"### initrd image: sysd: deactivate")
        command = self.host_sysd.command_terminate()
        os.system(command)

    # FIXME "Failed to create bus connection: Protocol error"
    def booter_report_generator(self) -> None:
        print(f"### report generated units")
        self.booter_run(f"/usr/lib/systemd/system-generators/systemd-cryptsetup-generator")
        self.booter_run(f"/usr/lib/systemd/system-generators/systemd-fstab-generator")
        time.sleep(1)
        self.booter_run(f"/usr/bin/ls -las /run/systemd/generator")

    def booter_qemu_action(self, action:str) -> None:
        print(f"### initrd image: action: {action}")
        command = self.host_qemu.command_action(action)
        print(command)
        os.system(command)

    def booter_qemu_initiate(self) -> None:
        if not self.host_qemu.has_manager():
            return
        print()
        self.sysroot.produce_media()
        print(f"### initrd image: qemu: activate")
# TODO
#         os.system(f"{this_dir}/qemu-tap-activate.sh")
        command = self.host_qemu.command_initiate()
        self.booter_initiate_thread(command)

    # manual stop: keyboard terminate: CTRL+A then X
    def booter_qemu_terminate(self) -> None:
        if not self.host_qemu.has_manager():
            return
        print()
        print(f"### initrd image: qemu: deactivate")
        command = self.host_qemu.command_terminate()
        os.system(command)
# TODO
#         os.system(f"{this_dir}/qemu-tap-deactivate.sh")
