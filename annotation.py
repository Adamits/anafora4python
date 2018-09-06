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
    pass

  def pp(self):
    # remove \n in strings
    #line_break = re.compile(r'\n', re.MULTILINE)
    #return line_break.sub(r'', self.soup.prettify())
    xml = self.soup.prettify()
    xml = re.sub(r'>\n\s+([\w,_@\-\./\:\s]+)\n\s+<', r'>\1<', xml)
    xml = re.sub(r'<([\w]+)>\n\s+</([\w]+)', r'<\1></\2', xml)
    return xml

class Annotation(AbstractXML):
  def remove(self):
    """
    An annotation is responsible for removing itself, because it means that we already have a handle
    on the XML node to be removed.
    Extracting the soup should modify the entire soup object,
    including what is pointed to by doc.soup, and ultimately output with AbstractXML.pp()
    """
    # This will return the soup that was removed
    return self.soup.extract()


class Document(AbstractXML):
  def __init__(self, soup, filename):
    super(Document, self).__init__(soup)
    self.filename = filename
    self.status = self.get_text_safe(self.soup.data.info.progress)
    self.savetime = self.get_text_safe(self.soup.data.info.savetime)
    #self.schema = Schema(self.soup.schema)
    self.entities_dict = {}
    self._populate_entities()

  def _populate_entities(self):
    """
    populates the entities attrbute: a list of all entity objects,
    and the entities_dict attr, a dict of {entity ID: entity object}
    """
    for ent_soup in self.soup.annotations.find_all("entity"):
      ent = Entity(ent_soup)
      self.entities_dict[ent.id] = ent

  def get_entities(self):
    """
    Return: a list of all entities in the Document
    """
    return list(self.entities_dict.values())

  def get_sorted_entity_ids(self):
    """
    Return: a list of all entity ids in the Document from lowest to highest int
    """
    return list(sorted(self.entities_dict.keys()))

  def get_tlinks(self):
    """
    Return: A list of Tlink objects for all Tlinks in the document.

    This traverses the beautiful soup structure each time it is called.
    """
    tlink_soups = self.soup.annotations.find_all('type',\
                   text='TLINK')
    tlink_soups = tlink_soups if tlink_soups else []

    return [Tlink(tlink_soup.find_parent('relation'), self)\
             for tlink_soup in tlink_soups]

  def get_contains_subevent_tlinks(self):
    """
    Return: A list of ContainsSubevent objects for all
     CONTAINS-SUBEVENT Tlinks in the document.

    This traverses the beautiful soup structure each time it is called.
    """
    cons_sub_soups = self.soup.annotations.find_all('Type',\
                      text='CONTAINS-SUBEVENT')
    cons_sub_soups = cons_sub_soups if cons_sub_soups else []

    return [ContainsSubevent(cons_sub_soup.find_parent('relation'), self)\
            for cons_sub_soup in cons_sub_soups]

  def get_cross_doc_contains_subevent_tlinks(self):
    """
    Return: A list of ContainsSubevent objects for all
     CONTAINS-SUBEVENT Tlinks in the document that are cross-doc.

    This traverses the beautiful soup structure each time it is called.
    """

    return [con_sub for con_sub in self.get_contains_subevent_tlinks if con_sub.is_cross_doc()]

  def get_identical_chains(self):
    """
    Return: A list of IdenticalChain objects for all
     Identical relations in the document.

    This traverses the beautiful soup structure each time it is called.
    """
    ident_soups = self.soup.annotations.find_all('type',\
                   text='Identical')
    ident_soups = ident_soups if ident_soups else []

    return[IdenticalChain(ident_soup.find_parent('relation'), self)\
           for ident_soup in ident_soups]

  def get_set_subsets(self):
    """
    Return: A list of SetSubset objects for all
     Set/Subset relations in the document.

    This traverses the beautiful soup structure each time it is called.
    """
    s_ss_soups = self.soup.annotations.find_all('type',\
                   text='Set/Subset')
    s_ss_soups = s_ss_soups if s_ss_soups else []

    return [SetSubset(s_ss_soup.find_parent('relation'), self)\
             for s_ss_soup in s_ss_soups]

  def get_whole_parts(self):
    """
    Return: A list of WholePart objects for all
     Whole/Part relations in the document.

    This traverses the beautiful soup structure each time it is called.
    """
    w_p_soups = self.soup.annotations.find_all('type', text='Whole/Part')
    w_p_soups = w_p_soups if w_p_soups else []

    return [WholePart(w_p_soup.find_parent('relation'), self) \
            for w_p_soup in w_p_soups]

  def get_all_relations(self):
    """
    Return all relations of any type

    This traverses the beautiful soup structure each time it is called.
    """
    return [Relation(rel_soup, self) for rel_soup in\
            self.soup.annotations.find_all("relation")]

  def get_single_doc_idents(self):
    return [ident for ident in self.get_identical_chains() if ident.single_doc()]

  def entity_types(self):
    return list(set([entity.type for entity in self.get_entities()]))

  def contains_span(self, span):
    """
    span: a tuple of start/end span for an annotation
    return: Boolean reflecting if that span is annotated
    """
    ann_spans = []
    # Add all spans, including multiple for a single, disjointed annotation
    # to one flat list
    ann_spans += [span for a in self.get_annotations() for span in a.spans]
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
    span_range = range(int(start), int(end)+1)

    for ann in self.get_annotations():
      if doc_id is not None:
        if ann.get_doc_id() != doc_id:
          continue
      # Check entire 'spans' list to account for disjoint spans
      for span in ann.spans:
        start, end = span
        if start in span_range and end in span_range:
          annotations.append(ann)

    return annotations

  def get_tlinks_by_span(self, span, doc_id):
    """
    Given a span (tuple of numbers),
    return all Tlinks within it's range
    """
    #TODO pretty sure this looks unfinished...
    ids = [ann.id for ann in self.get_annotations()]
    # Iterate over tlinks, and return the ones that have a source or target in ids
    return [tlink for tlink in self.get_tlinks() if any(set(tlink.entity_ids()).intersection(set(ids)))]

  def property_names(self):
    '''
    This is just for entities for now
    '''
    return list(set([propname for entity in self.get_entities() for propname in entity.property_names()]))

  def annotator(self):
    for entity in self.get_entities():
      # Find first entity that is not preannotated, and return that as it will ahve the name of the annotator
      if entity.id.split("@")[-1] != "gold":
        return entity.id.split("@")[-1]
    # If no entity id's have annotator name in them, return gold or empty string
    try:
      return self.get_entities()[0].id.split("@")[-1]
    except:
      return ""

  def get_preannotated_entities(self):
    return [e for e in self.get_entities() if e.preannotated()]

  def get_annotator_annotated_entities(self):
    return [e for e in self.get_entities() if not e.preannotated()]

  def align_entities_with(self, other_document):
    """
    Returns list of tuples where tuple[0] is an entity from document
    and tuple[1] is the aligned entity from other document.
    Where there is no alignment, the list will have None
    in the position of the document with no aligned entity
    """
    aligned = []
    leftover_anns = []
    anns = self.get_annotations()[::]
    other_anns = other_document.get_annotations()[::]

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

  def get_annotations(self):
    """
    Just entities for now, but relations can be added as that class is built out.
    """
    return self.get_entities()

  def max_entity_id_integer(self):
    """
    returns the highest id on any entity in the document
    """
    return max([int(ent.id.split("@")[0]) for ent in self.get_entities()])

  def max_relation_id_integer(self):
    """
    returns the highest id on any relation in the document
    """
    return max([int(rel.id.split("@")[0]) for rel in self.get_all_relations()])

  def get_contains_subevent_tuples(self):
    """
    returns a list of tuples of the form:
    (source entity id, target entity id)
    for all cons-sub relations in the document
    """
    return [cons_sub.entity_tuple for cons_sub in self.get_contains_subevent_tlinks()]

  def add_entity(self, annotator, _span, _type, _parentsType):
    #TODO need to investigate if this is incorrect in the case of a cross-doc file, which will have a simpler docname
    docname = self.filename.split(".")[0]
    # id node
    id = self.soup.new_tag("id")
    id.string = "%s@e@%s@%s" % (self.max_entity_id_integer() + 1, docname, annotator)

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
    # Add to document
    ent_obj = Entity(new_ent)
    self.entities_dict[ent_obj.id] = ent_obj

    return new_ent

  def add_tlink(self, _source_id, _target_id, _parentsType, _subtype):
    # Crossdoc/single doc distinction
    if _source_id.split("@")[2] == _target_id.split("@")[2]:
      docname = _source_id.split("@")[2]
    else:
      docname = self.filename.split(".")[0]

    # id node
    id = self.soup.new_tag("id")
    id.string = "%s@r@%s@%s" % (self.max_relation_id_integer() + 1, docname, self.annotator())

    type = self.soup.new_tag("type")
    type.string = "TLINK"

    parentsType = self.soup.new_tag("parentsType")
    parentsType.string = _parentsType

    properties = self.soup.new_tag("properties")

    source = self.soup.new_tag("Source")
    source.string = _source_id
    properties.append(source)

    subtype = self.soup.new_tag("Type")
    subtype.string = _subtype
    properties.append(subtype)

    target = self.soup.new_tag("Target")
    target.string = _target_id
    properties.append(target)

    nmo = self.soup.new_tag("Needs_Medical_Opinion")
    nmo.string = "FALSE"
    properties.append(nmo)

    new_rel = self.soup.new_tag("relation")
    new_rel.append(id)
    new_rel.append(type)
    new_rel.append(parentsType)
    new_rel.append(properties)
    self.soup.annotations.append(new_rel)
    # Add to document
    rel_obj = Relation(new_rel, self)
    self.get_tlinks().append(rel_obj)

    return new_rel

  def update_soup(self):
    '''
    Called in AbstractXml.pp()
    '''
    self.soup.data.info.progress.string = self.status
    self.soup.data.info.savetime.string = self.savetime
    for ent in self.get_entities():
      ent.update_soup()

    for rel in self.get_all_relations():
      rel.update_soup()


