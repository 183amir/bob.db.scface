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
      self.session = utils.session(INFO.type(), INFO.files()[0])

  def is_valid(self):
    """Returns if a valid session has been opened for reading the database"""

    return self.session is not None

  def __check_validity__(self, l, obj, valid):
    """Checks validity of user input data against a set of valid values"""
    if not l: return valid
    elif isinstance(l, str): return self.__check_validity__((l,), obj, valid)
    for k in l:
      if k not in valid:
        raise RuntimeError, 'Invalid %s "%s". Valid values are %s, or lists/tuples of those' % (obj, k, valid)
    return l

  def clients(self, protocol=None, groups=None, subworld=None):
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

    Returns: A list containing all the client ids which have the given
    properties.
    """

    VALID_PROTOCOLS = ('combined', 'close', 'medium', 'far')
    VALID_GROUPS = ('dev', 'eval', 'world')
    VALID_SUBWORLDS = ('onethird', 'twothirds')
    protocol = self.__check_validity__(protocol, 'protocol', VALID_PROTOCOLS)
    groups = self.__check_validity__(groups, 'group', VALID_GROUPS)
    subworld = self.__check_validity__(subworld, "subworld", VALID_SUBWORLDS)

    retval = []
    # List of the clients
    if "world" in groups:
      if len(subworld)==1:
        q = self.session.query(Client).join(Subworld).filter(Subworld.name.in_(subworld))
      else:
        q = self.session.query(Client).filter(Client.sgroup == 'world')
      q = q.order_by(Client.id)
      for id in [k.id for k in q]: 
        retval.append(id)
    if 'dev' in groups or 'eval' in groups:
      q = self.session.query(Client).filter(and_(Client.sgroup != 'world', Client.sgroup.in_(groups))).\
            order_by(Client.id)
      for id in [k.id for k in q]: 
        retval.append(id)

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

  def zmodels(self, protocol=None, groups=None):
    """Returns a set of Z-Norm models for the specific query by the user.

    Keyword Parameters:

    protocol
      The protocol to consider ('combined', 'close', 'medium', 'far')

    groups
      The groups to which the subjects attached to the models belong ('dev', 'eval', 'world')

    Returns: A list containing all the model ids belonging to the given group.
    """

    return self.zclients(protocol, groups)

  def get_client_id_from_model_id(self, model_id):
    """Returns the client_id attached to the given model_id
    
    Keyword Parameters:

    model_id
      The model_id to consider

    Returns: The client_id attached to the given model_id
    """
    return model_id

  def get_client_id_from_tmodel_id(self, model_id):
    """Returns the client_id attached to the given T-Norm model_id
    
    Keyword Parameters:

    model_id
      The model_id to consider

    Returns: The client_id attached to the given T-Norm model_id
    """
    return model_id


  def get_client_id_from_file_id(self, file_id):
    """Returns the client_id (real client id) attached to the given file_id
    
    Keyword Parameters:

    file_id
      The file_id to consider

    Returns: The client_id attached to the given file_id
    """
    q = self.session.query(File).\
          filter(File.id == file_id)
    if q.count() !=1:
      #throw exception?
      return None
    else:
      return q.first().client_id

  def get_internal_path_from_file_id(self, file_id):
    """Returns the unique "internal path" attached to the given file_id
    
    Keyword Parameters:

    file_id
      The file_id to consider

    Returns: The internal path attached to the given file_id
    """
    q = self.session.query(File).\
          filter(File.id == file_id)
    if q.count() !=1:
      #throw exception?
      return None
    else:
      return q.first().path


  def objects(self, directory=None, extension=None, protocol=None,
      purposes=None, model_ids=None, groups=None, classes=None,
      subworld=None):
    """Returns a set of filenames for the specific query by the user.
    WARNING: Files used as impostor access for several different models are
    only listed one and refer to only a single model

    Keyword Parameters:

    directory
      A directory name that will be prepended to the final filepath returned

    extension
      A filename extension that will be appended to the final filepath returned

    protocol
      One of the SCFace protocols ('combined', 'close', 'medium', 'far')

    purposes
      The purposes required to be retrieved ('enrol', 'probe') or a tuple
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

    Returns: A dictionary containing:
      - 0: the resolved filenames 
      - 1: the model id
      - 2: the claimed id attached to the model
      - 3: the real id
      - 4: the "stem" path (basename of the file)

    considering allthe filtering criteria. The keys of the dictionary are 
    unique identities for each file in the SCFace database. Conserve these 
    numbers if you wish to save processing results later on.
    """

    def make_path(stem, directory, extension):
      import os
      if not extension: extension = ''
      if directory: return os.path.join(directory, stem + extension)
      return stem + extension

    VALID_PROTOCOLS = ('combined', 'close', 'medium', 'far')
    VALID_PURPOSES = ('enrol', 'probe')
    VALID_GROUPS = ('dev', 'eval', 'world')
    VALID_CLASSES = ('client', 'impostor')
    VALID_SUBWORLDS = ('onethird', 'twothirds')

    protocol = self.__check_validity__(protocol, "protocol", VALID_PROTOCOLS)
    purposes = self.__check_validity__(purposes, "purpose", VALID_PURPOSES)
    groups = self.__check_validity__(groups, "group", VALID_GROUPS)
    classes = self.__check_validity__(classes, "class", VALID_CLASSES)
    subworld = self.__check_validity__(subworld, "subworld", VALID_SUBWORLDS)

    retval = {}
    
    if(isinstance(model_ids,str)):
      model_ids = (model_ids,)
    
    if 'world' in groups:
      # WARNING: Restrict to frontal and camera 1 to 5
      validcam = ('frontal', 'cam1', 'cam2', 'cam3', 'cam4', 'cam5')
      q = self.session.query(File, Protocol).join(Client).\
            filter(and_(Client.sgroup == 'world', File.camera.in_(validcam)))
      if len(subworld) == 1:
        q = q.join(Subworld).filter(Subworld.name.in_(subworld))
      if model_ids:
        q = q.filter(Client.id.in_(model_ids))
      q = q.order_by(File.client_id, File.camera, File.distance)
      for k in q:
        retval[k[0].id] = (make_path(k[0].path, directory, extension), k[0].client_id, k[0].client_id, k[0].client_id, k[0].path)
    
    if ('dev' in groups or 'eval' in groups):
      dev_eval = ('dev', 'eval')
      if('enrol' in purposes):
        q = self.session.query(File, Protocol).join(Client).\
              filter(and_(Client.sgroup.in_(groups), Client.sgroup != 'world')).\
              filter(and_(Protocol.name.in_(protocol), Protocol.purpose == 'enrol')).\
              filter(and_(File.camera == Protocol.camera, File.distance == Protocol.distance))
        if model_ids:
          q = q.filter(Client.id.in_(model_ids))
        q = q.order_by(File.client_id, File.camera, File.distance)
        for k in q:
          retval[k[0].id] = (make_path(k[0].path, directory, extension), k[0].client_id, k[0].client_id, k[0].client_id, k[0].path)
      if('probe' in purposes):
        if('client' in classes):
          q = self.session.query(File, Protocol).join(Client).\
                filter(and_(Client.sgroup.in_(groups), Client.sgroup != 'world')).\
                filter(and_(Protocol.name.in_(protocol), Protocol.purpose == 'probe')).\
                filter(and_(File.camera == Protocol.camera, File.distance == Protocol.distance))
          if model_ids:
            q = q.filter(Client.id.in_(model_ids))
          q = q.order_by(File.client_id, File.camera, File.distance)
          for k in q:
            retval[k[0].id] = (make_path(k[0].path, directory, extension), k[0].client_id, k[0].client_id, k[0].client_id, k[0].path)
        if('impostor' in classes):
          q = self.session.query(File, Protocol).join(Client).\
                filter(and_(Client.sgroup.in_(groups), Client.sgroup != 'world')).\
                filter(and_(Protocol.name.in_(protocol), Protocol.purpose == 'probe')).\
                filter(and_(File.camera == Protocol.camera, File.distance == Protocol.distance))
          if(model_ids and len(model_ids)==1):
            q = q.filter(not_(Client.id.in_(model_ids)))
          q = q.order_by(File.client_id, File.camera, File.distance)
          for k in q:
            if(model_ids and len(model_ids) == 1):
              retval[k[0].id] = (make_path(k[0].path, directory, extension), model_ids[0], model_ids[0], k[0].client_id, k[0].path)
            else:
              retval[k[0].id] = (make_path(k[0].path, directory, extension), k[0].client_id, k[0].client_id, k[0].client_id, k[0].path)
        
    return retval

  def files(self, directory=None, extension=None, protocol=None,
      purposes=None, model_ids=None, groups=None, classes=None,
      subworld=None):
    """Returns a set of filenames for the specific query by the user.

    Keyword Parameters:

    directory
      A directory name that will be prepended to the final filepath returned

    extension
      A filename extension that will be appended to the final filepath returned

    protocol
      One of the SCFace protocols ('combined', 'close', 'medium', 'far')

    purposes
      The purposes required to be retrieved ('enrol', 'probe') or a tuple
      with several of them. If 'None' is given (this is the default), it is 
      considered the same as a tuple with all possible values. This field is
      ignored for the data from the "world" group.

    model_ids
      Only retrieves the files for the provided list of model ids (claimed 
      client id).  If 'None' is given (this is the default), no filter over 
      the model_ids is performed.

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

    Returns: A dictionary containing the resolved filenames considering all
    the filtering criteria. The keys of the dictionary are unique identities 
    for each file in the SCFace database. Conserve these numbers if you 
    wish to save processing results later on.
    """

    retval = {}
    d = self.objects(directory, extension, protocol, purposes, model_ids, groups, classes, subworld)
    for k in d: retval[k] = d[k][0]

    return retval

  def tobjects(self, directory=None, extension=None, protocol=None,
      model_ids=None, groups=None):
    """Returns a set of filenames for enrolling T-norm models for score 
       normalization.

    Keyword Parameters:

    directory
      A directory name that will be prepended to the final filepath returned

    extension
      A filename extension that will be appended to the final filepath returned

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

    Returns: A dictionary containing:

      * 0: the resolved filenames 
      * 1: the model id
      * 2: the claimed id attached to the model
      * 3: the real id
      * 4: the "stem" path (basename of the file)

    considering all the filtering criteria. The keys of the dictionary are 
    unique identities for each file in the SCface database. Conserve these 
    numbers if you wish to save processing results later on.
    """

    def make_path(stem, directory, extension):
      import os
      if not extension: extension = ''
      if directory: return os.path.join(directory, stem + extension)
      return stem + extension

    VALID_PROTOCOLS = ('combined', 'close', 'medium', 'far')
    VALID_GROUPS = ('dev', 'eval', 'world')

    protocol = self.__check_validity__(protocol, "protocol", VALID_PROTOCOLS)
    groups = self.__check_validity__(groups, "group", VALID_GROUPS)

    retval = {}
    
    if(isinstance(model_ids,str)):
      model_ids = (model_ids,)
   
    # ZT-Norm cohort is 'onethird' 
    subworld = ('onethird',)
    # WARNING: Restrict to frontal camera (enrol T-Norm models)
    validcam = ('frontal',)
    q = self.session.query(File, Protocol).join(Client).\
            join(Subworld).filter(Subworld.name.in_(subworld)).\
            filter(and_(Client.sgroup == 'world', File.camera.in_(validcam)))
    if model_ids:
      q = q.filter(Client.id.in_(model_ids))
    q = q.order_by(File.client_id)
    for k in q:
      retval[k[0].id] = (make_path(k[0].path, directory, extension), k[0].client_id, k[0].client_id, k[0].client_id, k[0].path)
    
    return retval

  def tfiles(self, directory=None, extension=None, protocol=None,
      model_ids=None, groups=None):
    """Returns a set of filenames for enrolling T-norm models for score 
       normalization.

    Keyword Parameters:

    directory
      A directory name that will be prepended to the final filepath returned

    extension
      A filename extension that will be appended to the final filepath returned

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

    Returns: A dictionary containing:

      * 0: the resolved filenames 
      * 1: the model id
      * 2: the claimed id attached to the model
      * 3: the real id
      * 4: the "stem" path (basename of the file)

    considering allthe filtering criteria. The keys of the dictionary are 
    unique identities for each file in the SCface database. Conserve these 
    numbers if you wish to save processing results later on.
    """

    retval = {}
    d = self.tobjects(directory, extension, protocol, model_ids, groups)
    for k in d: retval[k] = d[k][0]

    return retval

  def zobjects(self, directory=None, extension=None, protocol=None,
      model_ids=None, groups=None):
    """Returns a set of filenames to perform Z-norm score normalization.

    Keyword Parameters:

    directory
      A directory name that will be prepended to the final filepath returned

    extension
      A filename extension that will be appended to the final filepath returned

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

    Returns: A dictionary containing:

      * 0: the resolved filenames 
      * 1: the model id
      * 2: the claimed id attached to the model
      * 3: the real id
      * 4: the "stem" path (basename of the file)

    considering all the filtering criteria. The keys of the dictionary are 
    unique identities for each file in the SCface database. Conserve these 
    numbers if you wish to save processing results later on.
    """

    def make_path(stem, directory, extension):
      import os
      if not extension: extension = ''
      if directory: return os.path.join(directory, stem + extension)
      return stem + extension

    VALID_PROTOCOLS = ('combined', 'close', 'medium', 'far')
    VALID_GROUPS = ('dev', 'eval', 'world')

    protocol = self.__check_validity__(protocol, "protocol", VALID_PROTOCOLS)
    groups = self.__check_validity__(groups, "group", VALID_GROUPS)

    retval = {}
    
    if(isinstance(model_ids,str)):
      model_ids = (model_ids,)
   
    # ZT-Norm cohort is 'onethird' 
    subworld = ('onethird',)
    # WARNING: Restrict to frontal camera (enrol T-Norm models)
    validcam = ('cam1','cam2','cam3','cam4','cam5')
    q = self.session.query(File, Protocol).join(Client).\
            join(Subworld).filter(Subworld.name.in_(subworld)).\
            filter(and_(Client.sgroup == 'world', File.camera.in_(validcam)))
    if model_ids:
      q = q.filter(Client.id.in_(model_ids))
    q = q.order_by(File.client_id)
    for k in q:
      retval[k[0].id] = (make_path(k[0].path, directory, extension), k[0].client_id, k[0].client_id, k[0].client_id, k[0].path)
    
    return retval

  def zfiles(self, directory=None, extension=None, protocol=None,
      model_ids=None, groups=None):
    """Returns a set of filenames to perform Z-norm score normalization.

    Keyword Parameters:

    directory
      A directory name that will be prepended to the final filepath returned

    extension
      A filename extension that will be appended to the final filepath returned

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

    Returns: A dictionary containing:

      * 0: the resolved filenames 
      * 1: the model id
      * 2: the claimed id attached to the model
      * 3: the real id
      * 4: the "stem" path (basename of the file)

    considering all the filtering criteria. The keys of the dictionary are 
    unique identities for each file in the SCface database. Conserve these 
    numbers if you wish to save processing results later on.
    """

    retval = {}
    d = self.zobjects(directory, extension, protocol, model_ids, groups)
    for k in d: retval[k] = d[k][0]

    return retval

  def save_one(self, id, obj, directory, extension):
    """Saves a single object supporting the bob save() protocol.

    This method will call save() on the the given object using the correct
    database filename stem for the given id.
    
    Keyword Parameters:

    id
      The id of the object in the database table "file".

    obj
      The object that needs to be saved, respecting the bob save() protocol.

    directory
      This is the base directory to which you want to save the data. The
      directory is tested for existence and created if it is not there with
      os.makedirs()

    extension
      The extension determines the way each of the arrays will be saved.
    """

    import os
    from bob.io import save

    fobj = self.session.query(File).filter_by(id=id).one()
    fullpath = os.path.join(directory, str(fobj.path) + extension)
    fulldir = os.path.dirname(fullpath)
    utils.makedirs_safe(fulldir)
    save(obj, fullpath)

  def save(self, data, directory, extension):
    """This method takes a dictionary of blitz arrays or bob.database.Array's
    and saves the data respecting the original arrangement as returned by
    files().

    Keyword Parameters:

    data
      A dictionary with two keys 'real' and 'attack', each containing a
      dictionary mapping file ids from the original database to an object that
      supports the bob "save()" protocol.

    directory
      This is the base directory to which you want to save the data. The
      directory is tested for existence and created if it is not there with
      os.makedirs()

    extension
      The extension determines the way each of the arrays will be saved.
    """    

    for key, value in data:
      self.save_one(key, value, directory, extension)
