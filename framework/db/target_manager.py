from framework.db import models
from framework.lib import general
from urlparse import urlparse
import sqlalchemy.exc
import os

TARGET_CONFIG = {
                    'ID' : '',
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
                    'IN_CONTEXT' : True
                }

PATH_CONFIG = {
                    'PARTIAL_URL_OUTPUT_PATH' : '',
                    'HOST_OUTPUT' : '',
                    'PORT_OUTPUT' : '',
                    'URL_OUTPUT' : '',
                    'PLUGIN_OUTPUT_DIR' : ''
              }

class TargetDB(object):
    # All these variables reflect to current target
    Target = None
    TargetConfig = dict(TARGET_CONFIG)
    PathConfig = dict(PATH_CONFIG)
    OutputDBSession = None
    TransactionDBSession = None
    UrlDBSession = None

    def __init__(self, Core):
        self.Core = Core
        self.TargetConfigDBSession = self.Core.DB.CreateScopedSession(self.Core.Config.FrameworkConfigGetDBPath("TCONFIG_DB_PATH"), models.TargetBase)
        #self.TargetDBHealthCheck()

    def SetTarget(self, target_url):
        if target_url in self.GetTargets():
            self.Target = target_url
            self.TargetConfig = self.GetTargetConfigForURL(target_url)
            self.PathConfig = self.GetPathConfigForTargetConfig(self.TargetConfig)
            self.OutputDBSession = self.CreateOutputDBSession(self.Target)
            self.TransactionDBSession = self.CreateTransactionDBSession(self.Target)
            self.UrlDBSession = self.CreateUrlDBSession(self.Target)

    def GetPathConfigForTargetConfig(self, target_config):
        path_config = {}
        path_config['HOST_OUTPUT'] = os.path.join(self.Core.Config.FrameworkConfigGet('OUTPUT_PATH'), target_config['HOST_IP']) # Set the output directory
        path_config['PORT_OUTPUT'] = os.path.join(path_config['HOST_OUTPUT'], target_config['PORT_NUMBER']) # Set the output directory
        URLInfoID = target_config['TARGET_URL'].replace('/','_').replace(':','')
        path_config['URL_OUTPUT'] = os.path.join(self.Core.Config.FrameworkConfigGet('OUTPUT_PATH'), self.Core.Config.FrameworkConfigGet('TARGETS_DIR'), URLInfoID) # Set the URL output directory (plugins will save their data here)
        path_config['PARTIAL_URL_OUTPUT_PATH'] = os.path.join(path_config['URL_OUTPUT'], 'partial') # Set the partial results path
        return path_config

    def GetTarget(self):
        return self.Target

    def GetTargetConfig(self):
        return self.TargetConfig

    def GetPathConfig(self):
        return self.PathConfig

    def GetPath(self, output_type):
        return self.PathConfig.get(output_type, None)

    def SetPath(self, output_type, path):
        self.PathConfig[output_type] = path

    def DBHealthCheck(self):
        # Target DB Health Check
        session = self.TargetConfigDBSession()
        target_list = session.query(models.Target).all()
        if target_list: 
        # If needed inorder to prevent an uninitialized value for target in self.SetTarget(target) few lines later
            for target in target_list:
                self.Core.DB.Target.CreateMissingDBsForURL(target.target_url)
            self.SetTarget(target) # This is to avoid "None" value for the main settings

    def AddTarget(self, TargetURL):
        if TargetURL not in self.GetTargets():
            target_config = self.Core.Config.DeriveConfigFromURL(TargetURL)
            #----------- Target model object creation -----------
            config_obj = models.Target(target_url = TargetURL)
            config_obj.host_name = target_config["HOST_NAME"]
            config_obj.host_path = target_config["HOST_PATH"]
            config_obj.url_scheme = target_config["URL_SCHEME"]
            config_obj.port_number = target_config["PORT_NUMBER"]
            config_obj.host_ip = target_config["HOST_IP"]
            config_obj.alternative_ips = str(target_config["ALTERNATIVE_IPS"])
            config_obj.ip_url = target_config["IP_URL"]
            config_obj.top_domain = target_config["TOP_DOMAIN"]
            config_obj.top_url = target_config["TOP_URL"]
            #----------------------------------------------------
            session = self.TargetConfigDBSession()
            session.add(config_obj)
            session.commit()
            session.close()
            self.CreateMissingDBsForURL(TargetURL)
            self.SetTarget(TargetURL)
        else:
            raise general.InvalidTargetException(TargetURL + " already present in Target DB")

    def UpdateTarget(self, data_dict, TargetURL=None, ID=None):
        session = self.TargetConfigDBSession()
        if ID:
            target_obj = session.query(models.Target).get(ID)
        if TargetURL:
            target_obj = session.query(models.Target).filter_by(target_url = TargetURL).one()
        # TODO: Updating all related attributes when one attribute is changed
        for key, value in data.items():
            if key == "IN_CONTEXT":
                setattr(target_obj, key.lower(), bool(value))
        session.merge(target_obj)
        session.commit()
        session.close()

    def DeleteTarget(self, TargetURL=None, ID=None):
        session = self.TargetConfigDBSession()
        if ID:
            target_obj = session.query(models.Target).get(ID)
        if TargetURL:
            target_obj = session.query(models.Target).filter_by(target_url = TargetURL).one()
        if not target_obj:
            raise general.InvalidTargetException("Target doesn't exist: " + str(ID) if ID else str(TargetURL))
        target_url = target_obj.target_url
        session.delete(target_obj)
        session.commit()
        self.Core.DB.CommandRegister.RemoveForTarget(target_url)
        self.Core.Config.CleanUpForTarget(target_url)
        session.close()

    def CreateMissingDBsForURL(self, TargetURL):
        self.Core.Config.CreateDBDirForTarget(TargetURL)
        self.Core.DB.EnsureDBWithBase(self.Core.Config.GetTransactionDBPathForTarget(TargetURL), models.TransactionBase)
        self.Core.DB.EnsureDBWithBase(self.Core.Config.GetUrlDBPathForTarget(TargetURL), models.URLBase)
        self.Core.DB.EnsureDBWithBase(self.Core.Config.GetOutputDBPathForTarget(TargetURL), models.OutputBase)

    def GetTargetConfigForURL(self, TargetUrl):
        session = self.TargetConfigDBSession()
        target_obj = session.query(models.Target).filter_by(target_url = TargetUrl).one()
        session.close()
        return(self.DeriveTargetConfig(target_obj))

    def GetTargetConfigForID(self, ID):
        session = self.TargetConfigDBSession()
        target_obj = session.query(models.Target).get(id = ID)
        session.close()
        if not target_obj:
            raise InvalidTargetException("Target doesn't exist: " + str(ID))
        return(self.DeriveTargetConfig(target_obj))

    def GetTargetConfigs(self, filter_data={}):
        session = self.TargetConfigDBSession()
        query = session.query(models.Target)
        if filter_data.get("TARGET_URL", None):
            query = query.filter_by(target_url = filter_data.get("TARGET_URL"))
        if filter_data.get("HOST_IP", None):
            query = query.filter_by(host_ip = filter_data.get("HOST_IP"))
        if filter_data.get("IN_CONTEXT", None):
            query = query.filter_by(in_context = bool(filter_data.get("IN_CONTEXT")))
        if filter_data.get("HOST_NAME", None):
            query = query.filter_by(host_name = filter_data.get("HOST_NAME"))
        target_obj_list = query.all()
        session.close()
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
        session = self.TargetConfigDBSession()
        results = session.query(getattr(models.Target, Key.lower())).all()
        session.close()
        results = [result[0] for result in results]
        return results

    def GetTargets(self):
        session = self.TargetConfigDBSession()
        targets = session.query(models.Target.target_url).all()
        session.close()
        targets = [i[0] for i in targets]
        return(targets)

    def IsInScopeURL(self, URL): # To avoid following links to other domains
        ParsedURL = urlparse(URL)
        #URLHostName = URL.split("/")[2]
        for HostName in self.GetAll('HOST_NAME'): # Get all known Host Names in Scope
            #if URLHostName == HostName:
            if ParsedURL.hostname == HostName:
                return True
        return False

    def CreateOutputDBSession(self, Target):
        return(self.Core.DB.CreateSession(self.Core.Config.GetOutputDBPathForTarget(Target)))

    def CreateTransactionDBSession(self, Target):
        return(self.Core.DB.CreateSession(self.Core.Config.GetTransactionDBPathForTarget(Target)))

    def CreateUrlDBSession(self, Target):
        return(self.Core.DB.CreateSession(self.Core.Config.GetUrlDBPathForTarget(Target)))

    def GetOutputDBSession(self, Target = None):
        if ((not Target) or (self.Target == Target)):
            return(self.OutputDBSession)
        else:
            return(self.CreateOutputDBSession(Target))

    def GetTransactionDBSession(self, Target = None):
        if ((not Target) or (self.Target == Target)):
            return(self.TransactionDBSession)
        else:
            return(self.CreateTransactionDBSession(Target))

    def GetUrlDBSession(self, Target = None):
        if ((not Target) or (self.Target == Target)):
            return(self.UrlDBSession)
        else:
            return(self.CreateUrlDBSession(Target))
