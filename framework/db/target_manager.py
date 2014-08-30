import os
import sqlalchemy.exc

from urlparse import urlparse

from framework.lib.exceptions import DBIntegrityException, \
                                     InvalidTargetReference, \
                                     InvalidParameterType
from framework.db import models
from framework.lib import general
from framework.lib.general import cprint #TODO: Shift to logging


TARGET_CONFIG = {
                    'ID' : 0,
                    'TARGET_URL' : '',
                    'HOST_NAME' : '',
                    'HOST_PATH' : '',
                    'URL_SCHEME' : '',
                    'PORT_NUMBER' : '', # In str form
                    'HOST_IP' : '',
                    'ALTERNATIVE_IPS' : '', # str(list), so it can easily reversed using list(str)
                    'IP_URL' : '',
                    'TOP_DOMAIN' : '',
                    'TOP_URL' : '',
                    'SCOPE' : True
                }

PATH_CONFIG = {
                    'PARTIAL_URL_OUTPUT_PATH' : '',
                    'HOST_OUTPUT' : '',
                    'PORT_OUTPUT' : '',
                    'URL_OUTPUT' : '',
                    'PLUGIN_OUTPUT_DIR' : ''
              }


def target_required(func):
    """
    Inorder to use this decorator on a `method` there are two requirements
    + target_id must be a kwarg of the function
    + Core must be attached to the object at self.Core

    All this decorator does is check if a valid value is passed for target_id
    if not get the target_id from target manager and pass it
    """
    def wrapped_function(*args, **kwargs):
        if (kwargs.get("target_id", "None") == "None") or (kwargs.get("target_id", True) is None):  # True if target_id doesnt exist
            kwargs["target_id"] = args[0].Core.DB.Target.GetTargetID()
        return func(*args, **kwargs)
    return wrapped_function


