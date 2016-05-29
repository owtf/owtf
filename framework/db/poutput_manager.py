import os
import json
from framework.dependency_management.dependency_resolver import BaseComponent
from framework.dependency_management.interfaces import PluginOutputInterface
from framework.db.target_manager import target_required
from framework.lib.exceptions import InvalidParameterType
from framework.db import models
from framework.utils import FileOperations


class POutputDB(BaseComponent, PluginOutputInterface):

    COMPONENT_NAME = "plugin_output"

    def __init__(self):
        self.register_in_service_locator()
        self.config = self.get_component("config")
        self.plugin_handler = self.get_component("plugin_handler")
        self.reporter = self.get_component("reporter")
        self.target = self.get_component("target")
        self.db_config = self.get_component("db_config")
        self.timer = self.get_component("timer")
        self.db = self.get_component("db")

    def PluginOutputExists(self, plugin_key, target_id):
        count = self.db.session.query(models.PluginOutput).filter_by(target_id=target_id, plugin_key=plugin_key).count()
        return (count > 0)

    def PluginCountOutput(self):
        complete_count = self.db.session.query(models.PluginOutput).count()
        left_count = self.db.session.query(models.Work).count()
        results = {'complete_count': complete_count, 'left_count': left_count}
        return results

    def DeriveHTMLOutput(self, plugin_output):
        Content = ''
        for item in plugin_output:
            Content += getattr(
                self.reporter,
                item["type"])(**item["output"])
        return(Content)

    @target_required
    def DeriveOutputDict(self, obj, target_id=None):
        if target_id:
            self.target.SetTarget(target_id)
        if obj:
            pdict = dict(obj.__dict__)
            pdict.pop("_sa_instance_state", None)
            pdict.pop("date_time")
            # If output is present, json decode it
            if pdict.get("output", None):
                pdict["output"] = self.DeriveHTMLOutput(
                    json.loads(pdict["output"]))
            pdict["start_time"] = obj.start_time.strftime(
                self.db_config.Get("DATE_TIME_FORMAT"))
            pdict["end_time"] = obj.end_time.strftime(
                self.db_config.Get("DATE_TIME_FORMAT"))
            pdict["run_time"] = self.timer.get_time_as_str(obj.run_time)
            return pdict

    @target_required
    def DeriveOutputDicts(self, obj_list, target_id=None):
        if target_id:
            self.target.SetTarget(target_id)
        dict_list = []
        for obj in obj_list:
            dict_list.append(self.DeriveOutputDict(obj, target_id=target_id))
        return(dict_list)

    def GenerateQueryUsingSession(self, filter_data, target_id, for_delete=False):
        query = self.db.session.query(models.PluginOutput).filter_by(target_id=target_id)
        if filter_data.get("target_id", None):
            query.filter_by(target_id=filter_data["target_id"])
        if filter_data.get("plugin_key", None):
            if isinstance(filter_data.get("plugin_key"), (str, unicode)):
                query = query.filter_by(plugin_key=filter_data["plugin_key"])
            if isinstance(filter_data.get("plugin_key"), list):
                query = query.filter(models.PluginOutput.plugin_key.in_(
                    filter_data["plugin_key"]))
        if filter_data.get("plugin_type", None):
            if isinstance(filter_data.get("plugin_type"), (str, unicode)):
                query = query.filter_by(plugin_type=filter_data["plugin_type"])
            if isinstance(filter_data.get("plugin_type"), list):
                query = query.filter(models.PluginOutput.plugin_type.in_(
                    filter_data["plugin_type"]))
        if filter_data.get("plugin_group", None):
            if isinstance(filter_data.get("plugin_group"), (str, unicode)):
                query = query.filter_by(
                    plugin_group=filter_data["plugin_group"])
            if isinstance(filter_data.get("plugin_group"), list):
                query = query.filter(models.PluginOutput.plugin_group.in_(
                    filter_data["plugin_group"]))
        if filter_data.get("plugin_code", None):
            if isinstance(filter_data.get("plugin_code"), (str, unicode)):
                query = query.filter_by(plugin_code=filter_data["plugin_code"])
            if isinstance(filter_data.get("plugin_code"), list):
                query = query.filter(models.PluginOutput.plugin_code.in_(
                    filter_data["plugin_code"]))
        if filter_data.get("status", None):
            if isinstance(filter_data.get("status"), (str, unicode)):
                query = query.filter_by(status=filter_data["status"])
            if isinstance(filter_data.get("status"), list):
                query = query.filter(models.PluginOutput.status.in_(
                    filter_data["status"]))
        try:
            if filter_data.get("user_rank", None):
                if isinstance(filter_data.get("user_rank"), (str, unicode)):
                    query = query.filter_by(
                        user_rank=int(filter_data["user_rank"]))
                if isinstance(filter_data.get("user_rank"), list):
                    numbers_list = [int(x) for x in filter_data["user_rank"]]
                    query = query.filter(models.PluginOutput.user_rank.in_(
                        numbers_list))
            if filter_data.get("owtf_rank", None):
                if isinstance(filter_data.get("owtf_rank"), (str, unicode)):
                    query = query.filter_by(
                        owtf_rank=int(filter_data["owtf_rank"]))
                if isinstance(filter_data.get("owtf_rank"), list):
                    numbers_list = [int(x) for x in filter_data["owtf_rank"]]
                    query = query.filter(models.PluginOutput.owtf_rank.in_(
                        numbers_list))
        except ValueError:
            raise InvalidParameterType(
                "Integer has to be provided for integer fields")
        if not for_delete:
            query = query.order_by(models.PluginOutput.plugin_key.asc())
        return query

    @target_required
    def GetAll(self, filter_data=None, target_id=None):
        if not filter_data:
            filter_data = {}
        self.target.SetTarget(target_id)
        query = self.GenerateQueryUsingSession(filter_data, target_id)
        results = query.all()
        return(self.DeriveOutputDicts(results, target_id=target_id))

    @target_required
    def GetUnique(self, target_id=None):
        """
        Returns a dict of some column names and their unique database
        Useful for advanced filter
        """
        unique_data = {
            "plugin_type": [i[0] for i in self.db.session.query(
                models.PluginOutput.plugin_type).filter_by(
                    target_id=target_id).distinct().all()],
            "plugin_group": [i[0] for i in self.db.session.query(
                models.PluginOutput.plugin_group).filter_by(
                    target_id=target_id).distinct().all()],
            "status": [i[0] for i in self.db.session.query(
                models.PluginOutput.status).filter_by(
                    target_id=target_id).distinct().all()],
            "user_rank": [i[0] for i in self.db.session.query(
                models.PluginOutput.user_rank).filter_by(
                    target_id=target_id).distinct().all()],
            "owtf_rank": [i[0] for i in self.db.session.query(
                models.PluginOutput.owtf_rank).filter_by(
                    target_id=target_id).distinct().all()],
        }
        return(unique_data)

    @target_required
    def DeleteAll(self, filter_data, target_id=None):
        """
        Here keeping filter_data optional is very risky
        """
        query = self.GenerateQueryUsingSession(
            filter_data,
            target_id,
            for_delete=True)  # Empty dict will match all results
        # Delete the folders created for these plugins
        for plugin in query.all():
            # First check if path exists in db
            if plugin.output_path:
                output_path = os.path.join(
                    self.config.GetOutputDirForTargets(),
                    plugin.output_path)
                if os.path.exists(output_path):
                    FileOperations.rm_tree(output_path)
        # When folders are removed delete the results from db
        results = query.delete()
        self.db.session.commit()

    @target_required
    def Update(self, plugin_group, plugin_type, plugin_code, patch_data, target_id=None):
        query = self.GenerateQueryUsingSession({
                "plugin_group": plugin_group,
                "plugin_type": plugin_type,
                "plugin_code": plugin_code,},
            target_id)
        obj = query.first()
        if obj:
            try:
                if patch_data.get("user_rank", None):
                    if isinstance(patch_data["user_rank"], list):
                        patch_data["user_rank"] = patch_data["user_rank"][0]
                    obj.user_rank = int(patch_data["user_rank"])
                if patch_data.get("user_notes", None):
                    if isinstance(patch_data["user_notes"], list):
                        patch_data["user_notes"] = patch_data["user_notes"][0]
                    obj.user_notes = patch_data["user_notes"]
                self.db.session.merge(obj)
                self.db.session.commit()
            except ValueError:
                raise InvalidParameterType("Integer has to be provided for integer fields")

    def PluginAlreadyRun(self, PluginInfo, target_id=None):
        plugin_output_count = self.db.session.query(models.PluginOutput).filter_by(
            target_id=target_id,
            plugin_code=PluginInfo["code"],
            plugin_type=PluginInfo["type"],
            plugin_group=PluginInfo["group"]).count()
        return plugin_output_count > 0 # This is nothin but a "None" returned

    @target_required
    def SavePluginOutput(self, plugin, output, target_id=None):
        """Save into the database the command output of the plugin `plugin."""
        self.db.session.merge(models.PluginOutput(
            plugin_key=plugin["key"],
            plugin_code=plugin["code"],
            plugin_group=plugin["group"],
            plugin_type=plugin["type"],
            output=json.dumps(output),
            start_time=plugin["start"],
            end_time=plugin["end"],
            status=plugin["status"],
            target_id=target_id,
            # Save path only if path exists i.e if some files were to be stored
            # it will be there
            output_path=(plugin["output_path"] if os.path.exists(
                self.plugin_handler.GetPluginOutputDir(plugin)) else None),
            owtf_rank=plugin['owtf_rank'])
        )
        self.db.session.commit()

    @target_required
    def SavePartialPluginOutput(self, plugin, output, message, target_id=None):
        self.db.session.merge(models.PluginOutput(
            plugin_key=plugin["key"],
            plugin_code=plugin["code"],
            plugin_group=plugin["group"],
            plugin_type=plugin["type"],
            output=json.dumps(output),
            error=message,
            start_time=plugin["start"],
            end_time=plugin["end"],
            status=plugin["status"],
            target_id=target_id,
            # Save path only if path exists i.e if some files were to be stored
            # it will be there
            output_path=(plugin["output_path"] if os.path.exists(
                self.plugin_handler.GetPluginOutputDir(plugin)) else None),
            owtf_rank=plugin['owtf_rank'])
        )
        self.db.session.commit()
