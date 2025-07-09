"""url_lib"""


from urllib import FancyURLopener

class NoAsk_URLopener(FancyURLopener):
   "URL opener that does not ask for a password interactively"

   def __init__(self, username, password):
      FancyURLopener.__init__(self)

      self.username = username
      self.password = password
      self._asked = 0

   def prompt_user_passwd(self, host, realm):
      if self._asked:
         return None, None

      self._asked = 1
      return self.username, self.password