class Schema(AbstractXML):
  '''
    Not sure if this is needed, this is Anafora-specific schema info
  '''
  def __init__(self, soup):
    super(Schema, self).__init__(soup)
    self.path = self.get_attributes("path", self.soup)[0]
    self.protocol = self.get_attributes("protocol", self.soup)[0]
    self.value = self.get_text_safe(self.soup)


class Relation(Annotation):
  """
  A lot like entities, but with no spans
  """
  def __init__(self, soup, doc):
    super(Relation, self).__init__(soup)
    self.document = doc
    self.id = self.get_text_safe(self.soup.id)
    self.id_num = self.id.split("@")[0]
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
    *** NOTE beautifulSoup lowercases these strings automatically? ***
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

  def is_cross_doc(self):
    return len(self.entity_documents()) > 1

  def get_entities(self):
    """
    return: A list of the actual entity objects
    """
    return [self.document.entities_dict[e] for e in self.entity_ids()]

  def identical_entities_with(self, other):
    """
    Takes another relation, of any type, and returns True if
    the two have the exact same set of entities that they relate

    NOTE maybe not the most pythonic, but easier for debugging right now...
    """
    if isinstance(other, Relation) or issubclass(type(other), Relation):
      """
      Check type, in order to throw more readable error
      """
      if sorted(self.entity_ids()) == sorted(other.entity_ids()):
        return True
      else:
        return False
    else:
      raise Exception("Relation.identical_entities_with(other) requires that other also be a Relation, not a %s" % type(other))

  def update_soup(self):
    self.soup.id.string = self.id
    self.soup.type.string = self.type
    self.soup.parentsType.string = self.parentsType
    for prop in self.properties:
      prop.update_soup()

  def get_head(self):
    return None

  def get_tail(self):
    return []

  def has_empty_args(self):
    """
    Return: Boolean as to whether the source or target are None
    """
    return None in [self.get_head()] + self.get_tail()