class TargetDB(object):
    # All these variables reflect to current target which is referenced by a unique ID
    TargetID = None
    TargetConfig = dict(TARGET_CONFIG)
    PathConfig = dict(PATH_CONFIG)

    def __init__(self, Core):
        self.Core = Core
        #self.TargetDBHealthCheck()

    def SetTarget(self, target_id):
        try:
            self.TargetID = target_id
            self.TargetConfig = self.GetTargetConfigForID(target_id)
            self.PathConfig = self.DerivePathConfig(self.TargetConfig)
        except InvalidTargetReference:
            pass

    def DerivePathConfig(self, target_config):
        path_config = {}
        path_config['HOST_OUTPUT'] = os.path.join(self.Core.Config.FrameworkConfigGet('OUTPUT_PATH'), target_config['HOST_IP']) # Set the output directory
        path_config['PORT_OUTPUT'] = os.path.join(path_config['HOST_OUTPUT'], target_config['PORT_NUMBER']) # Set the output directory
        path_config['URL_OUTPUT'] = os.path.join(self.Core.Config.GetOutputDirForTarget(target_config['TARGET_URL'])) # Set the URL output directory (plugins will save their data here)
        path_config['PARTIAL_URL_OUTPUT_PATH'] = os.path.join(path_config['URL_OUTPUT'], 'partial') # Set the partial results path
        return path_config

    def GetTargetID(self):
        return self.TargetID

    def GetTargetURL(self):
        return self.Get("TARGET_URL")

    def GetTargetURLs(self):
        return self.GetAll("TARGET_URL")

    def GetIndexedTargets(self):
        results = self.Core.DB.session.query(models.Target.id, models.Target.target_url).all()
        return results

    def GetTargetConfig(self):
        return self.TargetConfig

    def GetPathConfig(self):
        return self.PathConfig

    def GetPath(self, output_type):
        return self.PathConfig.get(output_type, None)

    def SetPath(self, output_type, path):
        # Mainly used for setting output paths for individual plugins, which need not be saved: PLUGIN_OUTPUT_DIR
        self.PathConfig[output_type] = path

    def DBHealthCheck(self):
        # Target DB Health Check
        target_list = self.Core.DB.session.query(models.Target).all()
        if target_list:
        # If needed inorder to prevent an uninitialized value for target in self.SetTarget(target) few lines later
            for target in target_list:
                self.Core.DB.Target.CreateMissingDBsForURL(target.target_url)
            self.SetTarget(target.id) # This is to avoid "None" value for the main settings

    def AddTarget(self, TargetURL):
        if TargetURL not in self.GetTargetURLs():
            # A try-except can be used here, but then ip-resolution takes time
            # even if target is present
            target_config = self.Core.Config.DeriveConfigFromURL(TargetURL)
            # ----------- Target model object creation -----------
            config_obj = models.Target(target_url=TargetURL)
            config_obj.host_name = target_config["HOST_NAME"]
            config_obj.host_path = target_config["HOST_PATH"]
            config_obj.url_scheme = target_config["URL_SCHEME"]
            config_obj.port_number = target_config["PORT_NUMBER"]
            config_obj.host_ip = target_config["HOST_IP"]
            config_obj.alternative_ips = str(target_config["ALTERNATIVE_IPS"])
            config_obj.ip_url = target_config["IP_URL"]
            config_obj.top_domain = target_config["TOP_DOMAIN"]
            config_obj.top_url = target_config["TOP_URL"]
            # ----------------------------------------------------
            self.Core.DB.session.add(config_obj)
            self.Core.DB.session.commit()
            target_id = config_obj.id
            self.CreateMissingDBsForURL(TargetURL)
            self.SetTarget(target_id)
        else:
            raise DBIntegrityException(TargetURL + " already present in Target DB")

    def UpdateTarget(self, data_dict, TargetURL=None, ID=None):
        if ID:
            target_obj = self.Core.DB.session.query(models.Target).get(ID)
        if TargetURL:
            target_obj = self.Core.DB.session.query(models.Target).filter_by(target_url = TargetURL).one()
        if not target_obj:
            raise InvalidTargetReference("Target doesn't exist: " + str(ID) if ID else str(TargetURL))
        # TODO: Updating all related attributes when one attribute is changed
        for key, value in data.items():
            if key == "IN_CONTEXT":
                setattr(target_obj, key.lower(), self.Core.Config.ConvertStrToBool(value))
        self.Core.DB.session.merge(target_obj)
        self.Core.DB.session.commit()

    def DeleteTarget(self, TargetURL=None, ID=None):
        if ID:
            target_obj = self.Core.DB.session.query(models.Target).get(ID)
        if TargetURL:
            target_obj = self.Core.DB.session.query(models.Target).filter_by(target_url = TargetURL).one()
        if not target_obj:
            raise InvalidTargetReference("Target doesn't exist: " + str(ID) if ID else str(TargetURL))
        target_url = target_obj.target_url
        target_id = target_obj.id
        self.Core.DB.session.delete(target_obj)
        self.Core.DB.session.commit()
        self.Core.Config.CleanUpForTarget(target_url)

    def CreateMissingDBsForURL(self, TargetURL):
        self.Core.Config.CreateOutputDirForTarget(TargetURL)

    def GetTargetURLForID(self, ID):
        target_obj = self.Core.DB.session.query(models.Target).get(ID)
        if not target_obj:
            cprint("Failing with ID:" + str(ID))
            raise InvalidTargetReference("Target doesn't exist with ID: " + str(ID))
        return(target_obj.target_url)

    def GetTargetConfigForID(self, ID):
        target_obj = self.Core.DB.session.query(models.Target).get(ID)
        if not target_obj:
            raise InvalidTargetReference("Target doesn't exist: " + str(ID))
        return(self.DeriveTargetConfig(target_obj))

    def GetTargetConfigs(self, filter_data=None):
        if filter_data is None:
            filter_data = {}
        query = self.Core.DB.session.query(models.Target)
        if filter_data.get("TARGET_URL", None):
            if isinstance(filter_data["TARGET_URL"], (str, unicode)):
                query = query.filter_by(target_url = filter_data["TARGET_URL"])
            if isinstance(filter_data["TARGET_URL"], list):
                query = query.filter(models.Target.target_url.in_(filter_data.get("TARGET_URL")))
        if filter_data.get("HOST_IP", None):
            if isinstance(filter_data["HOST_IP"], (str, unicode)):
                query = query.filter_by(host_ip = filter_data["HOST_IP"])
            if isinstance(filter_data["HOST_IP"], list):
                query = query.filter(models.Target.host_ip.in_(filter_data.get("HOST_IP")))
        if filter_data.get("SCOPE", None):
            filter_data["SCOPE"] = filter_data["SCOPE"][0]
            query = query.filter_by(scope = self.Core.Config.ConvertStrToBool(filter_data.get("SCOPE")))
        if filter_data.get("HOST_NAME", None):
            if isinstance(filter_data["HOST_NAME"], (str, unicode)):
                query = query.filter_by(host_name = filter_data["HOST_NAME"])
            if isinstance(filter_data["HOST_NAME"], list):
                query = query.filter(models.Target.host_name.in_(filter_data.get("HOST_NAME")))
        try:
            if filter_data.get("ID", None):
                if isinstance(filter_data["ID"], (str, unicode)):
                    query = query.filter_by(id = filter_data["ID"])
                if isinstance(filter_data["ID"], list):
                    query = query.filter(models.Target.id.in_(filter_data.get("ID")))
            if filter_data.get('ID[lt]', None):
                if isinstance(filter_data.get('ID[lt]'), list):
                    filter_data['id[lt]'] = filter_data['ID[lt]'][0]
                query = query.filter(models.Target.id < int(filter_data['ID[lt]']))
            if filter_data.get('ID[gt]', None):
                if isinstance(filter_data.get('ID[gt]'), list):
                    filter_data['ID[gt]'] = filter_data['ID[gt]'][0]
                query = query.filter(models.Target.id > int(filter_data['ID[gt]']))
        except ValueError:
            raise InvalidParameterType("Invalid parameter type for target db for ID[lt] or ID[gt]")
        target_obj_list = query.all()
        return(self.DeriveTargetConfigs(target_obj_list))

    def DeriveTargetConfig(self, target_obj):
        target_config = dict(TARGET_CONFIG)
        if target_obj:
            for key in TARGET_CONFIG.keys():
                target_config[key] = getattr(target_obj, key.lower())
            return target_config
        return(None)

    def DeriveTargetConfigs(self, target_obj_list):
        target_configs = []
        for target_obj in target_obj_list:
            target_configs.append(self.DeriveTargetConfig(target_obj))
        return(target_configs)

    def Get(self, Key):
        return(self.TargetConfig[Key])

    def GetAsList(self, key_list):
        values = []
        for key in key_list:
            values.append(self.Get(key))
        return(values)

    def GetAll(self, Key):
        results = self.Core.DB.session.query(getattr(models.Target, Key.lower())).all()
        results = [result[0] for result in results]
        return results

    def GetAllInScope(self, Key):
        results = self.Core.DB.session.query(getattr(models.Target, Key.lower())).filter_by(scope = True).all()
        results = [result[0] for result in results]
        return results

    def IsInScopeURL(self, URL): # To avoid following links to other domains
        ParsedURL = urlparse(URL)
        #URLHostName = URL.split("/")[2]
        for HostName in self.GetAll('HOST_NAME'): # Get all known Host Names in Scope
            #if URLHostName == HostName:
            if ParsedURL.hostname == HostName:
                return True
        return False
