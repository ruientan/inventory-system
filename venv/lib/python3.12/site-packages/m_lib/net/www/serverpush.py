"""Server Push"""


import sys, mimetools

class ServerPush:
   def __init__(self, out=sys.stdout):
      self.out = out
      self.output = out.write
      self.boundary = mimetools.choose_boundary()


   def start(self):
      self.output("""\
Content-type: multipart/x-mixed-replace;boundary=%s

""" % self.boundary)


   def next(self, content_type="text/html"):
      self.output("""\
--%s
Content-type: %s
""" % (self.boundary, content_type))


   def stop(self):
      self.output("--%s--" % self.boundary)
