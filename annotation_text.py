"""
This class will describe the interface between between annotated data, and the raw
text that it annotates
"""

from anafora4python import raw_text
from anafora4python import annotation
import re

class Document(object):

  def __init__(self, annotation, raw):
    self.annotation = annotation
    self.raw = raw
    self.sections = self._get_sections()

  def find_text_spans_by_regex(self, regex):
    """
    Searches all sections for the regex, and returns text spans that match it
    """
    text_spans = []
    for section in self.sections:
      text_spans += section.find_text_spans_by_regex(regex)

    return text_spans

  def find_text_spans_by_span(self, span):
    """
    Searches all sections for the span, and returns text spans within that span
    """
    text_spans = []
    for section in self.sections:
      # If the section is farther into the text than the end of the text span,
      # then this should stop checking
      if section.start_span > span[1]:
        return text_spans
      else:
        text_spans += section.find_text_spans_by_span(span)

    return text_spans

  def get_sections_by_regex(self, regex):
    """
    Return the list of Sections whose text matches the given regex
    """
    sections = []

    for section in self.sections:
      if section.has_regex(regex):
        sections.append(section)

    return sections

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
    sections = []

    section_spans = self.raw.find_spans_in_between('\[start section id=', '\[end section id=')
    for section_span in section_spans:
      # Get the entire text
      text = self.raw.find_string_by_span(section_span)
      # Split into lines
      lines = text.split("\n")
      # Use the first line to find the id for that section
      id = re.search("\[start section id=\"(.*)\"",lines[0]).group(1)
      # rejoin the lines, removing first and last line ([start section] and [end section])
      text = ("\n").join(lines[1:-1])
      start, end = section_span
      sections.append(Section(self, id, start, end, text))

    return sections

  def get_entity_text(self, entity):
    if type(entity) == annotation.Entity:
      """
      Entity object, defined by the annotation itself
      """
      return " ".join([self.raw.find_string_by_span(span) for span in entity.spans])
    elif type(entity) == tuple:
      """
      Span argument
      """
      return self.raw.find_string_by_span(span)

    else:
      raise Exception("get_entity_text takes either a tuple, representing the span, or an Entity object from the annotation module")

class Section(object):
  def __init__(self, document, id, start_span, end_span, text):
    self.document = document
    self.start_span = start_span
    self.end_span = end_span
    self.text = text
    self.id = id

  def find_text_spans_by_regex(self, regex):
    """
    Searches all text spans in the section, and if its text matches the given regex, returns it in a List
    """
    section_span_range = range(self.start_span, self.end_span)
    text_spans = self.document.raw.find_spans_and_strings_by_regex(regex)
    return [TextSpan(start_span, end_span, text, section=self) for start_span, end_span, text in text_spans if start_span in section_span_range and end_span in section_span_range]

  def find_text_spans_by_span(self, span):
    start, end = span
    section_span_range = range(self.start_span, self.end_span)
    if start in section_span_range and end in section_span_range:
      text = self.document.raw.find_string_by_span(span)
      return TextSpan(start, end, text, section=self)

  def has_regex(self, regex):
    match = re.match(regex, self.text)
    if match == None:
      return True
    else:
      return False

class TextSpan(object):
  def __init__(self, start, end, text, section=None):
    self.section = section
    self.text = text
    self.start = start
    self.end = end
    self.span = (self.start, self.end)

  def is_annotation(self):
    return self.section.document.annotation.annotation.contains_span(self.span)

  def get_annotations(self, doc_id):
    return self.section.document.annotation.get_annotations_by_span(self.span, doc_id=doc_id)

  def truncate_end(self, trunc):
    """
    Truncates from the first instance of str to the end of the text
    """
    if type(trunc) == int:
      index = trunc
    elif type(trunc) == str:
      index = self.text.find(trunc)
      if index == -1:
        return None
    self.end = self.end - (len(self.text) - index)
    self.text = self.text[:index]
    self._reset_span()

  def truncate_begin(self, trunc):
    """
    Truncates from the first instance of str to the beginning of the text
    """
    if type(trunc) == int:
      index = trunc
    elif type(trunc) == str:
      index = self.text.find(trunc)
      if index == -1:
        return None
      else:
        # Get index of last char in the match
        index = index + len(trunc)

    self.text = self.text[index:]
    self.start = self.start + index
    self._reset_span()

  def _reset_span(self):
    self.span = (self.start, self.end)
