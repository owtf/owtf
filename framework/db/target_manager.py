from framework.db import models
import os

TARGET_CONFIG = {
                    'TARGET_URL' : '', 
                    'HOST_NAME' : '',
                    'HOST_PATH' : '',
                    'URL_SCHEME' : '',
                    'PORT_NUMBER' : '', # In str form
                    'HOST_IP' : '',
                    'ALTERNATIVE_IPS' : '', # str(list), so it can easily reversed using list(str)
                    'IP_URL' : '',
                    'TOP_DOMAIN' : '',
                    'TOP_URL' : ''
                }

PATH_CONFIG = {
                    'PARTIAL_URL_OUTPUT_PATH' : '',
                    'HOST_OUTPUT' : '',
                    'PORT_OUTPUT' : '',
                    'URL_OUTPUT' : '',
                    'PLUGIN_OUTPUT_DIR' : ''
              }

class TargetDB(object):
    Target = None
    TargetConfig = dict(TARGET_CONFIG)
    PathConfig = dict(PATH_CONFIG)
    def __init__(self, Core):
        self.Core = Core
        self.TargetConfigDBSession = self.Core.DB.CreateScopedSession(os.path.expanduser(self.Core.Config.FrameworkConfigGet("TARGET_CONFIG_DB_PATH")), models.TargetBase)
        self.TargetDBHealthCheck()

    def SetTarget(self, target_url):
        if target_url in self.GetTargets():
            self.Target = target_url
            self.TargetConfig = self.GetTargetConfigForURL(target_url)
            self.PathConfig = self.GetPathConfigForTargetConfig(self.TargetConfig)

    def GetPathConfigForTargetConfig(self, target_config):
        path_config = {}
        path_config['HOST_OUTPUT'] = os.path.join(self.Core.Config.Get('OUTPUT_PATH'), target_config['HOST_IP']) # Set the output directory
        path_config['PORT_OUTPUT'] = os.path.join(path_config['HOST_OUTPUT'], target_config['PORT_NUMBER']) # Set the output directory
        URLInfoID = target_config['TARGET_URL'].replace('/','_').replace(':','')
        path_config['URL_OUTPUT'] = os.path.join(path_config['PORT_OUTPUT'], URLInfoID) # Set the URL output directory (plugins will save their data here)
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

    def TargetDBHealthCheck(self):
        session = self.TargetConfigDBSession()
        target_list = session.query(models.Target).all()
        for target in target_list:
            self.Core.Config.Targets.append(target.url)
            self.Core.DB.EnsureDBsForTarget(target.url)

    def AddTarget(self, TargetURL):
        target_config = self.Core.Config.DeriveConfigFromURL(TargetURL)
        config_obj = models.Target(target_url = TargetURL)
        for key, value in target_config.items():
            key = key.lower()
            setattr(config_obj, key, str(value))
        session = self.TargetConfigDBSession()
        session.merge(config_obj)
        session.commit()
        session.close()
        self.EnsureDBsForTarget(TargetURL)

    def EnsureDBsForTarget(self, TargetURL):
        self.Core.Config.CreateDBDirForTarget(TargetURL)
        self.Core.DB.EnsureDBWithBase(self.Core.Config.GetTransactionDBPathForTarget(TargetURL), models.TransactionBase)
        self.Core.DB.EnsureDBWithBase(self.Core.Config.GetUrlDBPathForTarget(TargetURL), models.URLBase)
        self.Core.DB.EnsureDBWithBase(self.Core.Config.GetReviewDBPathForTarget(TargetURL), models.ReviewWebBase)

    def GetTargetConfigForURL(self, target_url):
        session = self.TargetConfigDBSession()
        target_obj = session.query(models.Target).get(target_url)
        session.close()
        target_config = {}
        if target_obj:
            for key in TARGET_CONFIG.keys():
                target_config[key] = getattr(target_obj, key.lower())
        return target_config

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
