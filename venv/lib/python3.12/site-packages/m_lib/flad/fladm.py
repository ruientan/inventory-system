"""
   Flat ASCII Database with "must" keys
"""


from m_lib.flad.flad import Flad, def_keysep


class Flad_WithMustKeys(Flad):
   """
      Database with two lists of keys - keys that must be in every record,
      and keys that allowed to be in some records.
   """

   def __init__(self, check_record_func = None, must_keys = None, other_keys = None):
      Flad.__init__(self, check_record_func)
      self.must_keys = must_keys   # Save keys lists to store...
      self.other_keys = other_keys #... desired sequence of keys


   def store_to_file(self, f):
      if type(f) == type(''): # If f is string - use it as file's name
         outfile = open(f, 'w')
      else:
         outfile = f          # else assume it is opened file (fileobject) or
                              # "compatible" object (must has write() method)

      flush_record = 0 # Do not close record on 1st loop

      for record in self:
         copy_rec = record.copy() # Make a copy to delete keys

         if flush_record:
            outfile.write('\n') # Close record
         else:
            flush_record = 1    # Set flag for all but 1st record

         if self.must_keys:
            for key in self.must_keys:
               outfile.write(key + def_keysep + copy_rec[key] + '\n')
               del copy_rec[key]

         if self.other_keys:
            for key in self.other_keys:
               if key in copy_rec:
                  outfile.write(key + def_keysep + copy_rec[key] + '\n')
                  del copy_rec[key]

         if copy_rec:
            for key in list(copy_rec.keys()):
               outfile.write(key + def_keysep + copy_rec[key] + '\n')
               del copy_rec[key]

      if type(f) == type(''): # If f was open - close it
         outfile.close()


def check_record(data, record):
   """
      Check record for consistency and append it to list of records
   """
   must_keys = data.must_keys
   other_keys  = data.other_keys

   if must_keys:
      copy_must = must_keys[:] # Make a copy
   else:
      copy_must = None

   for key in record.keys(): # Check every key
      if must_keys and (key in must_keys):
         del copy_must[copy_must.index(key)] # Remove the key from copied list
      elif (must_keys and (key not in must_keys) and (other_keys and (key not in other_keys))) or (other_keys and (key not in other_keys)):
         raise KeyError("field key \"" + key + "\" is not in list of allowed keys")

   if copy_must: # If there is at least one key - it is an error:
                      # not all "must" keys are in record
      raise KeyError("not all \"must\" keys are in record; keys: " + str(copy_must))

   return 1


def load_file(f, check_record_func = None, must_keys = None, other_keys = None):
   """
      Create a database object and load it from file
   """

   db = Flad_WithMustKeys(check_record_func, must_keys, other_keys)
   db.load_file(f)

   return db


def load_from_file(f, check_record_func = None, must_keys = None, other_keys = None):
   """
      Create a database object and load it from file
   """

   db = Flad_WithMustKeys(check_record_func, must_keys, other_keys)
   db.load_from_file(f)

   return db
