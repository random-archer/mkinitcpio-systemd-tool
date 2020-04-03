#!/usr/bin/env python

#
# build nftables image
#

from nspawn.build import *

import os
import sys

# import shared config
project_root = os.popen("git rev-parse --show-toplevel").read().strip()
python_module = f"{project_root}/tool/module"
sys.path.insert(0, python_module)
from arkon_config import base_image_url
from arkon_config import nftables_image_url

# declare image identity
IMAGE(url=nftables_image_url)

# provision dependency image
PULL(url=base_image_url)

# copy local resources
COPY("/etc")

# install packages
SH("pacman --sync --needed --noconfirm "
   "nftables "
)

# publish image
PUSH()
