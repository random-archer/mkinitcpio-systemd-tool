#!/usr/bin/env python

#
# build in batch for manual testing before commit
#

import os
import time

this_dir = os.path.dirname(os.path.abspath(__file__))

image_list = [
    "cryptsetup",
    "dropbear",
    "tinysshd",
    "unitada",
]

for image in image_list:
    print(f"@@@ build: {image}")
    image_base = f"{this_dir}/{image}"
    command_list = [
        (f"{image_base}/build.py", 1),
        (f"{image_base}/setup.py", 1),
        (f"{image_base}/verify.py", 1),
    ]
    for command, settle_time in command_list:
        print(f"@@@ command: {command}")
        result = os.system(command)
        assert result == 0, f"failure: {command}"
        time.sleep(settle_time)

print(f"@@@ finish")
