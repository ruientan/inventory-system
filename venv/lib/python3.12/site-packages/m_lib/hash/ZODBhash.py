"""(g)dbm-compatible interface to ZODB"""

import sys
try:
    from ZODB import FileStorage, DB, POSException
except ImportError:
    # prevent a second import of this module from spuriously succeeding
    del sys.modules[__name__]
    raise


__all__ = ["error", "open"]

error = POSException.POSError                     # Exported for anydbm


class ZODBhash:
    def __init__(self, file, flag, mode=0o666, trans_threshold=1000):
        create = (flag == 'n') # force recreation
        # if flag == 'w' or 'c' and file does not exist FileStorage will set it to 1 for us 

        self.read_only = read_only = (flag == 'r')
        self._closed = 0

        self.trans_threshold = trans_threshold
        self._transcount = 0 # transactions counter - for commiting transactions

        storage = FileStorage.FileStorage(file, create=create, read_only = read_only)
        db = DB(storage)
        self.conn = conn = db.open()
        self.dbroot = conn.root()

    def __del__(self):
        self.close()

    def keys(self):
        return self.dbroot.keys()

    def __len__(self):
        return len(self.dbroot)

    def has_key(self, key):
        return self.dbroot.has_key(key)

    def get(self, key, default=None):
        if self.dbroot.has_key(key):
            return self[key]
        return default

    def __getitem__(self, key):
        return self.dbroot[key]

    def __setitem__(self, key, value):
        self.dbroot[key] = value
        self._add_tran()

    def __delitem__(self, key):
        del self.dbroot[key]
        self._add_tran()

    def close(self):
        if self._closed: return
        if not self.read_only:
            get_transaction().commit()
            self.conn.db().close()
        self.conn.close()
        self._closed = 1

    def _add_tran(self):
        self._transcount = self._transcount + 1
        if self._transcount == self.trans_threshold:
            self._transcount = 0
            get_transaction().commit()


def open(file, flag, mode=0o666):
    return ZODBhash(file, flag, mode)
