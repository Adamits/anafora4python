import re

class Document(object):
  def __init__(self, text, name=""):
    self.text = text
    self.tokens = []
    self.name = name

  def find_string_by_span(self, span):
    """
    Expects a tuple of (start_span, end_span) and finds the string at that span
    """
    if not span: return None

    if type(span) == str:
      span = span.split(",")

    if type(span[0]) == str:
      span[0] = int(span[0])

    if type(span[1]) == str:
      span[1] = int(span[1])

    return self.text[span[0]:span[1]]

  def find_spans_by_string(self, string):
    """
    Expects a string, and finds the corresponding span
    """
    matches = [x for x in re.finditer(string, self.text)]
    #for m in matches:
    #  x = len([c for c in self.text[m.start(), m.end()] if not c.isalpha()])
    return [(m.start(), m.end()) for m in matches]

  def find_spans_in_between(self, start_string, end_string):
    """
    Expects a string, and finds the corresponding span
    """
    matches = [x for x in re.finditer(r'(%s)(.|\n)*?(%s)' % (start_string, end_string), self.text)]
    return [(m.start(), m.end()) for m in matches]

  def find_spans_by_regex(self, regex):
    matches = [x for x in re.finditer(regex, self.text)]
    return [(m.start(), m.end()) for m in matches]

  def find_spans_and_strings_by_regex(self, regex):
    matches = [x for x in re.finditer(regex, self.text)]
    return [(m.start(), m.end(), m.group(0)) for m in matches]
