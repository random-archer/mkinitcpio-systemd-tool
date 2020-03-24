#!/usr/bin/env python

#
# build in batch
#

import os
import time

this_dir = os.path.dirname(os.path.abspath(__file__))

image_list = [
    "cryptsetup",
    "dropbear",
    "tinysshd",
]

for image in image_list:
    print(f"build: {image}")
    image_root = f"{this_dir}/{image}"
    os.system(f"{image_root}/build.py")
    os.system(f"{image_root}/setup.py")
    os.system(f"{image_root}/verify.py")
