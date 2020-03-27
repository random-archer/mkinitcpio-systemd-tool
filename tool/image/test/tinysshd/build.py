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
from arkon_config import image_base_url
from arkon_config import image_tinysshd_url

# declare image identity
IMAGE(url=image_tinysshd_url)

# provision dependency image
PULL(url=image_base_url)

# copy local resources
COPY(path="/etc")

# publish image
PUSH()
