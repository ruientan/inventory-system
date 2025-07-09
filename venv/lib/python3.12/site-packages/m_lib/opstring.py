#! /usr/bin/env python
# -*- coding: koi8-r -*-

#
# opString - string/pathnames manipulation routines
# Some ideas came from Turbo Professional/Object Professional (t/o)pString.PAS
#


from __future__ import print_function
from string import *


#
### Int/string conversion routines
#


def bin(i):
   """
      Convert integer to binary string.
   """
   s = ''
   q = i
   while (1):
      q, r = divmod(q, 2)
      s = digits[r] + s
      if q == 0: break

   return s


#
### String manipulation routines
#


def PadCh(S, Ch, Len):
   """ Return a string right-padded to length Len with Ch """
   if len(S) >= Len:
      return S
   else:
      return S + Ch*(Len - len(S))


def Pad(S, Len):
   """ Return a string right-padded to length len with blanks """
   return PadCh(S, ' ', Len)


def LeftPadCh(S, Ch, Len):
   """ Return a string left-padded to length len with ch """
   if len(S) >= Len:
      return S
   else:
      return Ch*(Len - len(S)) + S


def LeftPad(S, Len):
   """ Return a string left-padded to length len with blanks """
   return LeftPadCh(S, ' ', Len)


def CenterCh(S, Ch, Width):
   """ Return a string centered in a string of Ch with specified width """
   if len(S) >= Width:
      return S
   else:
      l = (Width - len(S)) // 2
      r = Width - len(S) - l
      return Ch*l + S + Ch*r


def Center(S, Width):
   """ Return a string centered in a blank string of specified width """
   return CenterCh(S, ' ', Width)


def FindStr(str, list):
   """ Find given string in the list of strings """
   for i in range(len(list)):
      if str == list[i]:
         return i

   return -1


def FindStrUC(str, list):
   """ Find string ignoring case """
   str = upper(str)
   for i in range(len(list)):
      if str == upper(list[i]):
         return i

   return -1


# Склонения

transl_adict = {
   "day"  : ["день", "дня", "дней"],
   "week" : ["неделя", "недели", "недель"],
   "month": ["месяц", "месяца", "месяцев"],
   "year" : ["год", "года", "лет"]
}

transl_adict["days"] = transl_adict["day"]
transl_adict["weeks"] = transl_adict["week"]
transl_adict["months"] = transl_adict["month"]
transl_adict["years"] = transl_adict["year"]

transl_vdict = {
   1: 0,
   2: 1, 3: 1, 4: 1,
   5: 2, 6: 2, 7: 2, 8: 2, 9: 2, 0: 2
}

def translate_a(val, id):
   if not transl_adict.has_key(id):
      return ''

   if 5 <= (val % 100) <= 20:
      val = 2
   else:
      val = transl_vdict[val % 10]
   return transl_adict[id][val]


def recode(s, from_encoding, to_encoding, errors = "strict"):
   if isinstance(s, bytes):
      s = s.decode(from_encoding, errors)
   return s.encode(to_encoding, errors)


def win2koi(s, errors = "strict"):
   return recode(s, "cp1251", "koi8-r", errors)

def koi2win(s, errors = "strict"):
   return recode(s, "koi8-r", "cp1251", errors)


#
### Test stuff
#

def test():
   print("bin(0x6) =", bin(0x6))
   print("bin(0xC) =", bin(0xC))

   print("'Test' left-padded :", LeftPad("Test", 20))
   print("'Test' right-padded:", PadCh("Test", '*', 20))
   print("'Test' centered    :", CenterCh("Test", '=', 20))

   print("'Олег':", koi2win(win2koi("Олег")))

if __name__ == "__main__":
   test()
