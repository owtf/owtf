from framework.db import models
import json

class POutputDB(object):
    def __init__(self, Core):
        self.Core = Core

    def GetDictFromObj(self, obj):
        return({
                "key" : obj.key,
                "code" : obj.code,
                "type" : obj.plugin_type,
                "output" : json.loads(obj.ouput),
                "success" : obj.status,
                "user_notes" : obj.user_notes,
                "user_rank" : obj.user_rank,
                "owtf_rank" : obj.owtf_rank
                })

    def GetDictsFromObjs(self, obj_list):
        dict_list = []
        for obj in obj_list:
            dict_list.append(self.GetDictFromObj(obj))
        return(dict_list)

    def PluginAlreadyRun(self, PluginInfo, Target = None):
        Session = self.Core.DB.Target.GetOutputDBSession(Target)
        session = Session()
        plugin_output = session.query(models.PluginOutput).get(PluginInfo["key"])
        if plugin_output:
            return(self.GetDictFromObj(plugin_output))
        return(plugin_output)

    def SavePluginOutput(self, Plugin, Output, StartTime, Duration, Target = None):
        Session = self.Core.DB.Target.GetOutputDBSession(Target)
        session = Session()
        session.merge(models.PluginOutput(  key = Plugin["key"],
                                            code = Plugin["code"],
                                            plugin_type = Plugin["type"],
                                            output = json.dumps(Output),
                                            start_time = StartTime,
                                            execution_time = Duration,
                                            success = True
                                         ))
        session.commit()
        session.close()

    def SavePartialPluginOutput(self, Plugin, Message, StartTime, Duration, Target = None):
        Session = self.Core.DB.Target.GetOutputDBSession(Target)
        session = Session()
        session.merge(models.PluginOutput(  key = Plugin["key"],
                                            code = Plugin["code"],
                                            plugin_type = Plugin["type"],
                                            error = Message,
                                            start_time = StartTime,
                                            execution_time = Duration,
                                            success = False
                                        ))
        session.commit()
        session.close()
