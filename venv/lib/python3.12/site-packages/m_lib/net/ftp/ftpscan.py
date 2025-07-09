#! /usr/bin/env python
"""Recursive FTP scanners"""


from __future__ import print_function
import codecs
import ftplib
import sys
from .ftpparse import ftpparse


class FtpScanError(Exception): pass
ftpscan_error_mark = object() # error marker


class GetFiles:
   def __init__(self):
      self.entries = []

   def __call__(self, line):
      entry = ftpparse(line)
      if entry:
         self.entries.append(entry)

   def filter(self, file_type):
      return filter(lambda e, file_type=file_type: e.file_type == file_type,
         self.entries)

   def files(self):
      return self.filter('f')

   def directories(self):
      return filter(lambda e: e.name not in (".", ".."), self.filter('d'))


class ReconnectingFTPCallWrapper:
   retries = 10 # retries per function call

   def __init__(self, wrapper, func):
      self.wrapper = wrapper
      self.func = func

   def __call__(self, *params, **kw):
      wrapper = self.wrapper
      func = self.func

      for retry in range(self.retries):
         try:
            return func(*params, **kw)
         except EOFError:
            pass

         ftp_dir = wrapper._ftp_dir
         wrapper._tree.append((ftpscan_error_mark, "Connection reset by peer at directory `%s'. Reconnecting..." % ftp_dir))

         ftp = wrapper._ftp
         ftp.close()

         ftp.connect(wrapper._ftp_server, wrapper._ftp_port)
         ftp.login(wrapper._login, wrapper._password)
         ftp.cwd(ftp_dir)

class ReconnectingFTPWrapper:
   ReconnectingFTPCallWrapperClass = ReconnectingFTPCallWrapper

   def __init__(self, ftp, ftp_server, ftp_port=0, login=None, password=None, ftp_dir='/', tree=None):
      self._ftp = ftp
      self._ftp_server = ftp_server
      self._ftp_port = ftp_port
      self._login = login
      self._password = password
      ftp_dir = [''] + [name for name in ftp_dir.split('/') if name] # remove double slashes //
      self._ftp_dir = '/'.join(ftp_dir)
      self._tree = tree

   def cwd(self, new_cwd, do_ftp=True):
      ftp_dir = self._ftp_dir.split('/')
      if new_cwd == "..":
         del ftp_dir[-1]
      else:
         ftp_dir.append(new_cwd)
      self._ftp_dir = '/'.join(ftp_dir)
      if do_ftp: self._wrap(self._ftp.cwd)(new_cwd)

   def __getattr__(self, attr):
      value = getattr(self._ftp, attr)
      if callable(value):
         return self._wrap(value)
      return value

   def _wrap(self, func):
      return self.ReconnectingFTPCallWrapperClass(self, func)


def _traverse_ftp(ftp, tree, ftp_dir):
   get_files = GetFiles()
   try:
      ftp.dir(get_files)
   except ftplib.all_errors as msg:
      tree.append((ftpscan_error_mark, "Cannot list directory `%s': %s" % (ftp_dir, msg)))
      return
   files = get_files.files()
   directories = get_files.directories()

   if ftp_dir and ftp_dir[-1] == '/':
      ftp_dir = ftp_dir[:-1] # Prevent paths to contain double slashes //

   tree.append((ftp_dir, files))

   for d in directories:
      name = d.name
      full_path = ftp_dir + '/' + name
      try:
         ftp.cwd(name)
      except ftplib.error_perm as msg:
         tree.append((ftpscan_error_mark, "Cannot enter directory `%s': %s" % (full_path, msg)))
         if isinstance(ftp, ReconnectingFTPWrapper):
            ftp.cwd("..", False)
      except ftplib.all_errors as msg:
         tree.append((ftpscan_error_mark, "Cannot enter directory `%s': %s" % (full_path, msg)))
      else:
         _traverse_ftp(ftp, tree, full_path)
         ftp.cwd("..")


def ftpscan1(ftp_server, ftp_port=0, login=None, password=None,
      ftp_dir='/', passive=None, FTPClass=ftplib.FTP, reconnect=False,
      ReconnectingFTPWrapperClass=ReconnectingFTPWrapper):
   """Recursive FTP scan using one-by-one directory traversing. It is slow
   but robust - it works with all but very broken FTP servers.
   """
   tree = []
   ftp = FTPClass()
   if passive is not None:
      ftp.set_pasv(passive)
   if reconnect:
      ftp = ReconnectingFTPWrapperClass(ftp, ftp_server, ftp_port, login, password, ftp_dir, tree)
   ftp.connect(ftp_server, ftp_port)
   ftp.login(login, password)
   if ftp_dir != '/':
      ftp.cwd(ftp_dir)

   _traverse_ftp(ftp, tree, ftp_dir)
   ftp.quit()

   return tree


