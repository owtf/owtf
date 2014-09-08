import os
import sqlalchemy.exc

from urlparse import urlparse

from framework.lib.exceptions import DBIntegrityException, \
                                     InvalidTargetReference, \
                                     InvalidParameterType
from framework.db import models
from framework.db.session_manager import session_required
from framework.lib import general
from framework.lib.general import cprint  # TODO: Shift to logging


TARGET_CONFIG = {
    'id': 0,
    'TARGET_URL': '',
    'host_name': '',
    'host_path': '',
    'url_scheme': '',
    'port_number': '',  # In str form
    'host_ip': '',
    'alternative_ips': '',  # str(list), so it can easily reversed using list(str)
    'ip_url': '',
    'top_domain': '',
    'top_url': '',
    'scope': True,
    "max_user_rank": -1,
    "max_owtf_rank": -1
}

PATH_CONFIG = {
    'partial_url_output_path': '',
    'host_output': '',
    'port_output': '',
    'url_output': '',
    'plugin_output_dir': ''
}


def target_required(func):
    """

    In order to use this decorator on a `method` there are two requirements
    + target_id must be a kwarg of the function
    + Core must be attached to the object at self.Core

    All this decorator does is check if a valid value is passed for target_id
    if not get the target_id from target manager and pass it

    """
    def wrapped_function(*args, **kwargs):
        if ((kwargs.get("target_id", "None") == "None") or
                (kwargs.get("target_id", True) is None)):  # True if target_id doesnt exist.
            kwargs["target_id"] = args[0].Core.DB.Target.GetTargetID()
        return func(*args, **kwargs)
    return wrapped_function


