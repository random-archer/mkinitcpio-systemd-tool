#!/usr/bin/env python

#
# setup basic archux machine
#

from nspawn.setup import *

import os
import sys

# import shared config
project_root = os.popen("git rev-parse --show-toplevel").read().strip()
python_module = f"{project_root}/tool/module"
sys.path.insert(0, python_module)
from arkon_config import image_base_url
from arkon_config import machine_base

# invoke image identity
IMAGE(url=image_base_url)

# container name
MACHINE(name=machine_base)