class Tlink(Relation):
  """
  Tlinks, which are a type of relation
  """
  def _get_subtype(self):
    return [prop.value for prop in self.properties if prop.name.lower() == "type"][0]

  def update_subtype(self, subtype):
    """
    Change the subtype ('type' in the set of properties) to the given input
    """
    for prop in self.properties:
      if prop.name.lower() == "type":
        prop.value = subtype
        break

  def get_source(self):
    """
    Just use the soup, there is only one source and this is faster
    than looping over property objects. Then lookup the entity in the dictionary

    return the actual Entity object that source points to
    """
    if self.get_text_safe(self.soup.properties.Source):
      return self.document.entities_dict.get(self.get_text_safe(self.soup.properties.Source))

  def get_target(self):
    """
    Just use the soup, there is only one source and this is faster
    than looping over property objects. Then lookup the entity in the dictionary

    return the actual Entity object that target points to
    """
    if self.get_text_safe(self.soup.properties.Target):
      return self.document.entities_dict.get(self.get_text_safe(self.soup.properties.Target))

  def entity_ids(self):
    """
    Returns a list of every entity ID in the coref string
    """
    names = ["Source", "Target"]
    return [prop.value for prop in self.properties if prop.name in names]

  def get_head(self):
    """
    Generalizable mask for get_source()
    """
    return self.get_source()

  def get_tail(self):
    """
    Generalizable mask for get_target()

    returns: List
    """
    return [self.get_target()]

