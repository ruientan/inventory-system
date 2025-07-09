#! /usr/bin/env python
"""Parse output of FTP LIST command.
   Pure python implementation.

   See http://cr.yp.to/ftpparse.html, http://effbot.org/downloads#ftpparse,
   http://c0re.23.nu/c0de/ftpparsemodule/ and http://www.ocgy.ubc.ca/~tang/treeftp

Currently covered formats:
   UNIX ls, with or without gid;
   Windoze FTP Servers;
   VMS;
   WFTPD;
   NetPresenz (Mac);
   NetWare;
   DOS;

Definitely not covered:
   EPLF (show me an FTP server first...);
   Long VMS filenames, with information split across two lines;
   NCSA Telnet FTP server. Has LIST = NLST (and bad NLST for directories).
"""


from __future__ import print_function
try:
   from mx import DateTime
except ImportError:
   _parse_datetime = False
else:
   _parse_datetime = True


class parse_error(Exception): pass


class entry:
   def __init__(self, name=None, perm=None, nlink=None, user=None, group=None, \
         size=None, mtime=None, links_to=None, file_type=None):

      if mtime:
         mtime = ' '.join(mtime)
         if _parse_datetime:
            try:
               mtime = DateTime.DateTimeFrom(mtime)
            except DateTime.Error:
               pass

      self.name = name
      self.perm = perm
      self.nlink = nlink
      self.user = user
      self.group = group
      self.size = size
      self.mtime = mtime
      self.links_to = links_to
      self.file_type = file_type # f - regular file, d - directory, l - symlink


   def __str__(self):
      return """<%s: name=%s, perm=%s, nlink=%s, user=%s, group=%s, size=%s, mtime=%s, links-to=%s, type=%s at 0x%x>""" % (
      self.__class__.__name__, self.name, self.perm, self.nlink,
         self.user, self.group, self.size, self.mtime,
         self.links_to, self.file_type, id(self))


def _parse_unix(line, parts):
   name = None
   perm = None
   nlink = None
   user = None
   group = None
   size = None
   mtime = None
   links_to = None
   file_type = None

   perm = parts[0]

   if parts[1][0] == '[': # NetWare
      if perm[0] == 'd':
         file_type = 'd'
      elif perm[0] == '-':
         file_type = 'f'
      else:
         return None
      perm = perm + ' ' + parts[1]
      user = parts[2]
      size = parts[3]
      mtime = parts[4:7]

      parts = line.split(None, 7) # resplit the original line...
      name = parts[7]             # ...in case the filename contains whitespaces

   elif parts[1] == "folder": # NetPresenz for the Mac
      file_type = 'd'
      size = parts[2]
      mtime = parts[3:6]

      parts = line.split(None, 6)
      name = parts[6]

   elif parts[0][0] == 'l': # symlink
      file_type = 'l'
      nlink = int(parts[1])
      user = parts[2]
      group = parts[3]
      size = parts[4]
      mtime = parts[5:8]

      parts = line.split(None, 8)
      link = parts[8]
      parts = link.split(" -> ")
      name = parts[0]
      links_to = parts[1]

   elif len(parts) > 8:
      if perm[0] == 'd':
         file_type = 'd'
      elif perm[0] == '-':
         file_type = 'f'
      else:
         return None
      nlink = int(parts[1])
      user = parts[2]
      group = parts[3]
      size = parts[4]
      mtime = parts[5:8]

      parts = line.split(None, 7)
      name = parts[7]
      parts = name.split(' ')[1:]
      name = ' '.join(parts)

   else:
      if parts[2].isdigit(): # NetPresenz
         file_type = 'f'
         size = parts[3]
         mtime = parts[4:7]
      else:
         if perm[0] == 'd':
            file_type = 'd'
         elif perm[0] == '-':
            file_type = 'f'
         else:
            return None
         nlink = int(parts[1])
         user = parts[2]
         size = parts[3]
         mtime = parts[4:7]

      parts = line.split(None, 7)
      name = parts[7]

   return entry(name, perm, nlink, user, group, size, mtime, links_to, file_type)


