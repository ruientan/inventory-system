"""Lazy dictionaries calculate self content upon first access"""

class LazyDict:
   "Abstract parent of all lazy dictionaries"

   def _init(self):
      raise NotImplementedError

   def __getattr__(self, attr):
      if self.data is None: self._init()
      return getattr(self.data, attr)

   def __getitem__(self, key):
      if self.data is None: self._init()
      return self.data[key]

   def __setitem__(self, key, value):
      if self.data is None: self._init()
      self.data[key] = value


class LazyDictInitFunc(LazyDict):
   "Lazy dict that initializes itself by calling supplied init function"

   def __init__(self, init=None, *args, **kw):
      self.init = init
      self.data = None
      self.args = args
      self.kw = kw

   def _init(self):
      init = self.init
      if init is None:
         data = {} # just a new empty dict
      else:
         data = init(*self.args, **self.kw)
      self.data = data
