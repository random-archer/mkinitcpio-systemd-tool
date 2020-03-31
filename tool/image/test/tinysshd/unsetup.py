#!/usr/bin/env python

#
# terminate machine
#

import os
import sys
import time

this_dir = os.path.dirname(os.path.abspath(__file__))

command = f"{this_dir}/setup.py --action desure"

os.system(command)
