"""
   Flat ASCII Database to implement VERY simple config files.
"""


from m_lib.flad import flad, fladm


from .flad import checking_error
class error(checking_error):
    # Too many records
    pass


class Flad_Conf(dict):
   """
      FLAD config is just FLAD Database with exactly ONE record.
      Flad_Conf objects are just UserDicts.
   """
   def __init__(self, must_keys = None, other_keys = None):
      dict.__init__(self)

      self.must_keys = must_keys
      self.other_keys = other_keys


   def __make_db(self):
      if self.must_keys:
         db = fladm.Flad_WithMustKeys(check_record, self.must_keys, self.other_keys)
      else:
         db = flad.Flad()

      return db


   def load_file(self, f):
      db = self.__make_db()
      db.load_file(f)

      if len(db) != 1:
         raise error("incorrect number of records in config file `%s'; expected 1, got %d" % (str(f), len(db)))

      self.update(db[0])


   def load_from_file(self, f):
      db = self.__make_db()
      db.load_from_file(f)

      if len(db) != 1:
         raise error("incorrect number of records in config file `%s'; expected 1, got %d" % (str(f), len(db)))

      self.update(db[0])


   def store_to_file(self, f):
      db = self.__make_db()
      db.append(self)
      db.store_to_file(f)


def check_record(data, record): # Only allow append 1 record
   return len(data) == 0


def load_file(f, must_keys = None, other_keys = None):
   """
      Create a database object and load it from file
   """

   db = Flad_Conf(must_keys, other_keys)
   db.load_file(f)

   return db


def load_from_file(f, must_keys = None, other_keys = None):
   """
      Create a database object and load it from file
   """

   db = Flad_Conf(must_keys, other_keys)
   db.load_from_file(f)

   return db
