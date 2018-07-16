import annotation
import raw_text
from bs4 import BeautifulSoup as soup
import re
test = "/Users/ajwieme/verbs-projects/thyme/anaforaProjectFile/Cross-THYMEColonFinal/Dev/ID028/ID028.Thyme2v1-Correction.haco1069.completed.xml"

doc = annotation.Document(soup(open(test), "lxml"), "ID028.Thyme2v1-Correction.haco1069.completed.xml")

print("Getting all relations..")
print([r.id for r in doc.get_all_relations()])
print([r.is_cross_doc() for r in doc.get_all_relations()])
print("Getting all Tlinks...")
print([r.id for r in doc.get_tlinks()])
print("Getting all CONS-SUB...")
print([r.id for r in doc.get_contains_subevent_tlinks()])
print("Getting all IDENT...")
print([r.id for r in doc.get_identical_chains()])
print("Getting all Set/Subset...")
print([r.id for r in doc.get_set_subsets()])
