"""
   Flat ASCII Database.
   This module implements a very simple database on the flat ASCII files.
"""


# Flad restriction error
class checking_error(Exception):
    pass

# Default key/value separator
def_keysep = ": "


class Flad(list):
   """
      Class to represent memory database.
      FLAD database is a list of records,
      where every record is a dictionary.
   """

   # Field and record separators are ALWAYS newline. It cannot be changed
   #    without extensive rewriting of this module
   # field_sep = rec_sep = '\n'

   def __init__(self, check_record_func = None, key_sep = def_keysep):
      list.__init__(self)
      self.check_record_func = check_record_func
      self.key_sep = key_sep

      self.comment = ''
      self.wait_comment = 1


   def check_record(self, record): # Method can be overriden in subclasses
      if self.check_record_func:
         if callable(self.check_record_func):
            return self.check_record_func(self, record)
         else:
            raise TypeError("non-callable restriction function")
      else:
         return 1


   def checking_error(self): # Method can be overriden in subclasses
      raise checking_error


   def __setitem__(self, i, item):
      if not self.check_record(item):
         self.checking_error()
      else:
         list.__setitem__(self, i, item)


   def __setslice__(self, i, j, v_list):
      if v_list:
         copy_list = v_list[:]
         for item in v_list:
            if not self.check_record(item):
               self.checking_error()
               del copy_list[copy_list.index(item)]
         list.__setslice__(self, i, j, copy_list)


   def append(self, item):
      if not self.check_record(item):
         self.checking_error()
      else:
         list.append(self, item)


   def insert(self, i, item):
      if not self.check_record(item):
         self.checking_error()
      else:
         list.insert(self, i, item)


   def split_key(self, line):
      """
         Split input line to key/value pair and add the pair to dictionary
      """
      ###line = line.lstrip() # Do not rstrip - if empty value, this will remove space from key
      if line[-1] == '\n':
         line = line[:-1] # Chop

      l = line.split(self.key_sep, 1) # Just split to key and reminder
      return tuple(l)


   def __parse_line(self, record, line): # Internal function
      if line == '\n': # Empty line is record separator (but there cannot be more than 1 empty lines)
         if record: # This helps to skip all empty lines
            self.append(record) # Check and add the record to list
            return 1 # Signal to stop filling the record and start a new one

      else:
         key, value = self.split_key(line)
         if key in record.keys(): # This have to be done with check_record
                                  # but the record is not complete now,
                                  # so it is not ready to be checked :(
                                  # And, of course, two keys with the same name
                                  # cannot be added to dictionary
            raise KeyError("field key \"" + key + "\" already in record")

         record[key] = value

      return 0


   def create_new_record(self): # Method can be overriden in subclasses
      return {}


   def feed(self, record, line): # Method can be overriden in subclasses
      if line:
         if self.wait_comment:
            if line.strip() == '':
               self.comment = self.comment + '\n'
               self.wait_string = 0
               return 0

            elif line.lstrip()[0] == '#':
               self.comment = self.comment + line
               return 0

            else:
               self.wait_comment = 0
               # Fallback to parsing

         return self.__parse_line(record, line)

      else:
         self.append(record)

      return 0


   def load_file(self, f):
      """
         Load a database from file as a list of records.
         Every record is a dictionary of key/value pairs.
         The file is reading as whole - this is much faster, but require
         more memory.
      """

      if type(f) == type(''): # If f is string - use it as file's name
         infile = open(f, 'r')
      else:
         infile = f           # else assume it is opened file (fileobject) or
                              # "compatible" object (must has readline() methods)

      try:
         lines = infile.readlines()

      finally:
         if type(f) == type(''): # If f was opened - close it
            infile.close()

      record = self.create_new_record()

      for line in lines:
         if self.feed(record, line):
            record = self.create_new_record()

      # Close record on EOF without empty line
      if record:
         self.feed(record, None)


   def load_from_file(self, f):
      """
         Load a database from file as a list of records.
         Every record is a dictionary of key/value pairs.
         The file is reading line by line - this is much slower, but do not
         require so much memory. (On systems with limited virtual memory,
         like DOS, it is even faster - for big files)
      """

      if type(f) == type(''): # If f is string - use it as file's name
         infile = open(f, 'r')
      else:
         infile = f           # else assume it is opened file (fileobject) or
                              # "compatible" object (must has readline() method)

      record = self.create_new_record()

      try:
         line = infile.readline()

         while line:
            if self.feed(record, line):
               record = self.create_new_record()

            line = infile.readline()

      finally:
         if type(f) == type(''): # If f was opened - close it
            infile.close()

      # Close record on EOF without empty line
      if record:
         self.feed(record, None)


   def store_to_file(self, f):
      if type(f) == type(''): # If f is string - use it as file's name
         outfile = open(f, 'w')
      else:
         outfile = f          # else assume it is opened file (fileobject) or
                              # "compatible" object (must has write() method)

      flush_record = 0 # Do not close record on 1st loop

      if self.comment != '':
         outfile.write(self.comment)

      for record in self:
         copy_rec = record.copy() # Make a copy to delete keys

         if flush_record:
            outfile.write('\n') # Close record
         else:
            flush_record = 1    # Set flag for all but 1st record

         if copy_rec:
            for key in list(copy_rec.keys()):
               outfile.write(key + self.key_sep + copy_rec[key] + '\n')
               del copy_rec[key]

      if type(f) == type(''): # If f was opened - close it
         outfile.close()


def load_file(f, check_record_func = None):
   """
      Create a database object and load it from file
   """

   db = Flad(check_record_func)
   db.load_file(f)

   return db


def load_from_file(f, check_record_func = None):
   """
      Create a database object and load it from file
   """

   db = Flad(check_record_func)
   db.load_from_file(f)

   return db
