#! /usr/bin/env python
"""Test if current interpreter do not have clock() and define it as need"""

from __future__ import print_function
import sys, time

print("Testing...", end=' ')
sys.stdout.flush()

time.sleep(3)
print('\n' + " "*len("Testing...") + '\n', end=' ')

need_clock = time.clock() != 3 if hasattr(time, 'clock') else True

outfile = open("clock.py", 'w')

if need_clock:
   print("Generaing clock.py with custom clock()")
   outfile.write("""\"\"\"
   Define clock() for systems that do not have it
\"\"\"

from time import time
_clock = time()

def clock():
   return int(time() - _clock)
""")
else:
   print("Generaing clock.py with standard clock()")
   outfile.write("""\"\"\"
   Define clock() shim
\"\"\"

from time import clock
   """)
