'''
Python classes for representing Anafora annotations
Expects a BeautifulSoup object from an XML document
'''

import re

class AbstractXML(object):
  '''
  Parent class for all objects that represent an XML
  '''
  def __init__(self, soup):
    self.soup = soup

  def get_attributes(self, cat, special_soup=None):
    if not special_soup:
      special_soup = self.soup
    try:
      return special_soup.get(cat).split()
    except AttributeError:
      return []

  def get_text_safe(self, soup):
    try:
      return soup.get_text()
    except:
      return ""

  def diff(self, other_xml):
    return {}

  def number_of_diffs(self, other_xml):
    return 0

  def update_soup(self):
    self.soup

  def pp(self):
    # remove \n in strings
    #line_break = re.compile(r'\n', re.MULTILINE)
    #return line_break.sub(r'', self.soup.prettify())
    xml = self.soup.prettify()
    xml = re.sub(r'>\n\s+([\w,_@\-\./\:\s]+)\n\s+<', r'>\1<', xml)
    xml = re.sub(r'<([\w]+)>\n\s+</([\w]+)', r'<\1></\2', xml)
    return xml


class Document(AbstractXML):
  def __init__(self, soup, filename):
    self.soup = soup
    self.filename = filename
    self.status = self.get_text_safe(self.soup.data.info.progress)
    self.savetime = self.get_text_safe(self.soup.data.info.savetime)
    #self.schema = Schema(self.soup.schema)
    self.entities_dict = {}
    self.entities = []
    self._populate_entities()
    self.relations = []
    self.tlinks = []
    self.identical_chains = []
    self.set_subsets = []
    self._populate_relations()

  def _populate_entities(self):
    """
    populates the entities attrbute: a list of all entity objects,
    and the entities_dict attr, a dict of {entity ID: rntity object}
    """
    for ent_soup in self.soup.annotations.find_all("entity"):
      ent = Entity(ent_soup)
      self.entities.append(ent)
      self.entities_dict[ent.id] = ent

  def _populate_relations(self):
    for relation_soup in self.soup.annotations.find_all("relation"):
      if self.get_text_safe(relation_soup.type).lower() == "tlink":
        tlink = Tlink(relation_soup, self)
        self.relations.append(tlink)
        self.tlinks.append(tlink)
      elif self.get_text_safe(relation_soup.type).lower() == "identical":
        ident = IdenticalChain(relation_soup, self)
        self.relations.append(ident)
        self.identical_chains.append(ident)
      elif self.get_text_safe(relation_soup.type).lower() == "set/subset":
        set_subset = SetSubset(relation_soup, self)
        self.relations.append(set_subset)
        self.set_subsets.append(set_subset)
      else:
        """
        For now, we are only using the Tlink class
        #TODO Add a class for each relation type, and instantiate them uniquely
        """
        self.relations.append(Relation(relation_soup, self))

  def entity_types(self):
    return list(set([entity.type for entity in self.entities]))

  def contains_span(self, span):
    """
    span: a tuple of start/end span for an annotation
    return: Boolean reflecting if that span is annotated
    """
    ann_spans = []
    # Add all spans, including multiple for a single, disjointed annotation
    # to one flat list
    ann_spans += [span for a in self.annotations() for span in a.spans]
    # Note this does not return true for overlapping spans
    for ann_span in ann_spans:
      start, end = span
      span_range = range(*ann_span)
      # Make the range include "end" by adding one more to it
      span_range_list = [s for s in span_range]
      span_range_list.append(span_range_list[-1]+1)

      if start in span_range_list and end in span_range_list:
        return True

    return False

  def get_annotations_by_span(self, span, doc_id=None):
    """
    Given a span (tuple of numbers),
    return all annotations within it's range
    """
    annotations = []

    start, end = span
    span_range = range(start, end)
    # Make the range include "end" by adding one more to it
    span_range_list = [s for s in span_range]
    span_range_list.append(span_range_list[-1] + 1)

    for ann in self.annotations():
      if doc_id is not None:
        if ann.get_doc_id() != doc_id:
          continue
      # Check entire 'spans' list to account for disjoint spans
      for span in ann.spans:
        start, end = span
        if start in span_range and end in span_range:
          annotations.append(ann)

    return annotations

  def property_names(self):
    '''
    This is just for entities for now
    '''
    return list(set([propname for entity in self.entities for propname in entity.property_names()]))

  def annotator(self):
    for entity in self.entities:
      # Find first entity that is not preannotated, and return that as it will ahve the name of the annotator
      if entity.id.split("@")[-1] != "gold":
        return entity.id.split("@")[-1]
    # If no entity id's have annotator name in them, return gold or empty string
    try:
      return self.entities[0].id.split("@")[-1]
    except:
      return ""

  def get_preannotated_entities(self):
    return [e for e in self.entities if e.preannotated()]

  def get_annotator_annotated_entities(self):
    return [e for e in self.entities if not e.preannotated()]

  def align_entities_with(self, other_document):
    '''
      Returns list of tuples where tuple[0] is an entity from document
      and tuple[1] is the aligned entity from other document.
      Where there is no alignment, the list will have None
      in the position of the document with no aligned entity
    '''
    aligned = []
    leftover_anns = []
    anns = self.annotations()[::]
    other_anns = other_document.annotations()[::]

    for i, ann in enumerate(anns):
      match = False
      for j, other_ann in enumerate(other_anns):
        if ann.is_aligned_with(other_ann):
          aligned.append((ann, other_ann))
          # These 2 are aligned, so safely remove annotation from other_anns
          other_anns.pop(j)
          match = True
          break
      if not match:
        leftover_anns.append(ann)

    # Add those with no alignment
    aligned += [(ann, None) for ann in leftover_anns]
    aligned += [(None, other_ann) for other_ann in other_anns] # Other anns will only have leftovers

    return aligned

  def annotations(self):
    '''
      Just entities for now, but relations can be added as that class is built out.
    '''
    return self.entities

  def max_annotation_id_integer(self):
    return max([int(i.string.split("@")[0]) for i in self.soup.find_all("id")])

  def get_entities(self):
    return self.entities

  def add_entity(self, annotator, _span, _type, _parentsType):
    docname = self.filename.split(".")[0]
    # id node
    id = self.soup.new_tag("id")
    id.string = "%s@e@%s@%s" % (self.max_annotation_id_integer() + 1, docname, annotator)

    span = self.soup.new_tag("span")
    span.string = "%s,%s" % _span

    type = self.soup.new_tag("type")
    type.string = _type

    parentsType = self.soup.new_tag("parentsType")
    parentsType.string = _parentsType

    properties = self.soup.new_tag("properties")

    new_ent = self.soup.new_tag("entity")
    new_ent.append(id)
    new_ent.append(span)
    new_ent.append(type)
    new_ent.append(parentsType)
    new_ent.append(properties)
    self.soup.annotations.append(new_ent)

    return new_ent

  def update_soup(self):
    '''
    Called in AbstractXml.pp()
    '''
    self.soup.data.info.progress.string = self.status
    self.soup.data.info.savetime.string = self.savetime
    for ent in self.entities:
      ent.update_soup()


