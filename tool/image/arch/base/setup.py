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
from arkon_config import base_image_url
from arkon_config import base_machine

# invoke image identity
IMAGE(url=base_image_url)

# container name
MACHINE(name=base_machine)
