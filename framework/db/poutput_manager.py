from framework.db import models
import json

class POutputDB(object):
    def __init__(self, Core):
        self.Core = Core

    def DeriveOutputDict(self, obj):
        if obj:
            pdict = dict(obj.__dict__)
            pdict.pop("_sa_instance_state", None)
            if pdict.get("output", None): # If output is present, json decode it
                pdict["output"] = json.loads(pdict["output"])
            if pdict.get("date_time", None):
                pdict["date_time"] = pdict["date_time"].strftime(self.Core.DB.Config.Get("DATE_TIME_FORMAT"))
            return pdict

    def DeriveOutputDicts(self, obj_list):
        dict_list = []
        for obj in obj_list:
            dict_list.append(self.DeriveOutputDict(obj))
        return(dict_list)

    def GenerateQueryUsingSession(self, session, filter_data):
        query = session.query(models.PluginOutput)
        if filter_data.get("plugin_type", None):
            if isinstance(filter_data.get("plugin_type"), str) or isinstance(filter_data.get("plugin_type"), unicode):
                query = query.filter_by(plugin_type = filter_data["plugin_type"])
            if isinstance(filter_data.get("plugin_type"), list):
                query = query.filter(models.PluginOutput.plugin_type.in_(filter_data["plugin_type"]))
        if filter_data.get("plugin_group", None):
            if isinstance(filter_data.get("plugin_group"), str) or isinstance(filter_data.get("plugin_group"), unicode):
                query = query.filter_by(plugin_group = filter_data["plugin_group"])
            if isinstance(filter_data.get("plugin_type"), list):
                query = query.filter(models.PluginOutput.plugin_group.in_(filter_data["plugin_group"]))
        if filter_data.get("plugin_code", None):
            if isinstance(filter_data.get("plugin_code"), str) or isinstance(filter_data.get("plugin_code"), unicode):
                query = query.filter_by(plugin_code = filter_data["plugin_code"])
            if isinstance(filter_data.get("plugin_code"), list):
                query = query.filter(models.PluginOutput.plugin_code.in_(filter_data["plugin_code"]))
        if filter_data.get("status", None):
            if isinstance(filter_data.get("status"), str) or isinstance(filter_data.get("status"), unicode):
                query = query.filter_by(status = filter_data["status"])
            if isinstance(filter_data.get("status"), list):
                query = query.filter(models.PluginOutput.status.in_(filter_data["status"]))
        try:
            if filter_data.get("owtf_rank[lt]", None):
                if isinstance(filter_data.get("owtf_rank[lt]"), list):
                    filter_data["owtf_rank[lt]"] = filter_data["owtf_rank[lt]"][0]
                query = query.filter_by(owtf_rank < int(filter_data["owtf_rank[lt]"]))
            if filter_data.get("owtf_rank[gt]", None):
                if isinstance(filter_data.get("owtf_rank[gt]"), list):
                    filter_data["owtf_rank[gt]"] = filter_data["owtf_rank[gt]"][0]
                query = query.filter_by(owtf_rank > int(filter_data["owtf_rank[gt]"]))
            if filter_data.get("user_rank[lt]", None):
                if isinstance(filter_data.get("user_rank[lt]"), list):
                    filter_data["user_rank[lt]"] = filter_data["user_rank[lt]"][0]
                query = query.filter_by(user_rank < int(filter_data["user_rank[lt]"]))
            if filter_data.get("user_rank[gt]", None):
                if isinstance(filter_data.get("user_rank[gt]"), list):
                    filter_data["user_rank[gt]"] = filter_data["user_rank[gt]"][0]
                query = query.filter_by(user_rank > int(filter_data["user_rank[gt]"]))
        except ValueError:
            raise general.InvalidParameterType("Integer has to be provided for integer fields")
        return query

    def GetAll(self, filter_data={}, target_id=None):
        Session = self.Core.DB.Target.GetOutputDBSession(target_id)
        session = Session()
        query = self.GenerateQueryUsingSession(session, filter_data)
        results = query.all()
        session.close()
        return(self.DeriveOutputDicts(results))

    def DeleteAll(self, filter_data, target_id=None): # Here keeping filter_data optional is very risky
        Session = self.Core.DB.Target.GetOutputDBSession(target_id)
        session = Session()
        query = self.GenerateQueryUsingSession(session, filter_data) # Empty dict will match all results
        results = query.delete()
        session.commit()
        session.close()

    def Update(self, plugin_group, plugin_type, plugin_code, patch_data, target_id=None):
        Session = self.Core.DB.Target.GetOutputDBSession(target_id)
        session = Session()
        query = self.GenerateQueryUsingSession(session, {"plugin_group":plugin_group, "plugin_type":plugin_type, "plugin_code":plugin_code})
        obj = query.first()
        if obj:
            try:
                if patch_data.get("user_rank", None):
                    obj.user_rank = int(patch_data["user_rank"])
                session.merge(obj)
                session.commit()
            except ValueError:
                raise general.InvalidParameterType("Integer has to be provided for integer fields")
        session.close()

    def PluginAlreadyRun(self, PluginInfo, Target = None):
        Session = self.Core.DB.Target.GetOutputDBSession(Target)
        session = Session()
        plugin_output = session.query(models.PluginOutput).get(PluginInfo["key"])
        if plugin_output:
            return(self.GetDictFromObj(plugin_output))
        return(plugin_output) # This is nothin but a "None" returned

    def SavePluginOutput(self, Plugin, Output, Duration, Target = None):
        Session = self.Core.DB.Target.GetOutputDBSession(Target)
        session = Session()
        session.merge(models.PluginOutput(  key = Plugin["key"],
                                            plugin_code = Plugin["code"],
                                            plugin_group = Plugin["group"],
                                            plugin_type = Plugin["type"],
                                            output = json.dumps(Output),
                                            start_time = Plugin["start"],
                                            execution_time = Duration,
                                            status = Plugin["status"]
                                         ))
        session.commit()
        session.close()

    def SavePartialPluginOutput(self, Plugin, Output, Message, Duration, Target = None):
        Session = self.Core.DB.Target.GetOutputDBSession(Target)
        session = Session()
        session.merge(models.PluginOutput(  key = Plugin["key"],
                                            plugin_code = Plugin["code"],
                                            plugin_group = Plugin["group"],
                                            plugin_type = Plugin["type"],
                                            output = json.dumps(Output),
                                            error = Message,
                                            start_time = Plugin["start"],
                                            execution_time = Duration,
                                            status = Plugin["status"]
                                        ))
        session.commit()
        session.close()
