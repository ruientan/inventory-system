"""
   Flat ASCII Database to load WIN.INI-like files.
"""


import re
from m_lib.flad import flad


from .flad import checking_error
class error(checking_error):
    pass

class section_error(checking_error):
    pass


re_section = re.compile("^ *\[(.+)\] *$")


class Flad_WIni(flad.Flad):
   """
      FLAD database is a list of records, where every record is
      a tuple (section_name, keys, section_dictionary).
      Sounds similary to Flad? But it is Flad! The only difference is that
      Flad_WIni has section names and keys (i.e. list of keys and comments
      in every section to preserve comments and desired order of keys).
   """
   def __init__(self):
      flad.Flad.__init__(self, key_sep = '=')
      self.first_section = 1


   def __parse_line(self, record, line): # Internal function
      match = re_section.match(line) # Record separator is section name
      if match:
         return match.group(1) # Signal to stop filling the record (section) and start a new one

      if self.first_section:
         if line.strip() != '':
            raise error("non-empty line before 1st section")

      elif (line.strip() == '') or (line.lstrip()[0] == ';') : # Empty line or comment
         record[0].append(line)

      else:
         key, value = self.split_key(line)
         if key in record[1].keys(): # This have to be done with check_record
                                  # but the record is not complete now,
                                  # so it is not ready to be checked :(
                                  # And, of course, two keys with the same name
                                  # cannot be added to dictionary
            raise KeyError("field key \"" + key + "\" already in record")

         record[0].append(key)
         record[1][key] = value

      return 0


   def create_new_record(self):
      return ([], {})


   def feed(self, record, line):
      if line:
         section = self.__parse_line(record, line)
         if section:
            if not self.first_section:
               self.append((self.section, record[0], record[1]))
               self.section = section

               return 1 # Section filled - create new section
            else:
               self.first_section = 0
               self.section = section

         else:
            if self.first_section and (line.strip() != ''):
               raise error("non-empty line before 1st section")
            # else: line had been appended to section in __parse_line()

      else: # This called after last line of the source file
         self.append((self.section, record[0], record[1]))
         del self.section, self.first_section

         # Now remove last empty line in every section
         for record in self:
            klist = record[1]
            if klist:
               l = len(klist) - 1
               if klist[l].strip() == '':
                  del klist[l]

      return 0


   def store_to_file(self, f):
      if type(f) == type(''): # If f is string - use it as file's name
         outfile = open(f, 'w')
      else:
         outfile = f          # else assume it is opened file (fileobject) or
                              # "compatible" object (must has write() method)

      flush_section = 0 # Do not close 1st section

      for record in self:
         if flush_section:
            outfile.write('\n') # Close section
         else:
            flush_section = 1    # Set flag for all but 1st section

         outfile.write('[' + record[0] + ']\n') # Section

         if record[1]:
            for key in record[1]:
               if key.strip() == '' or key.lstrip()[0] == ';' :
                  outfile.write(key)
               else:
                  outfile.write(key + self.key_sep + record[2][key] + '\n')

      if type(f) == type(''): # If f was opened - close it
         outfile.close()


   def find_section(self, section):
      for i in range(0, len(self)):
         record = self[i]
         if record[0] == section:
            return i

      return -1


   def add_section(self, section):
      rec_no = self.find_section(section)
      if rec_no >= 0:
         raise section_error("section [%s] already exists" % section)

      self.append((section, [], {}))


   def del_section(self, section):
      rec_no = self.find_section(section)
      if rec_no < 0:
         raise section_error("section [%s] does not exists" % section)

      del self[rec_no]


   def set_keyvalue(self, section, key, value):
      rec_no = self.find_section(section)
      if rec_no < 0:
         record = (section, [key], {key: value})
         self.append(record)

      else:
         record = self[rec_no]
         if key not in record[1]:
            record[1].append(key)
         record[2][key] = value


   def get_keyvalue(self, section, key):
      rec_no = self.find_section(section)
      if rec_no < 0:
         raise section_error("section [%s] does not exists" % section)

      record = self[rec_no]
      if key not in record[1]:
         raise KeyError("section [%s] does not has `%s' key" % (section, key))

      return record[2][key]


   def get_keydefault(self, section, key, default):
      rec_no = self.find_section(section)
      if rec_no < 0:
         return default

      record = self[rec_no]
      if key not in record[1]:
         return default

      return record[2][key]


   def del_key(self, section, key):
      rec_no = self.find_section(section)
      if rec_no < 0:
         raise section_error("section [%s] does not exists" % section)

      record = self[rec_no]
      if key not in record[1]:
         raise KeyError("section [%s] does not has `%s' key" % (section, key))

      klist = record[1]
      del klist[klist.index(key)]
      del record[2][key]


def load_file(f):
   db = Flad_WIni()
   db.load_file(f)

   return db


def load_from_file(f):
   db = Flad_WIni()
   db.load_from_file(f)

   return db