class ContainsSubevent(Tlink):
  """
  Contains Subevent, which are of type Tlink
  """
  def __eq__(self, other):
    """
    Check if 2 con-sub are equivalent.

    i.e. do they have exactly the same source and target
    according to the numerical id's on the entities
    """
    return self.get_source().id_doc_num == other.get_source().id_doc_num and self.get_target().id_doc_num == other.get_target().id_doc_num

  def entity_tuple(self):
    """
    Returns a typle of (source, target) entity id's
    """
    return (self.get_source(), self.get_target())

  def has_empty_args(self):
    """
    Return: Boolean as to whether the source or target are None
    """
    return None in [self.get_source(), self.get_target()]


class IdenticalChain(Relation):
  """
  Identical chains, which are a type of relation
  """
  def __eq__(self, other):
    """
    Check if 2 ident are equivalent.

    i.e. does other have exactly the same numerical entity id's
    as self
    """
    return set(self.entity_id_doc_nums()) == set(other.entity_id_doc_nums())

  def get_first_instance(self):
    """
    Just use the soup, there is only one FirstInstance and this is faster
    than looping over property objects. Then lookup the entity in the dictionary

    return the actual Entity object that FirstInstance points to
    """
    if self.get_text_safe(self.soup.properties.FirstInstance):
      return self.document.entities_dict.get(self.get_text_safe(self.soup.properties.FirstInstance))

  def get_coref_strings(self):
    """
    Just use the soup, there is only one source and this is faster
    than looping over property objects. Then lookup the entity in the dictionary

    return the actual Entity object that source points to
    """
    if self.soup.find_all("Coreferring_String") is not None:
      c_strings = [self.get_text_safe(c) for c in self.soup.findAll("Coreferring_String")]
      return [self.document.entities_dict.get(c) for c in c_strings]

  def entity_ids(self):
    """
    Returns a list of every entity ID in the coref string
    """
    names = ["firstinstance", "coreferring_string"]
    #print([(prop.value, prop.name) for prop in self.properties])
    return [prop.value for prop in self.properties if prop.name.lower() in names]

  def entity_id_nums(self):
    """
    Returns a list of every entity ID in the coref string
    """
    names = ["firstinstance", "coreferring_string"]
    # print([(prop.value, prop.name) for prop in self.properties])
    return [prop.value.split("@")[0] for prop in self.properties if prop.name.lower() in names]

  def entity_id_nums(self):
    """
    Returns a list of every entity ID@doc_id in the coref string
    """
    names = ["firstinstance", "coreferring_string"]
    return [prop.value.split("@")[0] + "@" + prop.value.split("@")[3] for prop in self.properties if prop.name.lower() in names]

  def get_head(self):
    """
    Generalizable mask for get_first_instance()
    """
    return self.get_first_instance()

  def get_tail(self):
    """
    Generalizable mask for get_coref_strings()
    """
    return self.get_coref_strings()

