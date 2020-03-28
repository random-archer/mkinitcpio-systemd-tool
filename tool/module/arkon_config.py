#
# shared config for build/setup/verify cycle
#

import os
import time
import shutil
import pathlib
import difflib
import threading

from datetime import datetime
from dataclasses import dataclass

from nspawn import CONFIG

from produce_media import produce_sysroot

# location of this module
this_dir = os.path.dirname(os.path.abspath(__file__))

# arch linux base iso image date
build_epoch = datetime(year=2020, month=3, day=1)

# discover project root
project_root = os.popen("git rev-parse --show-toplevel").read().strip()

# current user account
host_user = os.getenv('USER', "root")

# azure or local resource location
user_home = os.getenv('HOME', "/root")

# location of source repository
project_repo = os.getenv('BUILD_SOURCESDIRECTORY', project_root)

# location of disk mount shared between host and machine
project_boot = f"{project_repo}/boot"

# location of disk mount shared between host and machine
project_data = f"{project_repo}/data"

# location of machine resources
nspawn_store = CONFIG['storage']["root"]

# location of transient images produced by this tool
image_store = f"{nspawn_store}/systemd_tool"

# system path
linux_kernel = f"/boot/vmlinuz-linux"

# system path
linux_initrd = f"/boot/initramfs-linux.img"

# quemu manager
qemu_command = "qemu-system-x86_64"
qemu_kernel = f"{project_root}{linux_kernel}"
qemu_initrd = f"{project_root}{linux_initrd}"
qemu_sysroot = f"{project_root}/tool/module/sysroot.disk"
qemu_monitor_addr = "127.0.0.1"
qemu_monitor_port = "51234"


# detect build system
def has_ci_azure():
    return "AZURE_EXTENSION_DIR" in os.environ


# detect quemu manager
def has_ci_qemu():
    return shutil.which(qemu_command) is not None


# detect quemu/kvm support
def has_ci_qemu_kernel():
    return os.path.exists("/dev/kvm")


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
class Machine:
    "container operator"

    machine:str  # container name
    image_root:str  # absolute path to resource folder

    def __post_init__(self):
        if has_ci_azure():
            print(f"### settle machine state")
            time.sleep(3)

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

    def install_tool(self) -> None:
        print(f"### install systemd-tool")
        self.run(f"/repo/tool/module/manual-setup.sh")

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
        self.initrd_image_produce()
        self.share_folder_clear()
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

    # FIXME barely works
    # https://wiki.archlinux.org/index.php/systemd-nspawn#Run_docker_in_systemd-nspawn
    # https://www.freedesktop.org/software/systemd/man/systemd.exec.html#System%20Call%20Filtering
    # https://github.com/systemd/systemd/blob/master/units/systemd-nspawn%40.service.in
    def booter_sysd_initiate(self) -> None:
        self.booter_sysd_prepare()
        print(f"### initrd image: sysd: activate")
        proc_cmdline = (
            f"TERM=xterm "
#             "systemd.log_level=debug "
#             "systemd.log_target=console "
#             "systemd.journald.forward_to_console=1 "
        )
        command = (
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
            f"-M {self.booter_machine} "  # container name
            f"/init "  # /init is /usr/lib/systemd/systemd
        )
        print(f"{command}")

        def booter_task() -> None:
            try:
                print(f"### booter start  : {self.booter_machine}")
                os.system(command)
            finally:
                print(f"### booter finish : {self.booter_machine}")

        booter_thread = threading.Thread(target=booter_task)
        booter_thread.setDaemon(True)
        booter_thread.start()

    def booter_sysd_terminate(self) -> None:
        print()
        print(f"### initrd image: sysd: deactivate")
        command = (
            f"sudo SYSTEMD_COLORS=0 "
            f"machinectl terminate {self.booter_machine} "
        )
        os.system(command)

    # FIXME "Failed to create bus connection: Protocol error"
    def booter_report_generator(self) -> None:
        print(f"### report generated units")
        self.booter_run(f"/usr/lib/systemd/system-generators/systemd-cryptsetup-generator")
        self.booter_run(f"/usr/lib/systemd/system-generators/systemd-fstab-generator")
        time.sleep(1)
        self.booter_run(f"/usr/bin/ls -las /run/systemd/generator")

    # keyboard terminate: CTRL+]]]
    def booter_qemu_action(self, action:str) -> None:
        print(f"### initrd image: action: {action}")
        command = (
            f"printf '{action}\n' | telnet {self.qemu_monitor_addr} {self.qemu_monitor_port} "
        )
        print(command)
        os.system(command)

    def booter_qemu_initiate(self) -> None:
        if not has_ci_qemu():
            return
        print()
        produce_sysroot()
        print(f"### initrd image: qemu: activate")
        #
        os.system(f"sudo killall qemu-system-x86_64")
        #
        qemu_cpu_mode = f"-cpu host -enable-kvm " if has_ci_qemu_kernel() else ""
        command = (
            f"sudo "
            f"{qemu_command} "
            f"{qemu_cpu_mode} "
            f"-runas {host_user} "
            f"-kernel {qemu_kernel} "
            f"-initrd {qemu_initrd} "
            f"-m 512 -smp 2 "
            f"-drive if=virtio,cache=none,format=raw,file={qemu_sysroot} "
            f"-append 'edd=off console=ttyS0 TERM=xterm SYSTEMD_COLORS=0' "
            f"-nographic -serial mon:stdio "
            f"-monitor telnet:{qemu_monitor_addr}:{qemu_monitor_port},server,nowait "
        )
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

    # keyboard terminate: CTRL+A then X
    def booter_qemu_terminate(self) -> None:
        if not has_ci_qemu():
            return
        print()
        print(f"### initrd image: qemu: deactivate")
#         self.booter_qemu_action("quit")
        os.system(f"sudo killall qemu-system-x86_64")


# no proxy in azure
if has_ci_azure():
    CONFIG['proxy']['use_host_proxy'] = 'no'
    CONFIG['proxy']['use_machine_proxy'] = 'no'

#
# base image
#
machine_base = "arch-base"
image_base_path = f"{image_store}/{machine_base}/default.tar.gz"
image_base_url = f"file://localhost/{image_base_path}"

#
# verify cryptsetup
#
machine_cryptsetup = "test-cryptsetup"
image_cryptsetup_path = f"{image_store}/{machine_cryptsetup}/default.tar.gz"
image_cryptsetup_url = f"file://localhost/{image_cryptsetup_path}"

#
# verify dropbear
#
machine_dropbear = "test-dropbear"
image_dropbear_path = f"{image_store}/{machine_dropbear}/default.tar.gz"
image_dropbear_url = f"file://localhost/{image_dropbear_path}"

#
# verify tinysshd
#
machine_tinysshd = "test-tinysshd"
image_tinysshd_path = f"{image_store}/{machine_tinysshd}/default.tar.gz"
image_tinysshd_url = f"file://localhost/{image_tinysshd_path}"

#
# verify anything else
#
machine_unitada = "test-unitada"
image_unitada_path = f"{image_store}/{machine_unitada}/default.tar.gz"
image_unitada_url = f"file://localhost/{image_unitada_path}"