class TargetDB(object):
    # All these variables reflect to current target which is referenced by a
    # unique ID.
    TargetID = None
    TargetConfig = dict(TARGET_CONFIG)
    PathConfig = dict(PATH_CONFIG)

    def __init__(self, Core):
        self.Core = Core

    def SetTarget(self, target_id):
        try:
            self.TargetID = target_id
            self.TargetConfig = self.GetTargetConfigForID(target_id)
            self.PathConfig = self.DerivePathConfig(self.TargetConfig)
        except InvalidTargetReference:
            pass

    def DerivePathConfig(self, target_config):
        path_config = {}
        # Set the output directory.
        path_config['host_output'] = os.path.join(
            self.Core.Config.FrameworkConfigGet('OUTPUT_PATH'),
            target_config['host_ip'])
        path_config['port_output'] = os.path.join(
            path_config['host_output'],
            target_config['port_number'])
        # Set the URL output directory (plugins will save their data here).
        path_config['url_output'] = os.path.join(
            self.Core.Config.GetOutputDirForTarget(target_config['TARGET_URL']))
        # Set the partial results path.
        path_config['partial_url_output_path'] = os.path.join(
            path_config['url_output'],
            'partial')
        return path_config

    def GetTargetID(self):
        return self.TargetID

    def GetTargetURL(self):
        return self.Get("TARGET_URL")

    def GetTargetURLs(self):
        return self.GetAll("TARGET_URL")

    def GetIndexedTargets(self):
        results = self.Core.DB.session.query(
            models.Target.id,
            models.Target.target_url).all()
        return results

    def GetTargetConfig(self):
        return self.TargetConfig

    def GetPathConfig(self):
        return self.PathConfig

    def GetPath(self, output_type):
        return self.PathConfig.get(output_type, None)

    def SetPath(self, output_type, path):
        # Mainly used for setting output paths for individual plugins, which
        # need not be saved: plugin_output_dir.
        self.PathConfig[output_type] = path

    def DBHealthCheck(self):
        # Target DB Health Check
        target_list = self.Core.DB.session.query(models.Target).all()
        if target_list:
            # If needed in order to prevent an uninitialized value for target
            # in self.SetTarget(target) few lines later.
            for target in target_list:
                self.Core.DB.Target.CreateMissingDBsForURL(target.target_url)
            # This is to avoid "None" value for the main settings.
            self.SetTarget(target.id)

    @session_required
    def AddTarget(self, TargetURL, session_id=None):
        if TargetURL not in self.GetTargetURLs():
            # A try-except can be used here, but then ip-resolution takes time
            # even if target is present
            target_config = self.Core.Config.DeriveConfigFromURL(TargetURL)
            # ----------- Target model object creation -----------
            config_obj = models.Target(target_url=TargetURL)
            config_obj.host_name = target_config["host_name"]
            config_obj.host_path = target_config["host_path"]
            config_obj.url_scheme = target_config["url_scheme"]
            config_obj.port_number = target_config["port_number"]
            config_obj.host_ip = target_config["host_ip"]
            config_obj.alternative_ips = str(target_config["alternative_ips"])
            config_obj.ip_url = target_config["ip_url"]
            config_obj.top_domain = target_config["top_domain"]
            config_obj.top_url = target_config["top_url"]
            # ----------------------------------------------------
            self.Core.DB.session.add(config_obj)
            config_obj.sessions.append(
                self.Core.DB.session.query(models.Session).get(session_id))
            self.Core.DB.session.commit()
            target_id = config_obj.id
            self.CreateMissingDBsForURL(TargetURL)
            self.SetTarget(target_id)
        else:
            session_obj = self.Core.DB.session.query(
                models.Session).get(session_id)
            target_obj = self.Core.DB.session.query(
                models.Target).filter_by(target_url=TargetURL).one()
            if session_obj in target_obj.sessions:
                raise DBIntegrityException(
                    TargetURL + " already present in Target DB & session")
            else:
                self.Core.DB.OWTFSession.add_target_to_session(
                    target_obj.id,
                    session_id=session_obj.id)

    @session_required
    def AddTargets(self, target_urls, session_id=None):
        for target_url in target_urls:
            self.AddTarget(target_url, session_id=session_id)

    def UpdateTarget(self, data_dict, TargetURL=None, ID=None):
        if ID:
            target_obj = self.Core.DB.session.query(models.Target).get(ID)
        if TargetURL:
            target_obj = self.Core.DB.session.query(models.Target).filter_by(
                target_url=TargetURL).one()
        if not target_obj:
            raise InvalidTargetReference(
                "Target doesn't exist: " + str(ID) if ID else str(TargetURL))
        # TODO: Updating all related attributes when one attribute is changed
        if data_dict.get("scope", None) is not None:
            target_obj.scope = self.Core.Config.ConvertStrToBool(value)
        self.Core.DB.session.commit()

    def DeleteTarget(self, TargetURL=None, ID=None):
        if ID:
            target_obj = self.Core.DB.session.query(models.Target).get(ID)
        if TargetURL:
            target_obj = self.Core.DB.session.query(models.Target).filter_by(
                target_url=TargetURL).one()
        if not target_obj:
            raise InvalidTargetReference(
                "Target doesn't exist: " + str(ID) if ID else str(TargetURL))
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
            raise InvalidTargetReference(
                "Target doesn't exist with ID: " + str(ID))
        return(target_obj.target_url)

    def GetTargetConfigForID(self, ID):
        target_obj = self.Core.DB.session.query(models.Target).get(ID)
        if not target_obj:
            raise InvalidTargetReference("Target doesn't exist: " + str(ID))
        return(self.DeriveTargetConfig(target_obj))

    @session_required
    def GetTargetConfigs(self, filter_data=None, session_id=None):
        if filter_data is None:
            filter_data = {}
        query = self.Core.DB.session.query(models.Target).filter(
            models.Target.sessions.any(id=session_id))
        if filter_data.get("TARGET_URL", None):
            if isinstance(filter_data["TARGET_URL"], (str, unicode)):
                query = query.filter_by(target_url=filter_data["TARGET_URL"])
            if isinstance(filter_data["TARGET_URL"], list):
                query = query.filter(models.Target.target_url.in_(
                    filter_data.get("TARGET_URL")))
        if filter_data.get("host_ip", None):
            if isinstance(filter_data["host_ip"], (str, unicode)):
                query = query.filter_by(host_ip=filter_data["host_ip"])
            if isinstance(filter_data["host_ip"], list):
                query = query.filter(models.Target.host_ip.in_(
                    filter_data.get("host_ip")))
        if filter_data.get("scope", None):
            filter_data["scope"] = filter_data["scope"][0]
            query = query.filter_by(
                scope=self.Core.Config.ConvertStrToBool(filter_data.get("scope")))
        if filter_data.get("host_name", None):
            if isinstance(filter_data["host_name"], (str, unicode)):
                query = query.filter_by(host_name=filter_data["host_name"])
            if isinstance(filter_data["host_name"], list):
                query = query.filter(models.Target.host_name.in_(
                    filter_data.get("host_name")))
        try:
            if filter_data.get("id", None):
                if isinstance(filter_data["id"], (str, unicode)):
                    query = query.filter_by(id=filter_data["id"])
                if isinstance(filter_data["id"], list):
                    query = query.filter(models.Target.id.in_(filter_data.get("id")))
            if filter_data.get('id[lt]', None):
                if isinstance(filter_data.get('id[lt]'), list):
                    filter_data['id[lt]'] = filter_data['id[lt]'][0]
                query = query.filter(models.Target.id < int(filter_data['id[lt]']))
            if filter_data.get('id[gt]', None):
                if isinstance(filter_data.get('id[gt]'), list):
                    filter_data['id[gt]'] = filter_data['id[gt]'][0]
                query = query.filter(models.Target.id > int(filter_data['id[gt]']))
        except ValueError:
            raise InvalidParameterType(
                "Invalid parameter type for target db for id[lt] or id[gt]")
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
        results = self.Core.DB.session.query(
            getattr(models.Target, Key.lower())).all()
        results = [result[0] for result in results]
        return results

    def GetAllInScope(self, Key):
        results = self.Core.DB.session.query(
            getattr(models.Target, Key.lower())).filter_by(scope=True).all()
        results = [result[0] for result in results]
        return results

    def IsInScopeURL(self, URL):  # To avoid following links to other domains.
        ParsedURL = urlparse(URL)
        # Get all known Host Names in Scope.
        for HostName in self.GetAll('host_name'):
            if ParsedURL.hostname == HostName:
                return True
        return False