class SetSubset(Relation):
  """
  Set-Subset, which are a type of relation
  """
  def __eq__(self, other):
    """
    Check if 2 set-subset are equivalent.

    i.e. does other have exactly the same numerical entity id for Set
    as well as for all Subset entities
    """
    if self.get_set().id_doc_num == other.get_set().id_doc_num:
      return set([e.id_doc_num for e in self.get_subset()]) == set([e.id_doc_num for e in other.get_subset()])

  def get_set(self):
    if self.get_text_safe(self.soup.properties.Set):
      return self.document.entities_dict.get(self.get_text_safe(self.soup.properties.Set))

  def get_subset(self):
    if self.soup.find_all("Subset") is not None:
      ss_strings = [self.get_text_safe(c) for c in self.soup.findAll("Subset")]
      return [self.document.entities_dict.get(c) for c in ss_strings]

  def entity_ids(self):
    """
    Returns a list of every entity ID in the coref string
    """
    names = ["set", "subset"]

    return [prop.value for prop in self.properties if prop.name.lower() in names]

  def get_head(self):
    """
    Generalizable mask for get_set()
    """
    return self.get_set()

  def get_tail(self):
    """
    Generalizable mask for get_subset()
    """
    return self.get_subset()


class WholePart(Relation):
  """
  Whole-Part, which are a type of relation
  """
  def __eq__(self, other):
    """
    Check if 2 whole-part are equivalent.

    i.e. does other have exactly the same numerical entity id for Whole
    as well as for all Part entities
    """
    if self.get_whole().id_doc_num == other.get_whole().id_doc_num:
      return set([e.id_doc_num for e in self.get_part()]) == set([e.id_doc_num for e in other.get_part()])


  def get_whole(self):
    if self.get_text_safe(self.soup.properties.Whole):
      return self.document.entities_dict.get(self.get_text_safe(self.soup.properties.Whole))


  def get_part(self):
    if self.soup.find_all("Part") is not None:
      ss_strings = [self.get_text_safe(c) for c in self.soup.findAll("Part")]
      return [self.document.entities_dict.get(c) for c in ss_strings]


  def entity_ids(self):
    """
    Returns a list of every entity ID in the coref string
    """
    names = ["whole", "part"]

    return [prop.value for prop in self.properties if prop.name.lower() in names]

  def get_head(self):
    """
    Generalizable mask for get_whole()
    """
    return self.get_whole()

  def get_tail(self):
    """
    Generalizable mask for get_part()
    """
    return self.get_part()


class Entity(Annotation):
  def __init__(self, soup):
    super(Entity, self).__init__(soup)
    self.id = self.get_text_safe(self.soup.id)
    self.id_num = self.id.split("@")[0]
    self.id_doc_num = self.id_num + "@" + self.get_doc_id()
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
    return ";" in self.span_string

  def start_span(self):
    return self.spans[0][-1]

  def end_span(self):
    if self.is_disjointed():
      return self.spans[-1][-1]
    else:
      return self.spans[0][1]

  def properties(self):
    valued_props = []

    if self.soup.properties:
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
    self.soup.span.string = self.span_string
    self.soup.type.string = self.type
    self.soup.parentsType.string = self.parentsType


class Property(Annotation):
  def __init__(self, soup):
    super(Property, self).__init__(soup)
    self.name = self.soup.name
    self.value = self.get_text_safe(self.soup)

  def has_modality(self, modality):
    return self.name.lower() == "contextualmodality" and self.value.lower() == modality.lower()

  def is_aligned_with(self, other_prop):
    return self.name == other_prop.name and self.value and other_prop.value

  def agrees_with(self, other_prop):
    return self.name == other_prop.name and self.value == other_prop.value

  def update_soup(self):
    self.soup.string = self.value
