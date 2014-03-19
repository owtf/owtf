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

class TargetDB(object):
    def __init__(self, Core):
        self.Core = Core
        self.TargetConfigDBSession = self.Core.DB.CreateScopedSession(os.path.expanduser(self.Core.Config.FrameworkConfigGet("TARGET_CONFIG_DB_PATH")), models.TargetBase)
        self.TargetDBHealthCheck()

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

    def GetTargetConfigFromDB(self, target_url):
        session = self.TargetConfigDBSession()
        target_obj = session.query(models.Target).get(target_url)
        target_config = {}
        if target_obj:
            for key in TARGET_CONFIG.keys():
                target_config[key] = getattr(target_obj, key.lower())
        return target_config

    def GetAll(self, Key):
        session = self.TargetConfigDBSession()
        results = session.query(getattr(models.Target, Key.lower())).all()
        results = [result[0] for result in results]
        return results
