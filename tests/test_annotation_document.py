from anafora4python import annotation, raw_text, annotation_text
from bs4 import BeautifulSoup as soup
import re

thyme_directory = "/Users/ajwieme/verbs-projects/thyme/anaforaProjectFile/"
test = thyme_directory + 'THYMEColonFinal' + '/' + 'Test' + "/" + 'ID054_clinic_158/ID054_clinic_158.Temporal-RelationReGold.preannotation.completed.xml'
test_raw = thyme_directory + 'THYMEColonFinal' + '/' + 'Test' + "/" + 'ID054_clinic_158/ID054_clinic_158'

doc = annotation.Document(soup(open(test), "xml"), "ID054_clinic_158.Temporal-RelationReGold.preannotation.completed.xml")
raw = raw_text.Document(open(test_raw).read())
ann_text = annotation_text.Document(doc, raw)

print(ann_text.get_entity_text(doc.entities[20]))
print(doc.entities[20].type)

print(ann_text._get_sections())

