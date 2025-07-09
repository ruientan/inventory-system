#! /usr/bin/env python
# -*- coding: koi8-r -*-

from __future__ import print_function
from ..lazy.dict import LazyDictInitFunc

#
# Lat -> Rus translation
#

lat2koi_d = {
   "q": "й",
   "w": "ц",
   "e": "у",
   "r": "к",
   "t": "е",
   "y": "н",
   "u": "г",
   "i": "ш",
   "o": "щ",
   "p": "з",
   "[": "х",
   "]": "ъ",
   "a": "ф",
   "s": "ы",
   "d": "в",
   "f": "а",
   "g": "п",
   "h": "р",
   "j": "о",
   "k": "л",
   "l": "д",
   ";": "ж",
   "'": "э",
   "z": "я",
   "x": "ч",
   "c": "с",
   "v": "м",
   "b": "и",
   "n": "т",
   "m": "ь",
   ",": "б",
   ".": "ю",
   "Q": "Й",
   "W": "Ц",
   "E": "У",
   "R": "К",
   "T": "Е",
   "Y": "Н",
   "U": "Г",
   "I": "Ш",
   "O": "Щ",
   "P": "З",
   "{": "Х",
   "}": "Ъ",
   "A": "Ф",
   "S": "Ы",
   "D": "В",
   "F": "А",
   "G": "П",
   "H": "Р",
   "J": "О",
   "K": "Л",
   "L": "Д",
   ":": "Ж",
   "\"": "Э",
   "Z": "Я",
   "X": "Ч",
   "C": "С",
   "V": "М",
   "B": "И",
   "N": "Т",
   "M": "Ь",
   "<": "Б",
   ">": "Ю",
   "`": "ё",
   "~": "Ё",
   "!": "!",
   "@": "\"",
   "#": "#",
   "$": "*",
   "%": ":",
   "^": ",",
   "&": ".",
   "*": ";",
}


def make_lat2xxx(encoding="cp1251"):
   d = {}
   for k, v in lat2koi_d.items():
      d[k] = v
   return d


lat2win_d = LazyDictInitFunc(make_lat2xxx, encoding="cp1251")


def lat2rus(instr, lat2rus_d = lat2koi_d):
   out = []
   for c in instr:
      c = lat2rus_d.get(c, c)
      out.append(c)
   return ''.join(out)


lat2koi = lat2rus

def lat2win(instr):
   return lat2rus(instr, lat2win_d)


if __name__ == "__main__":
   Test = "Ghbdtn nt,t^ ghtrhfcysq vbh!"
   print("Test:", Test)
   print("Тест:", lat2koi(Test))
   test = lat2win(Test)
   print("Тест:", test)
