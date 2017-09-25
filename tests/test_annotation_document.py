from anafora4python import annotation
from bs4 import BeautifulSoup as soup

thyme_directory = "/Users/ajwieme/verbs-projects/thyme/anaforaProjectFile/"
test = thyme_directory + 'THYMEColonFinal' + '/' + 'Test' + "/" + 'ID054_clinic_158/ID054_clinic_158.Temporal-RelationReGold.preannotation.completed.xml'

doc = annotation.Document(soup(open(test), "xml"), "ID054_clinic_158.Temporal-RelationReGold.preannotation.completed.xml")
print(doc.max_annotation_id_integer())

doc.add_entity("gold", (20, 30), "Markable", "TemporalEntities")

print(doc.pp())