#! /usr/bin/env python
"""Get default encoding"""

from __future__ import print_function
import sys

try:
   import locale
   use_locale = True
except ImportError:
   use_locale = False

__all__ = ['default_encoding']

if use_locale:
   # Get the default charset.
   try:
      if sys.version_info[:2] < (3, 11):
         lcAll = locale.getdefaultlocale()
      else:
         lcAll = []
   except locale.Error as err:
      print("WARNING:", err, file=sys.stderr)
      lcAll = []

   if len(lcAll) == 2 and lcAll[0] is not None:
      default_encoding = lcAll[1]
   else:
      try:
         default_encoding = locale.getpreferredencoding()
      except locale.Error as err:
         print("WARNING:", err, file=sys.stderr)
         default_encoding = sys.getdefaultencoding()
else:
   default_encoding = sys.getdefaultencoding()

default_encoding = default_encoding.lower()

if __name__ == "__main__":
   print(default_encoding)
