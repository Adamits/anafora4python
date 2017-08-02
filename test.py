import annotation
import raw_text
from bs4 import BeautifulSoup as soup
import re
thyme_directory = "/Users/ajwieme/verbs-projects/thyme/anaforaProjectFile/"

test = thyme_directory + 'THYMEColonFinal' + '/' + 'Test' + "/" + 'ID054_clinic_158/ID054_clinic_158.Temporal-RelationReGold.preannotation.completed.xml'
test_raw = thyme_directory + 'THYMEColonFinal' + '/' + 'Test' + "/" + 'ID054_clinic_158/ID054_clinic_158'

doc = annotation.Document(soup(open(test), "lxml"))
r = raw_text.Document("".join([l for l in open(test_raw)]))
print(r.find_spans_by_string(re.compile('Mrs\. Camara and her son the evaluation of rectal cancer\.  We will')))
#print(r.find_spans_in_between('ADVANCE DIRECTIVES\n', '(\[end section|PATIENT EDUCATION|ADVANCE DIRECTIVES\n)'))
print(r.find_string_by_span((388, 453)))
#print([(e.span, e.type, e.start_span(), e.end_span())for e in doc.entities])
"""
for e in doc.entities:
  print(e.start_span())
  print(e.end_span())
"""