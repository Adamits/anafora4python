import annotation
import raw_text
from bs4 import BeautifulSoup as soup
import re
test = "/Users/ajwieme/verbs-projects/thyme/anaforaProjectFile/Cross-THYMEColonFinal/Dev/ID028/ID028.Thyme2v1-Correction.haco1069.completed.xml"

doc = annotation.Document(soup(open(test), "lxml"), "ID028.Thyme2v1-Correction.haco1069.completed.xml")
'''
for rel in doc.relations:
  print(rel.id)
  print(rel.type)
'''
for rel in doc.relations:
  if rel.cross_doc():
    print("CROSS")
    print(rel.type)
    print(rel.id)
    print(len(rel.entity_ids()))
    print(rel.entity_ids())