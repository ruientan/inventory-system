"""HTML parsers"""


try:
    from html.parser import HTMLParser as _HTMLParser
    from html.entities import entitydefs
except ImportError:
    from HTMLParser import HTMLParser as _HTMLParser
    from htmlentitydefs import entitydefs


def join_attrs(attrs):
   attr_list = ['']
   for attrname, value in attrs:
      if value is None:
         attr_list.append('%s' % attrname)
      else:
         attr_list.append('%s="%s"' % (attrname, value.strip()))

   return ' '.join(attr_list)


class HTMLParser(_HTMLParser):


   def __init__(self):
      _HTMLParser.__init__(self)
      self.accumulator = ""


   def handle_starttag(self, tag, attrs):
      try:
         method = getattr(self, 'start_' + tag)
      except AttributeError:
         try:
            method = getattr(self, 'do_' + tag)
         except AttributeError:
            self.unknown_starttag(tag, attrs)
         else:
            method(attrs)
      else:
         method(attrs)

   def handle_endtag(self, tag):
      try:
         method = getattr(self, 'end_' + tag)
      except AttributeError:
         self.unknown_endtag(tag)
      else:
         method()


   def handle_data(self, data):
      if data:
         self.accumulator = "%s%s" % (self.accumulator, data)

   def handle_comment(self, data):
      if data:
         self.accumulator = "%s<!--%s-->" % (self.accumulator, data)


   def handle_charref(self, name):
      self.accumulator = "%s&#%s;" % (self.accumulator, name)

   def handle_entityref(self, name):
      if entitydefs.has_key(name): # If it is one of the standard SGML entities - close it with semicolon
         x = ';'
      else:
         x = ''
      self.accumulator = "%s&%s%s" % (self.accumulator, name, x)


   # Pass other tags unmodified
   def unknown_starttag(self, tag, attrs):
      self.accumulator = "%s<%s%s>" % (self.accumulator, tag, join_attrs(attrs))

   def unknown_endtag(self, tag):
      self.accumulator = "%s</%s>" % (self.accumulator, tag)


# Additional classes for filters

class _allowStartTag:
    def __init__(self, filter, tag):
        self.filter = filter
        self.tag = tag

    def __call__(self, attrs):
        filter = self.filter
        filter.accumulator = "%s<%s%s>" % (filter.accumulator, self.tag, join_attrs(attrs))

class _allowEndTag:
    def __init__(self, filter, tag):
        self.filter = filter
        self.tag = tag

    def __call__(self):
        filter = self.filter
        filter.accumulator = "%s</%s>" % (filter.accumulator, self.tag)


class HTMLFilter(HTMLParser):
   allowStartTagClass = _allowStartTag
   allowEndTagClass = _allowEndTag

   def handle_comment(self, data):
      pass

   # Filter out all tags
   def unknown_starttag(self, tag, attrs):
      pass

   def unknown_endtag(self, tag):
      pass


   def allow_startTag(self, tag):
      setattr(self, "start_%s" % tag, self.allowStartTagClass(self, tag))

   def allow_endTag(self, tag):
      setattr(self, "end_%s" % tag, self.allowEndTagClass(self, tag))


# how to use them:

#class DocHTMLFilter(HTMLFilter):
#    def __init__(self):
#        HTMLFilter.__init__(self)
#
#        # allow tags <table>, <tr>, <td>
#        # ... and closing tags
#
#        self.allow_startTag('table')
#        self.allow_endTag('table')
#
#        self.allow_startTag('tr')
#        self.allow_endTag('tr')
#
#        self.allow_startTag('td')
#        self.allow_endTag('td')

def filter_html(str, filter=None):
    "Process HTML using some HTML parser/filter"

    if filter is None:
       filter = HTMLFilter()

    filter.feed(str)
    return filter.accumulator
