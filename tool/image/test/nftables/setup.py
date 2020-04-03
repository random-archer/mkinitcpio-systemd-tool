#!/usr/bin/env python

#
# setup nftables machine
#

from nspawn.setup import *

import os
import sys

# import shared config
project_root = os.popen("git rev-parse --show-toplevel").read().strip()
python_module = f"{project_root}/tool/module"
sys.path.insert(0, python_module)
from arkon_config import nftables_machine
from arkon_config import nftables_image_url

# invoke image identity
IMAGE(url=nftables_image_url)

# container name
MACHINE(name=nftables_machine)

# configure machine ssh access
WITH(BindReadOnly="/root/.ssh/authorized_keys")
