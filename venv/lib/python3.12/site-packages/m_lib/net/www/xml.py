"""XML parsers"""


import re, xmllib
illegal = re.compile('[^\t\r\n -\377]') # illegal chars in content
xmllib.illegal = illegal # allow cyrillic characters in XML


def join_xml_attrs(attrs):
   attr_list = ['']
   for attrname, value in attrs.items():
      attr_list.append('%s="%s"' % (attrname, string.strip(value)))

   return string.join(attr_list, " ")


class XMLParser(xmllib.XMLParser):
   def __init__(self):
      xmllib.XMLParser.__init__(self)
      self.accumulator = ""


   def handle_data(self, data):
      if data:
         self.accumulator = "%s%s" % (self.accumulator, data)

   def handle_comment(self, data):
      if data:
         self.accumulator = "%s<!--%s-->" % (self.accumulator, data)


   # Pass other tags unmodified
   def unknown_starttag(self, tag, attrs):
      self.accumulator = "%s<%s%s>" % (self.accumulator, tag, join_xml_attrs(attrs))

   def unknown_endtag(self, tag):
      self.accumulator = "%s</%s>" % (self.accumulator, tag)


class XMLFilter(XMLParser):
   def handle_comment(self, data):
      pass

   # Filter out all tags
   def unknown_starttag(self, tag, attrs):
      pass

   def unknown_endtag(self, tag):
      pass

def filter_xml(str, filter=None):
    "Process XML using some XML parser/filter"

    if filter is None:
       filter = XMLFilter()

    filter.feed(str)
    return filter.accumulator
