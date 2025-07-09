"""(g)dbm-compatible interface to MetaKit"""

import sys
try:
    import Mk4py
except ImportError:
    # prevent a second import of this module from spuriously succeeding
    del sys.modules[__name__]
    raise


__all__ = ["error", "open"]

error = ValueError


class MKhash:
    def __init__(self, file, flag, mode=0o666, trans_threshold=1000):
        self.read_only = 0
        self._closed = 0

        self.trans_threshold = trans_threshold
        self._transcount = 0 # transactions counter - for commiting transactions

        if flag in ('c', 'n'):
            mode = 1
        elif flag == 'r':
            mode = 0
            self.read_only = 1
        else:
            mode = 2

        self.db = db = Mk4py.storage(file, mode)
        if mode == 1:
            self.vw = db.getas("hash[key:S,value:S]")
        else:
            self.vw = db.view("hash")

    def __del__(self):
        self.close()

    def keys(self):
        return map(lambda x: x.key, self.vw)

    def __len__(self):
        return len(self.vw)

    def has_key(self, key):
        return self.vw.find(key=key)+1

    def get(self, key, default=None):
        if self.has_key(key):
            return self[key]
        return default

    def __getitem__(self, key):
        vw = self.vw
        ix = vw.find(key=key)
        if ix == -1:
            raise KeyError(key)
        return vw[ix].value

    def __setitem__(self, key, value):
        vw = self.vw
        ix = vw.find(key=key)
        if ix == -1:
            vw.append(key=key, value=value)
        else:
            vw[ix].value = value
        self._add_tran()

    def __delitem__(self, key):
        vw = self.vw
        ix = vw.find(key=key)
        if ix == -1:
            raise KeyError(key)
        vw.delete(ix)
        self._add_tran()

    def close(self):
        if self._closed: return
        if not self.read_only: self.db.commit()
        del self.db
        self._closed = 1

    def _add_tran(self):
        self._transcount = self._transcount + 1
        if self._transcount == self.trans_threshold:
            self._transcount = 0
            self.db.commit()


def open(file, flag, mode=0o666):
    return MKhash(file, flag, mode)