class Schema(AbstractXML):
  '''
    Not sure if this is needed, this is Anafora-specific schema info
  '''
  def __init__(self, soup):
    self.soup = soup
    self.path = self.get_attributes("path", self.soup)[0]
    self.protocol = self.get_attributes("protocol", self.soup)[0]
    self.value = self.get_text_safe(self.soup)


class Relation(AbstractXML):
  '''
    A lot like entities, but with no spans
  '''
  def __init__(self, soup, doc):
    self.soup = soup
    self.document = doc
    self.id = self.get_text_safe(self.soup.id)
    self.type = self.get_text_safe(self.soup.type)
    self.parentsType = self.get_text_safe(self.soup.parentsType)
    # If the property does not have a value, we can treat it as not existing
    self.properties = self.properties()
    self.subtype = self._get_subtype()

  def properties(self):
    valued_props = []

    for c in self.soup.properties.children:
      prop = Property(c)
      if prop.name and prop.value:
        valued_props.append(prop)

    return valued_props

  def _get_subtype(self):
    return None

  def entity_ids(self):
    """
    Returns a list of every entity ID in the coref string
    This is a catch all, that should find coref string for any relation type
    NOTE beautifulSoup lowercases these string sautomatically?
    """
    names = ["firstinstance", "coreferring_string", "set", "subset", "whole", "part", "source", "target"]
    return [prop.value for prop in self.properties if prop.name in names]

  def entity_documents(self):
    """
    A list of unique document id's that the relation points to
    """
    return list(set([id.split("@")[2] for id in self.entity_ids()]))

  def single_doc(self):
    return len(self.entity_documents()) < 2

  def cross_doc(self):
    return len(self.entity_documents()) > 1

  def get_entities(self):
    """
    return: A list of the actual entity objects
    """
    return [self.document.entities_dict[e]for e in self.entity_ids()]

  def remove(self):
    """
    A relation is responsible for removing itself, because it means that we already have a handle
    on the XML node to be removed.
    Extracting the soup should modify the entire soup object,
    including what is pointed to by doc.soup, and ultimately output with AbstractXML.pp()
    """
    # This will return the soup that was removed
    return self.soup.extract()

