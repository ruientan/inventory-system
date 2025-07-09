"""Extended disk hashes package.

It extends anydbm/whichdb with ZODB and MetaKit-based hashes."""


__all__ = ["zshelve", "ZODBhash", "MKhash"]


import anydbm
anydbm._names.insert(len(anydbm._names)-1, ['ZODBhash', 'MKhash'])
   # Insert before dumbdbm


import whichdb
_orig_module = whichdb
_orig_whichdb = _orig_module.whichdb

def whichdb(filename):
    result = _orig_whichdb(filename)
    if result:
       return result

    try:
        f = open(filename, "rb")
    except IOError:
        return None

    # Read the start of the file -- the magic number
    s = f.read(4)
    f.close()

    # Return "" if not at least 4 bytes
    if len(s) != 4:
        return ""

    # Check for MetaKit
    if s == "JL\x1A\0":
        return "MKhash"

    # Check for ZODB
    if s == "FS21":
        return "ZODBhash"

    # Unknown
    return ""

_orig_module.whichdb = whichdb # Now install our extended replacement
whichdb.__doc__ = _orig_whichdb.__doc__
