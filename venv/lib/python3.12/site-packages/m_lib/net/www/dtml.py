"""DTML utilities"""

class standard_html: # Base class for using with ZTemplates
   def __init__(self, title):
      self.standard_html_header = """<HTML>
   <HEAD>
      <TITLE>
         %s
      </TITLE>
   </HEAD>

<BODY>""" % title

      self.standard_html_footer = """</BODY>
</HTML>"""

      self.title = title
