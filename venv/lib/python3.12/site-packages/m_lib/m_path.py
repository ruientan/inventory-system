#! /usr/bin/env python

#
# useful function(s) for manipulating paths
#

from __future__ import print_function

_homedir = None

def get_homedir():
   global _homedir
   if _homedir is None:
      import sys, os
      _homedir = os.path.abspath(os.path.dirname(sys.argv[0]))
   return _homedir


def test():
   print(get_homedir())


if __name__ == "__main__":
   test()
