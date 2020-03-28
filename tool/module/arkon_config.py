#
# shared config for build/setup/verify
#

import os
import time
import pathlib
import difflib
import threading

from dataclasses import dataclass
from datetime import datetime
from nspawn import CONFIG

# location of this module
this_dir = os.path.dirname(os.path.abspath(__file__))

# arch linux base iso image date
build_epoch = datetime(year=2020, month=3, day=1)

# discover project root
project_root = os.popen("git rev-parse --show-toplevel").read().strip()

# azure or local resource location
user_home = os.getenv('HOME', "/tmp/systemd-tool")

# location of source repository
project_repo = os.getenv('BUILD_SOURCESDIRECTORY', project_root)

# location of disk mount shared between host and machine
project_boot = f"{project_repo}/boot"

# location of transient images produced by this tool
image_store = f"/var/lib/nspawn_systemd_tool"


# detect build system
def has_ci_azure():
    return "AZURE_EXTENSION_DIR" in os.environ


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

    def boot_folder_clear(self):
        print(f"### reset boot folder")
        os.system(f"sudo rm -rf {project_boot}/*")

    def boot_folder_report(self):
        print(f"### review boot folder")
        os.system(f"ls -las {project_boot}")

    def produce_initrd(self):
        print(f"### produce machine initrd")
        self.run(f"/usr/bin/mkinitcpio -p linux")

    def extract_initrd(self):
        print(f"### extract machine initrd")
        self.run(f"/usr/bin/bash -c 'cd /repo/boot; lsinitcpio -x /boot/initramfs-linux.img' ")

    def produce_boot_result(self) -> None:
        "produce boot image extract on the host"
        self.report_machine()
        self.produce_initrd()
        self.boot_folder_clear()
        self.extract_initrd()
        self.boot_folder_report()

    def assert_has_link(self, path:str) -> None:
        print(f"### assert link present: {path}")
        full_path = f"{project_boot}/{path}"
        assert pathlib.Path(full_path).is_symlink(), f"no link: {full_path}"

    def assert_has_path(self, path:str) -> None:
        print(f"### assert path present: {path}")
        full_path = f"{project_boot}/{path}"
        assert pathlib.Path(full_path).exists(), f"no path: {full_path}"

    def assert_has_text(self, path:str) -> None:
        print(f"### assert text matches: {path}")
        boot_path = f"{project_boot}/{path}"
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

    # TODO
    # https://wiki.archlinux.org/index.php/systemd-nspawn#Run_docker_in_systemd-nspawn
    # https://www.freedesktop.org/software/systemd/man/systemd.exec.html#System%20Call%20Filtering
    # https://github.com/systemd/systemd/blob/master/units/systemd-nspawn%40.service.in
    def booter_initiate(self) -> None:
        print(f"### initrd image: activate")
        proc_cmdline = (
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
#             f"--capability=all "
#             f"--private-users=false "
            f"--bind=/dev/pts "
            f"--bind=/dev/char "
            f"--bind=/dev/disk "
            f"--bind=/dev/block "
            f"--bind=/dev/mapper "
            f"--bind=/dev/loop-control "
#             f"--system-call-filter='@mount @keyring @privileged' "
            #
            f"-E TERM=xterm "
            f"-E SYSTEMD_COLORS=0 "  # suppress colors
            f"-E SYSTEMD_IN_INITRD=1 "  # imitate initramfs
            f"-E SYSTEMD_PROC_CMDLINE='{proc_cmdline}' "  # imitate kernel command line
            f"-D {project_boot} "  # image folder
            f"-M {self.booter_machine} "  # container name
            f"/init "  # init is systemd
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

    def booter_terminate(self) -> None:
        print()
        print(f"### initrd image: deactivate")
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
