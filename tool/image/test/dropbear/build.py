#!/usr/bin/env python

#
# build dropbear image
#

from nspawn.build import *

import os
import sys

# import shared config
project_root = os.popen("git rev-parse --show-toplevel").read().strip()
python_module = f"{project_root}/tool/module"
sys.path.insert(0, python_module)
from arkon_config import image_base_url
from arkon_config import image_dropbear_url

# declare image identity
IMAGE(url=image_dropbear_url)

# provision dependency image
PULL(url=image_base_url)

# copy local resources
COPY(path="/etc")

# regenerate host keys as pem
# dopbear convert fails on non-pem keys
SH("ssh-keygen -A -m PEM")

# publish image
PUSH()
