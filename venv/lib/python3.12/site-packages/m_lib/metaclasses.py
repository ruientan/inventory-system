#! /usr/bin/env python


# From: Michele Simionato (mis6@pitt.edu)
# http://groups.google.com/groups?selm=2259b0e2.0304250413.4be8ee45%40posting.google.com
# To solve "TypeError: metatype conflict among bases"


def _generatemetaclass(bases, metas):
   "Internal function called by child"

   if metas == (type,): # trivial metaclass
       metabases = (); metaname = "_"
   else: # non-trivial metaclass
       metabases = metas
       metaname = "_"+''.join([m.__name__ for m in metas])
   trivial = lambda m: m in metabases or m is type

   for b in bases:
       meta_b = type(b)
       if not trivial(meta_b):
           metabases += (meta_b,)
           metaname += meta_b.__name__

   if not metabases: # trivial metabase
       return type
   elif len(metabases) == 1: # single metabase
       return metabases[0]
   else: # multiple metabases
       return type(metaname, metabases, {}) # creates a new metaclass
      #shifting the possible conflict to meta-metaclasses


def child(*bases, **options):
   """Class factory avoiding metatype conflicts: if the base classes have
   metaclasses conflicting within themselves or with the given metaclass,
   it automatically generates a compatible metaclass and instantiate the
   child class from it. The recognized keywords in the option dictionary
   are name, dic and meta."""
   name = options.get('name', ''.join([b.__name__ for b in bases])+'_')
   dic = options.get('dic', {})
   metas = options.get('metas', (type,))
   return _generatemetaclass(bases, metas)(name, bases, dic)



def test():
    class M_A(type): pass
    class M_B(type): pass
    A = M_A('A', (), {})
    B = M_B('B', (), {})

    try:
       class C(A, B): pass
    except TypeError:
       pass
    else:
       raise RuntimeError

    C = child(A, B, name='C')


if __name__ == "__main__":
    test()
