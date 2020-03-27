#!/usr/bin/env python

#
# setup cryptsetup machine
#

from nspawn.setup import *

import os
import sys

# import shared config
project_root = os.popen("git rev-parse --show-toplevel").read().strip()
python_module = f"{project_root}/tool/module"
sys.path.insert(0, python_module)
from arkon_config import machine_cryptsetup
from arkon_config import image_cryptsetup_url

# discover network interface
network_face = TOOL.select_interface()

# invoke image identity
IMAGE(url=image_cryptsetup_url)

# container name
MACHINE(name=machine_cryptsetup)

# WITH(
#     MACVLAN=network_face,
#     Capability='all',
# )
