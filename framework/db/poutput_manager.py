import os
import json
from framework.db.target_manager import target_required
from framework.lib.exceptions import InvalidParameterType
from framework.db import models


class POutputDB(object):
    def __init__(self, Core):
        self.Core = Core

    def DeriveHTMLOutput(self, plugin_output):
        self.Core.Reporter.Loader.reset()
        Content = ''
        for item in plugin_output:
            Content += getattr(
                self.Core.Reporter,
                item["type"])(**item["output"])
        return(Content)

    @target_required
    def DeriveOutputDict(self, obj, target_id=None):
        if obj:
            pdict = dict(obj.__dict__)
            pdict.pop("_sa_instance_state", None)
            # If output is present, json decode it
            if pdict.get("output", None):
                pdict["output"] = self.DeriveHTMLOutput(
                    json.loads(pdict["output"]))
            pdict["start_time"] = obj.start_time.strftime(
                self.Core.DB.Config.Get("DATE_TIME_FORMAT"))
            pdict["end_time"] = obj.end_time.strftime(
                self.Core.DB.Config.Get("DATE_TIME_FORMAT"))
            pdict["run_time"] = self.Core.Timer.get_time_as_str(obj.run_time)
            return pdict

    @target_required
    def DeriveOutputDicts(self, obj_list, target_id=None):
        dict_list = []
        for obj in obj_list:
            dict_list.append(self.DeriveOutputDict(obj, target_id=target_id))
        return(dict_list)

    def GenerateQueryUsingSession(self, filter_data, target_id):
        query = self.Core.DB.session.query(models.PluginOutput).filter_by(target_id=target_id)
        if filter_data.get("target_id", None):
            query.filter_by(target_id=filter_data["target_id"])
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
        return query

    @target_required
    def GetAll(self, filter_data=None, target_id=None):
        if not filter_data:
            filter_data = {}
        self.Core.DB.Target.SetTarget(target_id)
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
            "plugin_type": [i[0] for i in self.Core.DB.session.query(
                models.PluginOutput.plugin_type).filter_by(
                    target_id=target_id).distinct().all()],
            "plugin_group": [i[0] for i in self.Core.DB.session.query(
                models.PluginOutput.plugin_group).filter_by(
                    target_id=target_id).distinct().all()],
            "status": [i[0] for i in self.Core.DB.session.query(
                models.PluginOutput.status).filter_by(
                    target_id=target_id).distinct().all()],
            "user_rank": [i[0] for i in self.Core.DB.session.query(
                models.PluginOutput.user_rank).filter_by(
                    target_id=target_id).distinct().all()],
            "owtf_rank": [i[0] for i in self.Core.DB.session.query(
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
            target_id)  # Empty dict will match all results
        # Delete the folders created for these plugins
        for plugin in query.all():
            # First check if path exists in db
            if plugin.output_path:
                output_path = os.path.join(
                    self.Core.Config.GetOutputDirForTargets(),
                    plugin.output_path)
                if os.path.exists(output_path):
                    self.Core.rmtree(output_path)
        # When folders are removed delete the results from db
        results = query.delete()
        self.Core.DB.session.commit()

    @target_required
    def Update(
            self,
            plugin_group,
            plugin_type,
            plugin_code,
            patch_data,
            target_id=None):
        query = self.GenerateQueryUsingSession(
            {
                "plugin_group": plugin_group,
                "plugin_type": plugin_type,
                "plugin_code": plugin_code,
            },
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
                self.Core.DB.session.merge(obj)
                self.Core.DB.session.commit()
            except ValueError:
                raise InvalidParameterType(
                    "Integer has to be provided for integer fields")

    @target_required
    def PluginAlreadyRun(self, PluginInfo, target_id=None):
        plugin_output_count = self.Core.DB.session.query(models.PluginOutput).filter_by(
            target_id=target_id,
            plugin_code=PluginInfo["code"],
            plugin_type=PluginInfo["type"],
            plugin_group=PluginInfo["group"]).count()
        if plugin_output_count > 0:
            return(True)
        return(False)  # This is nothin but a "None" returned

    @target_required
    def SavePluginOutput(self,
                         plugin,
                         output,
                         target_id=None,
                         owtf_rank=None):
        """Save into the database the command output of the plugin `plugin."""
        self.Core.DB.session.merge(models.PluginOutput(
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
                self.Core.PluginHandler.GetPluginOutputDir(plugin)) else None),
            owtf_rank=owtf_rank)
            )
        self.Core.DB.session.commit()

    @target_required
    def SavePartialPluginOutput(
            self,
            Plugin,
            Output,
            Message,
            target_id=None):
        self.Core.DB.session.merge(models.PluginOutput(
            plugin_key=Plugin["key"],
            plugin_code=Plugin["code"],
            plugin_group=Plugin["group"],
            plugin_type=Plugin["type"],
            output=json.dumps(Output),
            error=Message,
            start_time=Plugin["start"],
            end_time=Plugin["end"],
            status=Plugin["status"],
            target_id=target_id,
            # Save path only if path exists i.e if some files were to be stored
            # it will be there
            output_path=(Plugin["output_path"] if os.path.exists(
                self.Core.PluginHandler.GetPluginOutputDir(Plugin)) else None)
            ))
        self.Core.DB.session.commit()
