import os
import datetime
from urlparse import urlparse

from framework.dependency_management.dependency_resolver import BaseComponent, ServiceLocator
from framework.dependency_management.interfaces import TargetInterface
from framework.lib.exceptions import DBIntegrityException, InvalidTargetReference, InvalidParameterType
from framework.db import models
from framework.db.session_manager import session_required
from framework.lib.general import cprint  # TODO: Shift to logging


TARGET_CONFIG = {
    'id': 0,
    'target_url': '',
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
        if "target_id" not in kwargs:
            kwargs["target_id"] = ServiceLocator.get_component("target").GetTargetID()
        return func(*args, **kwargs)
    return wrapped_function


class TargetDB(BaseComponent, TargetInterface):
    # All these variables reflect to current target which is referenced by a unique ID
    TargetID = None
    TargetConfig = dict(TARGET_CONFIG)
    PathConfig = dict(PATH_CONFIG)

    COMPONENT_NAME = "target"

    def __init__(self):
        self.register_in_service_locator()
        self.config = self.get_component("config")
        self.command_register = self.get_component("command_register")
        self.db = self.get_component("db")

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
        path_config['host_output'] = os.path.join(self.config.FrameworkConfigGet('OUTPUT_PATH'),
                                                  target_config['host_ip'])
        path_config['port_output'] = os.path.join(path_config['host_output'], target_config['port_number'])
        # Set the URL output directory (plugins will save their data here).
        path_config['url_output'] = os.path.join(self.config.GetOutputDirForTarget(target_config['target_url']))
        # Set the partial results path.
        path_config['partial_url_output_path'] = os.path.join(path_config['url_output'], 'partial')
        return path_config

    def GetTargetID(self):
        return self.TargetID

    def GetTargetURL(self):
        return self.Get("target_url")

    def GetTargetURLs(self):
        return self.GetAll("target_url")

    def GetIndexedTargets(self):
        results = self.db.session.query(models.Target.id, models.Target.target_url).all()
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
        target_list = self.db.session.query(models.Target).all()
        if target_list:
            # If needed in order to prevent an uninitialized value for target
            # in self.SetTarget(target) few lines later.
            for target in target_list:
                self.CreateMissingDBsForURL(target.target_url)
            # This is to avoid "None" value for the main settings.
            self.SetTarget(target.id)

    @session_required
    def AddTarget(self, target_url, session_id=None):
        if target_url not in self.GetTargetURLs():
            # A try-except can be used here, but then ip-resolution takes time
            # even if target is present
            target_config = self.config.DeriveConfigFromURL(target_url)
            # ----------- Target model object creation -----------
            config_obj = models.Target(target_url=target_url)
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
            self.db.session.add(config_obj)
            config_obj.sessions.append(self.db.session.query(models.Session).get(session_id))
            self.db.session.commit()
            target_id = config_obj.id
            self.CreateMissingDBsForURL(target_url)
            self.SetTarget(target_id)
        else:
            session_obj = self.db.session.query(models.Session).get(session_id)
            target_obj = self.db.session.query(models.Target).filter_by(target_url=target_url).one()
            if session_obj in target_obj.sessions:
                raise DBIntegrityException("%s already present in Target DB & session" % target_url)
            else:
                self.db.OWTFSession.add_target_to_session(target_obj.id, session_id=session_obj.id)

    @session_required
    def AddTargets(self, target_urls, session_id=None):
        for target_url in target_urls:
            self.AddTarget(target_url, session_id=session_id)

    def UpdateTarget(self, data_dict, TargetURL=None, ID=None):
        target_obj = None
        if ID:
            target_obj = self.db.session.query(models.Target).get(ID)
        if TargetURL:
            target_obj = self.db.session.query(models.Target).filter_by(target_url=TargetURL).one()
        if not target_obj:
            raise InvalidTargetReference("Target doesn't exist: %s" % str(ID) if ID else str(TargetURL))
        # TODO: Updating all related attributes when one attribute is changed
        if data_dict.get("scope", None) is not None:
            target_obj.scope = self.config.ConvertStrToBool(data_dict.get("scope", None))
        self.db.session.commit()

    def DeleteTarget(self, TargetURL=None, ID=None):
        if ID:
            target_obj = self.db.session.query(models.Target).get(ID)
        if TargetURL:
            target_obj = self.db.session.query(models.Target).filter_by(target_url=TargetURL).one()
        if not target_obj:
            raise InvalidTargetReference("Target doesn't exist: %s" % str(ID) if ID else str(TargetURL))
        target_url = target_obj.target_url
        self.db.session.delete(target_obj)
        self.db.session.commit()
        self.config.CleanUpForTarget(target_url)

    def CreateMissingDBsForURL(self, TargetURL):
        self.config.CreateOutputDirForTarget(TargetURL)

    def GetTargetURLForID(self, ID):
        target_obj = self.db.session.query(models.Target).get(ID)
        if not target_obj:
            cprint("Failing with ID: %s" % str(ID))
            raise InvalidTargetReference("Target doesn't exist with ID: %s" % str(ID))
        return target_obj.target_url

    def GetTargetConfigForID(self, ID):
        target_obj = self.db.session.query(models.Target).get(ID)
        if not target_obj:
            raise InvalidTargetReference("Target doesn't exist: %s" % str(ID))
        return self.DeriveTargetConfig(target_obj)

    def _generate_query(self, filter_data, session_id, for_stats=False):
        query = self.db.session.query(models.Target).filter(models.Target.sessions.any(id=session_id))
        if filter_data.get("search") is not None:
            if filter_data.get('target_url', None):
                if isinstance(filter_data.get('target_url'), list):
                    filter_data['target_url'] = filter_data['target_url'][0]
                query = query.filter(models.Target.target_url.like("%%%s%%" % filter_data['target_url']))
        else:
            if filter_data.get("target_url", None):
                if isinstance(filter_data["target_url"], (str, unicode)):
                    query = query.filter_by(target_url=filter_data["target_url"])
                if isinstance(filter_data["target_url"], list):
                    query = query.filter(models.Target.target_url.in_(filter_data.get("target_url")))
            if filter_data.get("host_ip", None):
                if isinstance(filter_data["host_ip"], (str, unicode)):
                    query = query.filter_by(host_ip=filter_data["host_ip"])
                if isinstance(filter_data["host_ip"], list):
                    query = query.filter(models.Target.host_ip.in_(filter_data.get("host_ip")))
            if filter_data.get("scope", None):
                filter_data["scope"] = filter_data["scope"][0]
                query = query.filter_by(scope=self.config.ConvertStrToBool(filter_data.get("scope")))
            if filter_data.get("host_name", None):
                if isinstance(filter_data["host_name"], (str, unicode)):
                    query = query.filter_by(host_name=filter_data["host_name"])
                if isinstance(filter_data["host_name"], list):
                    query = query.filter(models.Target.host_name.in_(filter_data.get("host_name")))
            if filter_data.get("id", None):
                if isinstance(filter_data["id"], (str, unicode)):
                    query = query.filter_by(id=filter_data["id"])
                if isinstance(filter_data["id"], list):
                    query = query.filter(models.Target.id.in_(filter_data.get("id")))
        # This will allow new targets to be at the start
        query = query.order_by(models.Target.id.desc())
        if not for_stats:  # query for stats shouldn't have limit and offset
            try:
                if filter_data.get('offset', None):
                    if isinstance(filter_data.get('offset'), list):
                        filter_data['offset'] = filter_data['offset'][0]
                    query = query.offset(int(filter_data['offset']))
                if filter_data.get('limit', None):
                    if isinstance(filter_data.get('limit'), list):
                        filter_data['limit'] = filter_data['limit'][0]
                    if int(filter_data['limit']) != -1:
                        query = query.limit(int(filter_data['limit']))
            except ValueError:
                raise InvalidParameterType("Invalid parameter type for target db for id[lt] or id[gt]")
        return query

    @session_required
    def SearchTargetConfigs(self, filter_data=None, session_id=None):
        # Three things needed
        # + Total number of targets
        # + Filtered target dicts
        # + Filtered number of targets
        total = self.db.session.query(models.Target).filter(models.Target.sessions.any(id=session_id)).count()
        filtered_target_objs = self._generate_query(filter_data, session_id).all()
        filtered_number = self._generate_query(filter_data, session_id, for_stats=True).count()
        results = {
            "records_total": total,
            "records_filtered": filtered_number,
            "data": self.DeriveTargetConfigs(filtered_target_objs)
        }
        return results

    @session_required
    def GetTargetConfigs(self, filter_data=None, session_id=None):
        if filter_data is None:
            filter_data = {}
        target_obj_list = self._generate_query(filter_data, session_id).all()
        return self.DeriveTargetConfigs(target_obj_list)

    def DeriveTargetConfig(self, target_obj):
        target_config = dict(TARGET_CONFIG)
        if target_obj:
            for key in TARGET_CONFIG.keys():
                target_config[key] = getattr(target_obj, key)
            return target_config
        return None

    def DeriveTargetConfigs(self, target_obj_list):
        target_configs = []
        for target_obj in target_obj_list:
            target_configs.append(self.DeriveTargetConfig(target_obj))
        return target_configs

    def Get(self, Key):
        return self.TargetConfig[Key]

    def GetAsList(self, key_list):
        values = []
        for key in key_list:
            values.append(self.Get(key))
        return values

    def GetAll(self, Key):
        results = self.db.session.query(getattr(models.Target, Key.lower())).all()
        results = [result[0] for result in results]
        return results

    def GetAllInScope(self, Key):
        results = self.db.session.query(getattr(models.Target, Key.lower())).filter_by(scope=True).all()
        results = [result[0] for result in results]
        return results

    def IsInScopeURL(self, URL):  # To avoid following links to other domains.
        ParsedURL = urlparse(URL)
        # Get all known Host Names in Scope.
        for HostName in self.GetAll('host_name'):
            if ParsedURL.hostname == HostName:
                return True
        return False

    def GetRecentlyFinishedTargets(self):
        results = []
        time15min = datetime.datetime.now() - datetime.timedelta(minutes=15)
        completed_targets = self.db.session.query(models.PluginOutput.target_id).filter(models.PluginOutput.end_time>=time15min).distinct(models.PluginOutput.target_id)
        running_targets = self.db.session.query(models.Work.target_id).distinct(models.Work.target_id)
        list_completed_targets = [target[0] for target in completed_targets]
        list_running_targets = [target[0] for target in running_targets]
        recently_finished_targets = [x for x in list_completed_targets if x not in list_running_targets]
        for target in recently_finished_targets:
            values = {}
            target_obj = self.db.session.query(models.Target).filter_by(id=target)
            values['target_id'] = target_obj[0].id
            values['target_url'] = target_obj[0].target_url
            results.append(values)
        return ({"data": results})

    @session_required
    def GetTargetsSeverityCount(self, session_id=None):
        filtered_severity_objs = []
        # "not ranked" = gray, "passing" = light green, "info" = light sky blue, "low" = blue, medium = yellow, high = red, critical = dark purple
        severity_frequency = [
            {"id":0, "label": "Not Ranked", "value": 0, "color": "#A9A9A9"},
            {"id":1, "label": "Passing", "value": 0, "color": "#32CD32"},
            {"id":2, "label": "Info", "value": 0, "color": "#b1d9f4"},
            {"id":3, "label": "Low", "value": 0, "color": "#337ab7"},
            {"id":4, "label": "Medium", "value": 0, "color": "#ffcc00"},
            {"id":5, "label": "High", "value": 0, "color": "#c12e2a"},
            {"id":6, "label": "Critical", "value": 0, "color": "#800080"}
        ]
        total = self.db.session.query(models.Target).filter(models.Target.sessions.any(id=session_id)).count()
        target_objs = self.db.session.query(models.Target).filter(models.Target.sessions.any(id=session_id)).all()

        for target_obj in target_objs:
            if target_obj.max_user_rank != -1:
                severity_frequency[target_obj.max_user_rank + 1]["value"] += 100 / total
            else:
                severity_frequency[target_obj.max_owtf_rank + 1]["value"] += 100 / total

        for severity in severity_frequency:
            if severity["value"] != 0:
                filtered_severity_objs.append(severity)

        return {"data": filtered_severity_objs}
