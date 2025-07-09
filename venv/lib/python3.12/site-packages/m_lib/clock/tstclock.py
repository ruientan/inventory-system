#! /usr/bin/env python
"""Define clock() for systems that do not have it"""

from __future__ import print_function
from clock import clock
from time import sleep

print("Testing...")
sleep(3)
print("Clock:", clock())
