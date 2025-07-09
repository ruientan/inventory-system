#! /usr/bin/env python
"""File logger"""


from time import *


class FLog:
   def __init__(self, f, overwrite = 0, timeformat = "%a %d %b %Y %T"):
      if type(f) == type(''): # If f is string - use it as file's name
         if overwrite:
            mode = 'w'
         else:
            mode = 'a'
         self.outfile = open(f, mode)
      else:
         self.outfile = f     # else assume it is opened file (fileobject) or
                              # "compatible" object (must has write() method)
      self.f = f
      self.timeformat = timeformat


   def __del__(self):
      self.close()


   def close(self):
      if type(self.f) == type(''): # If f was opened - close it
         self.outfile.close()


   def log(self, str):
      self.outfile.write("%s %s\n" % (strftime(self.timeformat, localtime(time())), str))


   __call__ = log


   def flush(self):
      self.outfile.flush()


def makelog(f):
   return FLog(f, 1)


def openlog(f):
   return FLog(f)


def test():
   log = makelog("test.log")
   log.log("Log opened")
   log("Log closed")
   log.close()

if __name__ == "__main__":
   test()
