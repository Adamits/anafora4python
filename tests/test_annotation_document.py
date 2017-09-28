from anafora4python import annotation, raw_text, annotation_text
from bs4 import BeautifulSoup as soup
import re

thyme_directory = "/Users/ajwieme/verbs-projects/thyme/anaforaProjectFile/"
test = thyme_directory + 'THYMEColonFinal' + '/' + 'Test' + "/" + 'ID054_clinic_158/ID054_clinic_158.Temporal-RelationReGold.preannotation.completed.xml'
test_raw = thyme_directory + 'THYMEColonFinal' + '/' + 'Test' + "/" + 'ID054_clinic_158/ID054_clinic_158'

doc = annotation.Document(soup(open(test), "xml"), "ID054_clinic_158.Temporal-RelationReGold.preannotation.completed.xml")
raw = raw_text.Document(open(test_raw).read())
ann_text = annotation_text.Document(doc, raw)

section = ann_text.get_section("20105")
r = re.compile("Radiology :")
other_r = re.compile("\*\*MORE THAN 10 ALLERGIES EXIST\*\*")

for text_span in section.find_text_spans_by_regex(r):
  print(text_span.text, text_span.span)
  text_span.truncate_end(" :")
  print(text_span.text, text_span.span)
  print(raw.find_string_by_span(text_span.span))

for text_span in section.find_text_spans_by_regex(other_r):
  print(text_span.text, text_span.span)
  text_span.truncate_begin("**")
  print(text_span.text, text_span.span)
  print(raw.find_string_by_span(text_span.span))


