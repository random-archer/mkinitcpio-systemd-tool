#!/usr/bin/env python

#
# setup tinysshd machine
#

from nspawn.setup import *

import os
import sys

# import shared config
project_root = os.popen("git rev-parse --show-toplevel").read().strip()
python_module = f"{project_root}/tool/module"
sys.path.insert(0, python_module)
from arkon_config import tinysshd_machine
from arkon_config import tinysshd_image_url

# invoke image identity
IMAGE(url=tinysshd_image_url)

# container name
MACHINE(name=tinysshd_machine)
