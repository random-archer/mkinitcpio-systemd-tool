#!/usr/bin/env python

#
# build basic archux image
#

from nspawn.build import *

import os
import sys

# import shared config
project_root = os.popen("git rev-parse --show-toplevel").read().strip()
python_module = f"{project_root}/tool/module"
sys.path.insert(0, python_module)
from arkon_config import build_epoch
from arkon_config import image_base_url
from arkon_config import project_repo
from arkon_config import project_boot
from arkon_config import project_data

version_path = TOOL.date_path(build_epoch)
version_dots = TOOL.date_dots(build_epoch)
version_dash = TOOL.date_dash(build_epoch)

# pacman setup params
archux_url = "https://archive.archlinux.org"
booter_url = f"{archux_url}/iso/{version_dots}/archlinux-bootstrap-{version_dots}-x86_64.tar.gz"
mirror_url = f"{archux_url}/repos/{version_path}/$repo/os/$arch"

# declare image identity
IMAGE(url=image_base_url)

# provision dependency image
PULL(url=booter_url)

# configure container profile
WITH(
    Boot="yes",  # auto-find image init program
    Quiet="yes",  # suppress "press to escape" message
    KeepUnit="yes",  # use service unit as nspawn scope
    Register="yes",  # expose service unit with machinectl
)

# copy local resources
COPY(path="/etc")
COPY(path="/root")

# template local resources
CAST(path="/etc/pacman.d/mirrorlist", mirror_url=mirror_url)

# activate proxy tls
SH("update-ca-trust")

# ensure gpg keys
SH(script="pacman-key --init")
SH(script="pacman-key --populate")

# update database
SH("pacman --sync --refresh")

# install packages
SH("pacman --sync --needed --noconfirm "
   # developer support
   "mc "
   "htop "
   "xterm "
   "strace "
   # provide host sshd keys
   "openssh "
   # build/install deps
   "sed "
   "grep "
   "make "
   # core package deps
   "linux "
   "mkinitcpio "
   # initrd-dropbear.service
   "dropbear "
   # initrd-tinysshd.service
   "busybox "
   "tinyssh "
   "tinyssh-convert "
   # initrd-cryptsetup.service
   "cryptsetup "
)

# enable services
SH("systemctl enable "
   "systemd-networkd "
   "systemd-resolved "
   "sshd "
)

# impose code repo
WITH(Bind=f"{project_repo}:/repo/")

# expose boot dir
WITH(Bind=f"{project_boot}/:/repo/boot/")

# expose data dir
WITH(Bind=f"{project_data}/:/repo/data/")

# publish image
PUSH()
