from bs4 import BeautifulSoup as soup
from collections import defaultdict as dd
import annotation

def get_entity_agreement_by_type(doc1, doc2):
  types_dict = {type: {"agree": 0, "total": 0} for type in set(doc1.entity_types() + doc2.entity_types())}
  #diffs = doc1.get_diff(doc2)
  aligned = doc1.align_entities_with(doc2)

  # With this logic, every entity adds +1 to its type count
  # every agreement will then add +2 to type count,
  # and therefore also adds +2 to agreement count
  for entity1, entity2 in aligned:
    if entity1:
      types_dict[entity1.type]["total"] += 1
      if entity2 and entity1.agrees_with(entity2):
        types_dict[entity1.type]["agree"] += 1
    if entity2:
      types_dict[entity2.type]["total"] += 1
      if entity1 and entity2.agrees_with(entity1):
        types_dict[entity2.type]["agree"] += 1
  return types_dict

def get_property_agreement_by_name(doc1, doc2):
  properties_dict = {name: {"agree": 0, "total": 0} for name in set(doc1.property_names() + doc2.property_names())}
  aligned_entities = doc1.align_entities_with(doc2)

  for entity1, entity2 in aligned_entities:
    if entity1.properties and entity2.properties:
      aligned_props = entity1.align_properties_with(entity2)

      for prop1, prop2 in aligned_props:
        if prop1:
          properties_dict[prop1.name]["total"] += 1
          if prop2 and prop1.agrees_with(prop2):
            properties_dict[prop1.name]["agree"] += 1
        if prop2:
          properties_dict[prop2.name]["total"] += 1
          if prop1 and prop2.agrees_with(prop1):
            properties_dict[prop2.name]["agree"] += 1
    elif entity1.properties:
      for prop in entity1.properties:
        properties_dict[prop.name]["total"] += 1
    elif entity2.properties:
      for prop in entity2.properties:
        properties_dict[prop.name]["total"] += 1

  return properties_dict
