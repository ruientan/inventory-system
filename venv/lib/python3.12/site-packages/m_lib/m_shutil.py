#! /usr/bin/env python
"""
Shell utilities. Additional to shutil.py (standard library module).
"""


from __future__ import print_function
import os


mkhier_error = "m_shutil.mkhier_error"

def mkhier(path): # Python implementation of UNIX' mkdir -p /path/to/dir
   if os.path.isdir(path):
      return # It's Ok to have the directory already created

   if os.path.exists(path):
      raise mkhier_error("`%s' is file" % path)

   list_dirs = path.split(os.sep)
   #print(list_dirs)
   for i in range(0, len(list_dirs)):
      new_path = os.sep.join(list_dirs[0:i+1])
      if (new_path != '') and (not os.path.exists(new_path)):
         #print("Making", new_path)
         os.mkdir(new_path)


def mcd(dir):
   os.mkdir(dir)
   os.chdir(dir)


def test():
   mkhier("I.AM/creating/TEST/dir")

if __name__ == "__main__":
   test()
