"""Broytman FTP Library for Python"""


__all__ = [
   "ftpparse", "ftpscan", "TelnetFTP"
]


from ftplib import FTP
try:
    from telnetlib import IAC
except ImportError:  # Python 3.13+
    IAC  = bytes([255]) # "Interpret As Command"


class TelnetFTP(FTP):
    def putline(self, line):
        line = line.replace(IAC, IAC+IAC)
        FTP.putline(self, line)
