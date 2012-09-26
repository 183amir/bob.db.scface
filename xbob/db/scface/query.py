#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Laurent El Shafey <Laurent.El-Shafey@idiap.ch>

"""This module provides the Dataset interface allowing the user to query the
SCFace database in the most obvious ways.
"""

import os
from bob.db import utils
from .models import *
from .driver import Interface

INFO = Interface()

SQLITE_FILE = INFO.files()[0]

class Database(object):
  """The dataset class opens and maintains a connection opened to the Database.

  It provides many different ways to probe for the characteristics of the data
  and for the data itself inside the database.
  """

  def __init__(self):
    # opens a session to the database - keep it open until the end
    self.connect()
  
  def connect(self):
    """Tries connecting or re-connecting to the database"""
    if not os.path.exists(SQLITE_FILE):
      self.session = None

    else:
      self.session = utils.session_try_readonly(INFO.type(), SQLITE_FILE)

  def is_valid(self):
    """Returns if a valid session has been opened for reading the database"""

    return self.session is not None

  def assert_validity(self):
    """Raise a RuntimeError if the database backend is not available"""

    if not self.is_valid():
      raise RuntimeError, "Database '%s' cannot be found at expected location '%s'. Create it and then try re-connecting using Database.connect()" % (INFO.name(), SQLITE_FILE)

  def __check_validity__(self, l, obj, valid, default):
    """Checks validity of user input data against a set of valid values"""
    if not l: return default
    elif not isinstance(l, (tuple,list)): 
      return self.__check_validity__((l,), obj, valid, default)
    for k in l:
      if k not in valid:
        raise RuntimeError, 'Invalid %s "%s". Valid values are %s, or lists/tuples of those' % (obj, k, valid)
    return l

  def groups(self):
    """Returns the names of all registered groups"""

    return ProtocolPurpose.group_choices # Same as Client.group_choices for this database

  def genders(self):
    """Returns the list of genders: 'm' for male and 'f' for female"""

    return Client.gender_choices

  def subworld_names(self):
    """Returns all registered subworld names"""

    self.assert_validity()
    l = self.subworlds()
    retval = [str(k.name) for k in l]
    return retval

  def subworlds(self):
    """Returns the list of subworlds"""

    self.assert_validity()

    return list(self.session.query(Subworld))

  def has_subworld(self, name):
    """Tells if a certain subworld is available"""

    self.assert_validity()
    return self.session.query(Subworld).filter(Subworld.name==name).count() != 0

  def clients(self, protocol=None, groups=None, subworld=None, gender=None, birthyear=None):
    """Returns a set of clients for the specific query by the user.

    Keyword Parameters:

    protocol
      The protocol to consider ('combined', 'close', 'medium', 'far')

    groups
      The groups to which the clients belong ('dev', 'eval', 'world')

    subworld
      Specify a split of the world data ("onethird", "twothirds", "")
      In order to be considered, "world" should be in groups and only one 
      split should be specified. 

    gender
      The genders to which the clients belong ('f', 'm')

    birthyear
      The birth year of the clients (in the range [1900,2050]) 

    Returns: A list containing all the clients which have the given
    properties.
    """

    self.assert_validity()

    VALID_PROTOCOLS = self.protocol_names()
    VALID_GROUPS = self.groups()
    VALID_SUBWORLDS = self.subworld_names()
    VALID_GENDERS = self.genders()
    VALID_BIRTHYEARS = range(1900,2050)
    protocol = self.__check_validity__(protocol, 'protocol', VALID_PROTOCOLS, VALID_PROTOCOLS)
    groups = self.__check_validity__(groups, 'group', VALID_GROUPS, VALID_GROUPS)
    subworld = self.__check_validity__(subworld, "subworld", VALID_SUBWORLDS, [])
    gender = self.__check_validity__(gender, "gender", VALID_GENDERS, [])
    birthyear = self.__check_validity__(birthyear, 'birthyear', VALID_BIRTHYEARS, [])

    retval = []
    # List of the clients
    if "world" in groups:
      q = self.session.query(Client).filter(Client.sgroup == 'world')
      if subworld:
        q = q.join(Subworld, Client.subworld).filter(Subworld.name.in_(subworld))
      if gender:
        q = q.filter(Client.gender.in_(gender))
      if birthyear:
        q = q.filter(Client.birthyear.in_(birthyear))
      q = q.order_by(Client.id)
      retval += list(q)
    if 'dev' in groups or 'eval' in groups:
      q = self.session.query(Client).filter(and_(Client.sgroup != 'world', Client.sgroup.in_(groups)))
      if gender:
        q = q.filter(Client.gender.in_(gender))
      if birthyear:
        q = q.filter(Client.birthyear.in_(birthyear))
      q = q.order_by(Client.id)
      retval += list(q)
    return retval

  def tclients(self, protocol=None, groups=None):
    """Returns a set of T-Norm clients for the specific query by the user.

    Keyword Parameters:

    protocol
      The protocol to consider ('combined', 'close', 'medium', 'far')

    groups
      The groups to which the clients belong ('dev', 'eval', 'world')

    Returns: A list containing all the client ids belonging to the given group.
    """

    # T-Norm clients are the ones from the onethird world subset
    return self.clients(protocol, 'world', 'onethird')

  def zclients(self, protocol=None, groups=None):
    """Returns a set of Z-Norm clients for the specific query by the user.

    Keyword Parameters:

    protocol
      The protocol to consider ('combined', 'close', 'medium', 'far')

    groups
      The groups to which the clients belong ('dev', 'eval', 'world')

    Returns: A list containing all the model ids belonging to the given group.
    """

    # Z-Norm clients are the ones from the onethird world subset
    return self.clients(protocol, 'world', 'onethird')

  def models(self, protocol=None, groups=None):
    """Returns a set of models for the specific query by the user.

    Keyword Parameters:

    protocol
      The protocol to consider ('combined', 'close', 'medium', 'far')

    groups
      The groups to which the subjects attached to the models belong ('dev', 'eval', 'world')

    Returns: A list containing all the model ids belonging to the given group.
    """

    return self.clients(protocol, groups)

  def has_client_id(self, id):
    """Returns True if we have a client with a certain integer identifier"""

    self.assert_validity()
    return self.session.query(Client).filter(Client.id==id).count() != 0

  def client(self, id):
    """Returns the client object in the database given a certain id. Raises
    an error if that does not exist."""

    self.assert_validity()
    return self.session.query(Client).filter(Client.id==id).one()

  def tmodels(self, protocol=None, groups=None):
    """Returns a set of T-Norm models for the specific query by the user.

    Keyword Parameters:

    protocol
      The protocol to consider ('combined', 'close', 'medium', 'far')

    groups
      The groups to which the subjects attached to the models belong ('dev', 'eval', 'world')

    Returns: A list containing all the model ids belonging to the given group.
    """

    return self.tclients(protocol, groups)

  def get_client_id_from_model_id(self, model_id):
    """Returns the client_id attached to the given model_id
    
    Keyword Parameters:

    model_id
      The model_id to consider

    Returns: The client_id attached to the given model_id
    """
    return model_id

  def objects(self, protocol=None, purposes=None, model_ids=None, groups=None, 
      classes=None, subworld=None):
    """Returns a set of Files for the specific query by the user.

    Keyword Parameters:

    protocol
      One of the SCFace protocols ('combined', 'close', 'medium', 'far')

    purposes
      The purposes required to be retrieved ('enrol', 'probe', 'world') or a tuple
      with several of them. If 'None' is given (this is the default), it is 
      considered the same as a tuple with all possible values. This field is
      ignored for the data from the "world" group.

    model_ids
      Only retrieves the files for the provided list of model ids (claimed 
      client id). The model ids are string.  If 'None' is given (this is 
      the default), no filter over the model_ids is performed.

    groups
      One of the groups ('dev', 'eval', 'world') or a tuple with several of them. 
      If 'None' is given (this is the default), it is considered the same as a 
      tuple with all possible values.

    classes
      The classes (types of accesses) to be retrieved ('client', 'impostor') 
      or a tuple with several of them. If 'None' is given (this is the 
      default), it is considered the same as a tuple with all possible values.

    subworld
      Specify a split of the world data ("onethird", "twothirds", "")
      In order to be considered, "world" should be in groups and only one 
      split should be specified. 

    Returns: A list of Files with the given properties
    """

    self.assert_validity()

    VALID_PROTOCOLS = self.protocol_names()
    VALID_PURPOSES = self.purposes()
    VALID_GROUPS = self.groups()
    VALID_CLASSES = ('client', 'impostor')
    VALID_SUBWORLDS = self.subworld_names()

    protocol = self.__check_validity__(protocol, "protocol", VALID_PROTOCOLS, VALID_PROTOCOLS)
    purposes = self.__check_validity__(purposes, "purpose", VALID_PURPOSES, VALID_PURPOSES)
    groups = self.__check_validity__(groups, "group", VALID_GROUPS, VALID_GROUPS)
    classes = self.__check_validity__(classes, "class", VALID_CLASSES, VALID_CLASSES)
    subworld = self.__check_validity__(subworld, "subworld", VALID_SUBWORLDS, [])

    import collections
    if(model_ids is None):
      model_ids = ()
    elif(not isinstance(model_ids,collections.Iterable)):
      model_ids = (model_ids,)

    # Now query the database
    retval = []
    if 'world' in groups:
      q = self.session.query(File).join(Client).join(ProtocolPurpose, File.protocol_purposes).join(Protocol)
      if subworld:
        q = q.join(Subworld, Client.subworld).filter(Subworld.name.in_(subworld))
      q = q.filter(and_(Protocol.name.in_(protocol), ProtocolPurpose.sgroup == 'world'))
      if model_ids:
        q = q.filter(Client.id.in_(model_ids))
      q = q.order_by(File.client_id, File.camera, File.distance, File.id)
      retval += list(q)
    
    if ('dev' in groups or 'eval' in groups):
      if('enrol' in purposes):
        q = self.session.query(File).join(Client).join(ProtocolPurpose, File.protocol_purposes).join(Protocol).\
              filter(and_(Protocol.name.in_(protocol), ProtocolPurpose.sgroup.in_(groups), ProtocolPurpose.purpose == 'enrol'))
        if model_ids:
          q = q.filter(Client.id.in_(model_ids))
        q = q.order_by(File.client_id, File.camera, File.distance, File.id)
        retval += list(q)

      if('probe' in purposes):
        if('client' in classes):
          q = self.session.query(File).join(Client).join(ProtocolPurpose, File.protocol_purposes).join(Protocol).\
                filter(and_(Protocol.name.in_(protocol), ProtocolPurpose.sgroup.in_(groups), ProtocolPurpose.purpose == 'probe'))
          if model_ids:
            q = q.filter(Client.id.in_(model_ids))
          q = q.order_by(File.client_id, File.camera, File.distance, File.id)
          retval += list(q)

        if('impostor' in classes):
          q = self.session.query(File).join(Client).join(ProtocolPurpose, File.protocol_purposes).join(Protocol).\
                filter(and_(Protocol.name.in_(protocol), ProtocolPurpose.sgroup.in_(groups), ProtocolPurpose.purpose == 'probe'))
          if len(model_ids) == 1:
            q = q.filter(not_(File.client_id.in_(model_ids)))
          q = q.order_by(File.client_id, File.camera, File.distance, File.id)
          retval += list(q)
    
    return list(set(retval)) # To remove duplicates


  def tobjects(self, protocol=None, model_ids=None, groups=None):
    """Returns a set of Files for enrolling T-norm models for score 
       normalization.

    Keyword Parameters:

    protocol
      One of the SCFace protocols ('combined', 'close', 'medium', 'far')

    model_ids
      Only retrieves the files for the provided list of model ids (claimed 
      client id).  If 'None' is given (this is the default), no filter over 
      the model_ids is performed.

    groups
      One of the groups ('dev', 'eval', 'world') or a tuple with several of them. 
      If 'None' is given (this is the default), it is considered the same as a 
      tuple with all possible values.

    Returns: A set of Files with the given properties
    """

    VALID_PROTOCOLS = self.protocol_names()
    VALID_GROUPS = self.groups()
    # ZT-Norm cohort is 'onethird' 
    subworld = ('onethird',)
    # WARNING: Restrict to frontal camera (enrol T-Norm models)
    validcam = ('frontal',)

    protocol = self.__check_validity__(protocol, "protocol", VALID_PROTOCOLS, VALID_PROTOCOLS)
    groups = self.__check_validity__(groups, "group", VALID_GROUPS, VALID_GROUPS)

    import collections
    if(model_ids is None):
      model_ids = ()
    elif(not isinstance(model_ids,collections.Iterable)):
      model_ids = (model_ids,)

    # Now query the database
    retval = []
    q = self.session.query(File).join(Client).join(ProtocolPurpose, File.protocol_purposes).join(Protocol)
    q = q.join(Subworld).filter(Subworld.name.in_(subworld))
    q = q.filter(and_(Protocol.name.in_(protocol), ProtocolPurpose.sgroup == 'world', File.camera.in_(validcam)))
    if model_ids:
      q = q.filter(Client.id.in_(model_ids))
    q = q.order_by(File.client_id, File.camera, File.distance, File.id)
    retval += list(q)

    return retval

  def zobjects(self, protocol=None, model_ids=None, groups=None):
    """Returns a set of Files to perform Z-norm score normalization.

    Keyword Parameters:

    protocol
      One of the SCFace protocols ('combined', 'close', 'medium', 'far')

    model_ids
      Only retrieves the files for the provided list of model ids (claimed 
      client id).  If 'None' is given (this is the default), no filter over 
      the model_ids is performed.

    groups
      One of the groups ('dev', 'eval', 'world') or a tuple with several of them. 
      If 'None' is given (this is the default), it is considered the same as a 
      tuple with all possible values.

    Returns: A set of Files
    """

    VALID_PROTOCOLS = self.protocol_names()
    VALID_GROUPS = self.groups()
    # ZT-Norm cohort is 'onethird' 
    subworld = ('onethird',)
    # WARNING: Restrict to non-frontal camera (enrol T-Norm models)
    validcam = ('cam1','cam2','cam3','cam4','cam5')

    protocol = self.__check_validity__(protocol, "protocol", VALID_PROTOCOLS, VALID_PROTOCOLS)
    groups = self.__check_validity__(groups, "group", VALID_GROUPS, VALID_GROUPS)

    import collections
    if(model_ids is None):
      model_ids = ()
    elif(not isinstance(model_ids,collections.Iterable)):
      model_ids = (model_ids,)

    retval = []    
    q = self.session.query(File).join(Client).join(ProtocolPurpose, File.protocol_purposes).join(Protocol)
    q = q.join(Subworld).filter(Subworld.name.in_(subworld))
    q = q.filter(and_(Protocol.name.in_(protocol), ProtocolPurpose.sgroup == 'world', File.camera.in_(validcam)))
    if model_ids:
      q = q.filter(Client.id.in_(model_ids))
    q = q.order_by(File.client_id, File.camera, File.distance, File.id)
    retval += list(q)
    
    return retval

  def protocol_names(self):
    """Returns all registered protocol names"""

    self.assert_validity()
    l = self.protocols()
    retval = [str(k.name) for k in l]
    return retval

  def protocols(self):
    """Returns all registered protocols"""

    self.assert_validity()
    return list(self.session.query(Protocol))

  def has_protocol(self, name):
    """Tells if a certain protocol is available"""

    self.assert_validity()
    return self.session.query(Protocol).filter(Protocol.name==name).count() != 0

  def protocol(self, name):
    """Returns the protocol object in the database given a certain name. Raises
    an error if that does not exist."""

    self.assert_validity()
    return self.session.query(Protocol).filter(Protocol.name==name).one()

  def protocol_purposes(self):
    """Returns all registered protocol purposes"""

    self.assert_validity()
    return list(self.session.query(ProtocolPurpose))

  def purposes(self):
    """Returns the list of allowed purposes"""

    return ProtocolPurpose.purpose_choices

  def paths(self, ids, prefix='', suffix=''):
    """Returns a full file paths considering particular file ids, a given
    directory and an extension

    Keyword Parameters:

    id
      The ids of the object in the database table "file". This object should be
      a python iterable (such as a tuple or list).

    prefix
      The bit of path to be prepended to the filename stem

    suffix
      The extension determines the suffix that will be appended to the filename
      stem.

    Returns a list (that may be empty) of the fully constructed paths given the
    file ids.
    """

    self.assert_validity()

    fobj = self.session.query(File).filter(File.id.in_(ids))
    retval = []
    for p in ids:
      retval.extend([k.make_path(prefix, suffix) for k in fobj if k.id == p])
    return retval

  def reverse(self, paths):
    """Reverses the lookup: from certain stems, returning file ids

    Keyword Parameters:

    paths
      The filename stems I'll query for. This object should be a python
      iterable (such as a tuple or list)

    Returns a list (that may be empty).
    """

    self.assert_validity()

    fobj = self.session.query(File).filter(File.path.in_(paths))
    for p in paths:
      retval.extend([k.id for k in fobj if k.path == p])
    return retval
 
