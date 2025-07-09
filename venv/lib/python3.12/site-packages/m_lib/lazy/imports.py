"""Lazy imoport - import the module upon first request"""


try:
   from mx.Misc import LazyModule

except ImportError:

   class LazyModule:
      def __init__(self, module_name, locals, globals=None):
         self.module = None
         self.module_name = module_name
         self.locals = locals
         if globals is None:
            globals = locals
         self.globals = globals

      def __getattr__(self, attr):
         if self.module is None:
            self.module = module = __import__(self.module_name, self.globals, self.locals)
         else:
            module = self.module
         return getattr(module, attr)