def ftpscanrecursive(ftp_server, ftp_port=0, login=None, password=None,
      ftp_dir='/', passive=None, FTPClass=ftplib.FTP, reconnect=False):
   """
   Recursive FTP scan using fast LIST -R command. Not all servers supports
   this, though.
   """
   ftp = FTPClass()
   if passive is not None:
      ftp.set_pasv(passive)
   ftp.connect(ftp_server, ftp_port)
   ftp.login(login, password)
   if ftp_dir != '/':
      ftp.cwd(ftp_dir)

   lines = []
   try:
      ftp.dir("-R", lines.append)
   except ftplib.error_perm:
      # The server does not implement LIST -R and
      # treats -R as a name of a directory (-:
      ftp.quit()
      raise FtpScanError("the server does not implement recursive listing")
   ftp.quit()

   tree = []
   current_dir = ftp_dir
   files = []

   for line in lines:
      if line:
         if line[-1] == ':' and not line.startswith("-rw-"): # directory
            tree.append((current_dir, files))
            if line[:2] == "./":
               line = line[1:] # remove leading dot
            elif line[0] != '/':
               line = '/' + line
            current_dir = line[:-1]
            files = []
         else:
            if not line.startswith("total "):
               entry = ftpparse(line)
               if entry:
                  if entry.file_type == 'f':
                     files.append(entry)
               else:
                  tree.append((ftpscan_error_mark, "Unrecognised line: `%s'" % line))
   tree.append((current_dir, files))

   if len(tree) == 1:
      raise FtpScanError("the server ignores -R in LIST")

   return tree


def ftpscan(ftp_server, ftp_port=0, login=None, password=None,
      ftp_dir='/', passive=None, FTPClass=ftplib.FTP):
   try:
      return ftpscanrecursive(ftp_server, ftp_port, login, password, ftp_dir, passive, FTPClass)
   except FtpScanError:
      try:
         return ftpscan1(ftp_server, ftp_port, login, password, ftp_dir, passive, FTPClass)
      except EOFError:
         return ftpscan1(ftp_server, ftp_port, login, password, ftp_dir, passive, FTPClass, True)
   except EOFError:
      return ftpscan1(ftp_server, ftp_port, login, password, ftp_dir, passive, FTPClass, True)


def test(ftp_server, func, passive=None, reconnect=False):
   from time import time
   start_time = time()

   tree = func(ftp_server, passive=passive, reconnect=reconnect)

   stop_time = time()
   print(stop_time - start_time)

   logfname = "%s.list" % ftp_server
   if sys.version_info[0] >= 3:
       log = codecs.open(logfname, 'w', encoding='utf-8')
   else:
       log = open(logfname, 'w')

   for ftp_dir, files in tree:
      if ftp_dir == ftpscan_error_mark:
         log.write("Error:\n")
         log.write(files)
         log.write('\n')
      else:
         log.write(ftp_dir + '\n')
         for _file in files:
            log.write("    ")
            log.write(_file.name + '\n')


def usage(code=0):
   sys.stderr.write("Usage: %s [-a|-p] [hostname]\n" % sys.argv[0])
   sys.exit(code)

if __name__ == "__main__":
   import sys
   from getopt import getopt, GetoptError

   try:
      options, arguments = getopt(sys.argv[1:], "hap",
         ["help", "active", "passive"])
   except GetoptError:
      usage(1)

   passive = None

   for option, value in options:
      if option in ("-h", "--help"):
         usage()
      elif option in ("-a", "--active"):
         passive = False
      elif option in ("-p", "--passive"):
         passive = True
      else:
         usage(2)

   l = len(arguments)
   if (l == 0):
      ftp_server = "localhost"
   elif l > 1:
      usage()
   else:
      ftp_server = arguments[0]

   print("Scanning", ftp_server)
   try:
      test(ftp_server, ftpscanrecursive, passive)
   except FtpScanError as msg:
      print("Rescanning due to the error:", msg)
      try:
         test(ftp_server, ftpscan1, passive)
      except EOFError:
         print("Rescanning due to the error: connection reset by peer")
         test(ftp_server, ftpscan1, passive, True)
   except EOFError:
      print("Rescanning due to the error: connection reset by peer")
      test(ftp_server, ftpscan1, passive, True)
