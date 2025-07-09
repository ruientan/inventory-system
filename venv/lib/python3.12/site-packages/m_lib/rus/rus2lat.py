#! /usr/bin/env python
# -*- coding: koi8-r -*-

from __future__ import print_function
from ..lazy.dict import LazyDictInitFunc

#
# Rus -> Lat transliteration (koi2lat and win2lat)
#

koi2lat_d = {
   "А": "A",
   "Б": "B",
   "В": "V",
   "Г": "G",
   "Д": "D",
   "Е": "E",
   "Ё": "Yo",
   "Ж": "Zh",
   "З": "Z",
   "И": "I",
   "Й": "Y",
   "К": "K",
   "Л": "L",
   "М": "M",
   "Н": "N",
   "О": "O",
   "П": "P",
   "Р": "R",
   "С": "S",
   "Т": "T",
   "У": "U",
   "Ф": "F",
   "Х": "H",
   "Ц": "Ts",
   "Ч": "Ch",
   "Ш": "Sh",
   "Щ": "Sh",
   "Ъ": "'",
   "Ь": "'",
   "Ы": "Y",
   "Э": "E",
   "Ю": "Yu",
   "Я": "Ya",
   "а": "a",
   "б": "b",
   "в": "v",
   "г": "g",
   "д": "d",
   "е": "e",
   "ё": "yo",
   "ж": "zh",
   "з": "z",
   "и": "i",
   "й": "y",
   "к": "k",
   "л": "l",
   "м": "m",
   "н": "n",
   "о": "o",
   "п": "p",
   "р": "r",
   "с": "s",
   "т": "t",
   "у": "u",
   "ф": "f",
   "х": "h",
   "ц": "ts",
   "ч": "ch",
   "ш": "sh",
   "щ": "sh",
   "ъ": "'",
   "ь": "'",
   "ы": "y",
   "э": "e",
   "ю": "yu",
   "я": "ya",
}

def make_xxx2lat(encoding="cp1251"):
   d = {}
   for k, v in koi2lat_d.items():
      d[k] = v
   return d


win2lat_d = LazyDictInitFunc(make_xxx2lat, encoding="cp1251")


def rus2lat(instr, rus2lat_d = koi2lat_d):
   out = []
   for c in instr:
      c = rus2lat_d.get(c, c)
      if isinstance(c, int):
         c = chr(c)
      out.append(c)
   return ''.join(out)


koi2lat = rus2lat

def win2lat(instr):
   return rus2lat(instr, win2lat_d)


if __name__ == "__main__":
   Test = "Щербаков Игорь Григорьевич. АБВ xyz абв ЬЬЭЮЯ ъьэюя"
   print("Test:", Test)
   print("Тест:", koi2lat(Test))
   print("Тест:", win2lat(Test))