class Tlink(Relation):
  def _get_subtype(self):
    return [prop.value for prop in self.properties if prop.name.lower() == "type"][0]

  """
  Tlinks, which are a type of relation
  """
  def source(self):
    """
    Just use the soup, there is only one source and this is faster
     than looping over property objects. Then lookup the entity in the dictionary
    """
    if self.get_text_safe(self.soup.properties.Source):
      return self.document.entities_dict.get(self.get_text_safe(self.soup.properties.Source))

  def target(self):
    """
    Just use the soup, there is only one source and this is faster
     than looping over property objects. Then lookup the entity in the dictionary
    """
    if self.get_text_safe(self.soup.properties.Target):
      return self.document.entities_dict.get(self.get_text_safe(self.soup.properties.Target))

  def entity_ids(self):
    """
    Returns a list of every entity ID in the coref string
    """
    names = ["Source", "Target"]
    return [prop.value for prop in self.properties if prop.name in names]

class IdenticalChain(Relation):
  """
  Identical chains, which are a type of relation
  """
  def entity_ids(self):
    """
    Returns a list of every entity ID in the coref string
    """
    names = ["firstinstance", "coreferring_string"]
    #print([(prop.value, prop.name) for prop in self.properties])
    return [prop.value for prop in self.properties if prop.name.lower() in names]

class SetSubset(Relation):
  """
  Set-Subset, which are a type of relation
  """
  def get_set(self):
    set_list = [prop.value for prop in self.properties if prop.name.lower() == "set"]
    return set_list[0] if set_list else None

  def get_subset(self):
    return [prop.value for prop in self.properties if prop.name.lower() == "subset"]

  def entity_ids(self):
    """
    Returns a list of every entity ID in the coref string
    """
    names = ["set", "subset"]

    return [prop.value for prop in self.properties if prop.name.lower() in names]


class Entity(AbstractXML):
  def __init__(self, soup):
    self.soup = soup
    self.id = self.get_text_safe(self.soup.id)
    self.span_string = self.get_text_safe(self.soup.span)
    self.spans = self._get_spans()
    self.type = self.get_text_safe(self.soup.type)
    self.parentsType = self.get_text_safe(self.soup.parentsType)
    # If the property does not have a value, we can treat it as not existing
    self.properties = self.properties()

  def _get_spans(self):
    spans = []

    text_spans = self.span_string.split(";")
    for text_span in text_spans:
      start = int(text_span.split(",")[0])
      end = int(text_span.split(",")[1])
      spans.append((start, end))

    return spans

  def get_doc_id(self):
    return self.id.split("@")[2]

  def is_disjointed(self):
    return ";" in self.span

  def start_span(self):
    return self.span.split(",")[0]

  def end_span(self):
    if self.is_disjointed():
      return self.span.split(",")[-1]
    else:
      return self.span.split(",")[1]

  def properties(self):
    valued_props = []

    for c in self.soup.properties.children:
      prop = Property(c)
      if prop.name and prop.value:
        valued_props.append(prop)

    return valued_props

  def property_names(self):
    return list(set([prop.name for prop in self.properties]))

  def is_aligned_with(self, other_entity):
    return self.span == other_entity.span

  def agrees_with(self, other_entity):
    return self.type == other_entity.type

  def preannotated(self):
    return self.id.endswith("@gold")

  def has_modality(self, modality):
    return len([p for p in self.properties if p.has_modality(modality)]) > 0

  def diff(self, other_entity):
    '''
    Returns a dict of {entity_sub_tag: [list of the two conflicting values]}
    '''
    other_entity_dict = dict(other_entity)
    diffs_dict = {}

    for attr, val in dict(self).items():
      if other_entity_dict[attr] and other_entity_dict[attr] == val:
          diffs_dict[attr] = [dict(self)[attr], other_entity_dict[attr]]

    return diffs_dict

  def align_properties_with(self, other_entity):
    aligned = []
    leftover_props = []
    props = self.properties[::]
    other_props = other_entity.properties[::]

    for i, prop in enumerate(props):
      match = False
      for j, other_prop in enumerate(other_props):
        if prop.is_aligned_with(other_prop):
          aligned.append((prop, other_prop))
          # These 2 are aligned, so safely remove annotation from other_anns
          other_props.pop(j)
          match = True
          break
      if not match:
        leftover_props.append(prop)

    # Add those with no alignment
    aligned += [(prop, None) for prop in leftover_props]
    aligned += [(None, other_prop) for other_prop in other_props]  # Other properties will only have leftovers

    return aligned

  def update_soup(self):
    self.soup.id.string = self.id
    self.soup.span.string = self.span
    self.soup.type.string = self.type
    self.soup.parentsType.string = self.parentsType


class Property(AbstractXML):
  def __init__(self, soup):
    self.soup = soup
    self.name = self.soup.name
    self.value = self.get_text_safe(self.soup)

  def has_modality(self, modality):
    return self.name.lower() == "contextualmodality" and self.value.lower() == modality.lower()

  def is_aligned_with(self, other_prop):
    return self.name == other_prop.name and self.value and other_prop.value

  def agrees_with(self, other_prop):
    return self.name == other_prop.name and self.value == other_prop.value

