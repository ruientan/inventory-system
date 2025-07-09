#! /usr/bin/env python
"""tty menus"""


from __future__ import print_function


try:
   raw_input
except NameError:  # Python 3
   raw_input = input


def hmenu(prompt, astring):
   """
      Writes prompt and read result
      until result[0] is one of allowed characters (from astring),
      and returns the character
   """
   while 1:
      result = raw_input(prompt)
      if len(result) > 0:
         c = result[0]
         if c in astring:
            return c


def vmenu(item_list, prompt, format = "%d. %s"):
   """
      Prints numbered list of items and allow user to select one,
      returns selected number. Returns -1, if user enter non-numeric string.
   """
   for i in range(len(item_list)):
      print(format % (i, item_list[i]))
   print

   result = raw_input(prompt)

   try:
      result = int(result)
   except ValueError:
      result = -1

   return result


def test():
   result = hmenu("Select: d)aily, w)eekly, m)onthly, c)ancel: ", "dwmc")
   print("Answer is '%s'\n" % result)

   os_list = ["DOS", "Windows", "UNIX"]
   result = vmenu(os_list, "Select OS: ")
   if 0 <= result < len(os_list):
      print("Answer is '%s'\n" % os_list[result])
   else:
      print("Wrong selection")

if __name__ == "__main__":
   test()
