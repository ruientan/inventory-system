#! /usr/bin/env python

#
# useful function(s) for module crypt
#


from __future__ import print_function
try:
    import crypt
except ImportError:  # Python 3.13+
    crypt = None
import random


saltchars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcedfghijklmnopqrstuvwxyz0123456789./"
len_salt = len(saltchars)

def gen_salt():
   """
      There are some difference among modern unicies. BSD/OS, for example,
      uses MD5 hash, and ignores salt completely. FreeBSD uses 3 different
      versions of crypt() - with standard salt, with extended 9-byte salt,
      and MD5 (again, ignoring salt at all).
      This function generates salt for standard "Broken DES"-based crypt().
   """
   r1 = random.randint(0, len_salt-1)
   r2 = random.randint(0, len_salt-1)
   return "%s%s" % (saltchars[r1], saltchars[r2])


def test():
   try:
      raw_input
   except NameError:  # Python 3
      raw_input = input

   passwd = raw_input("Enter password: ")
   salt = gen_salt()
   encrypted = crypt.crypt(passwd, salt)

   pwd_file = open("test.pwd", 'w')
   pwd_file.write("%s:%s" % ("user", encrypted))
   pwd_file.close()
   print("Password file written")

   pwd_file = open("test.pwd", 'r')
   username, encrypted = pwd_file.readline()[:-1].split(':')
   pwd_file.close()

   if crypt.crypt(encrypted, encrypted):
      print("Password verified Ok")
   else:
      print("BAD password")

if __name__ == "__main__":
   if crypt is not None:
      test()