def _parse_vms(parts):
   name = parts[0]
   perm = parts[5]
   nlink = parts[1]
   user = parts[4][1:-1]
   group = None
   size = None
   mtime = parts[2:4]
   links_to = None
   file_type = None

   if ',' in user:
      parts = user.split(',')
      user = parts[0]
      group = parts[1]

   return entry(name, perm, nlink, user, group, size, mtime, links_to, file_type)


def _parse_dos(parts):
   name = parts[3]
   perm = None
   nlink = None
   user = None
   group = None
   size = None
   links_to = None

   if _parse_datetime:
      # Change %m-%d-%y format to %y-%m-%d
      date = parts[0]
      date_parts = date.split('-')
      date = "%s-%s-%s" % (date_parts[2], date_parts[0], date_parts[1])
      time = parts[1]
      mtime = [date, time]
   else:
      mtime = parts[0:2]

   if parts[2] == "<DIR>":
      file_type = 'd'
   else:
      file_type = 'f'
      size = int(parts[2])

   return entry(name, perm, nlink, user, group, size, mtime, links_to, file_type)


def ftpparse(line):
   parts = line.split()
   c = parts[0][0]

   if c == '+': # EPLF format is not supported
      return None

   if c in ('b', 'c', 'd', 'l', 'p', 's', '-'): # UNIX-like
      return _parse_unix(line, parts)

   if ';' in parts[0]: # VMS
      return _parse_vms(parts)

   if '0' <= c <= '9': # DOS
      return _parse_dos(parts)


   #Some useless lines, safely ignored:
   #"Total of 11 Files, 10966 Blocks." (VMS)
   #"total 14786" (UNIX)
   #"DISK$ANONFTP:[ANONYMOUS]" (VMS)
   #"Directory DISK$PCSA:[ANONYM]" (VMS)

   return None


def test():
   #UNIX-style listing, without inum and without blocks
   print(ftpparse("-rw-r--r--   1 root     other        531 Jan 29 03:26 README"))
   print(ftpparse("dr-xr-xr-x   2 root     other        512 Apr  8  1994 etc"))
   print(ftpparse("dr-xr-xr-x   2 root     512 Apr  8  1994 etc"))
   print(ftpparse("lrwxrwxrwx   1 root     other          7 Jan 25 00:17 bin -> usr/bin"))
   #FTP servers for Windoze:
   print(ftpparse("----------   1 owner    group         1803128 Jul 10 10:18 ls-lR.Z"))
   print(ftpparse("d---------   1 owner    group               0 May  9 19:45 Softlib"))
   #WFTPD for DOS:
   print(ftpparse("-rwxrwxrwx   1 noone    nogroup      322 Aug 19  1996 message.ftp"))
   #NetWare:
   print(ftpparse("d [R----F--] supervisor            512       Jan 16 18:53    login"))
   print(ftpparse("- [R----F--] rhesus             214059       Oct 20 15:27    cx.exe"))
   #NetPresenz for the Mac:
   print(ftpparse("-------r--         326  1391972  1392298 Nov 22  1995 MegaPhone.sit"))
   print(ftpparse("drwxrwxr-x               folder        2 May 10  1996 network"))

   #MultiNet (some spaces removed from examples)
   print(ftpparse("00README.TXT;1      2 30-DEC-1996 17:44 [SYSTEM] (RWED,RWED,RE,RE)"))
   print(ftpparse("CORE.DIR;1          1  8-SEP-1996 16:09 [SYSTEM] (RWE,RWE,RE,RE)"))
   #non-MutliNet VMS:
   print(ftpparse("CII-MANUAL.TEX;1  213/216  29-JAN-1996 03:33:12  [ANONYMOU,ANONYMOUS]   (RWED,RWED,,)"))

   #DOS format
   print(ftpparse("04-27-00  09:09PM       <DIR>          licensed"))
   print(ftpparse("07-18-00  10:16AM       <DIR>          pub"))
   print(ftpparse("04-14-00  03:47PM                  589 readme.htm"))

   print(ftpparse("-rw-r--r--   1 root     other        531 Jan 29 03:26 READ ME"))
   print(ftpparse("-rw-r--r--   1 root     other        531 Jan 29 03:26  DO NOT READ ME "))

if __name__ == "__main__":
   test()
