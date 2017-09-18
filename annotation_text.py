"""
This class will describe the interface between between annotated data, and the raw
text that it annotates
"""

from anafora4python import raw_text
import re

class Document(object):

  def __init__(self, annotation, raw):
    self.annotation = annotation
    self.raw = raw
    #self.sections = _get_sections()

  def has_section(self, section_id):
    if self.raw.find_spans_by_string('section id="%s"' % section_id):
      return True

  def get_section(self, section_id):
    """
    Search the raw text by regex for the section id as a 'start section' and an 'end section',
    and get the resulting start and end spans
    """
    # Sections are unique so we can take first match tuple returned by the method
    section = self.raw.find_spans_by_regex('start section id=\"%s\"(.|\n)*?(\[end section id=\"%s\")' % (section_id, section_id))
    if section:
      span = section[0]
      text = self.raw.find_string_by_span(span)

      start, end = span
      return Section(self, section_id, start, end, text)

  def _get_sections(self):
    return []

class Section(object):
  def __init__(self, document, id, start_span, end_span, text):
    self.document = document
    self.start_span = start_span
    self.end_span = end_span
    self.text = text
    self.id = id

  def find_text_spans_by_regex(self, regex):
    section_span_range = range(self.start_span, self.end_span)
    text_spans = self.document.raw.find_spans_and_strings_by_regex(regex)
    return [TextSpan(self, start_span, end_span, text) for start_span, end_span, text in text_spans if start_span in section_span_range and end_span in section_span_range]

class TextSpan(object):
  def __init__(self, section, start, end, text):
    self.section = section
    self.text = text
    self.start = start
    self.end = end

  def truncate(self, str):
    """
    Truncates from the first instance of str
    """
    index = self.text.find(str)
    self.text = self.text[:index]
    self.end = self.end - len(self.text) - index + 1
