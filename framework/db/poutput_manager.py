from framework.db import models
import json

class POutputDB(object):
    def __init__(self, Core):
        self.Core = Core

    def GetDictFromObj(self, obj):
        return({
                "Key" : obj.key,
                "Code" : obj.code,
                "Type" : obj.plugin_type,
                "Output" : json.loads(obj.ouput),
                "Success" : obj.status,
                "UserNotes" : obj.user_notes,
                "UserRank" : obj.user_rank,
                "OwtfRank" : obj.owtf_rank
                })

    def GetDictsFromObjs(self, obj_list):
        dict_list = []
        for obj in obj_list:
            dict_list.append(self.GetDictFromObj(obj))
        return(dict_list)

    def PluginAlreadyRun(self, PluginInfo, Target = None):
        Session = self.Core.DB.Target.GetOutputDBSession(Target)
        session = Session()
        plugin_output = session.query(models.PluginOutput).get(PluginInfo["Key"])
        if plugin_output:
            return(self.GetDictFromObj(plugin_output))
        return(plugin_output)

    def SavePluginOutput(self, Plugin, Output, StartTime, Duration, Target = None):
        Session = self.Core.DB.Target.GetOutputDBSession(Target)
        session = Session()
        session.merge(models.PluginOutput(  key = Plugin["Key"],
                                            code = Plugin["Code"],
                                            plugin_type = Plugin["Type"],
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
        session.merge(models.PluginOutput(  key = Plugin["Key"],
                                            code = Plugin["Code"],
                                            plugin_type = Plugin["Type"],
                                            error = Message,
                                            start_time = StartTime,
                                            execution_time = Duration,
                                            success = False
                                        ))
        session.commit()
        session.close()

    def AddCommandToRegistry(self, Command, Target = None):
        Session = self.Core.DB.Target.GetOutputDBSession(Target)
        session = Session()
        session.merge(models.Command(
                                        start = Command['Start'],
                                        end = Command['End'],
                                        run_time = Command['RunTime'],
                                        success = Command['Success'],
                                        target = Command['Target'],
                                        modified_command = Command['ModifiedCommand'].strip(),
                                        original_command = Command['OriginalCommand'].strip()
                                    ))
        session.commit()
        session.close()

    def CommandAlreadyRegistered(self, original_command, Target = None):
        Session = self.Core.DB.Target.GetOutputDBSession(Target)
        session = Session()
        register_entry = session.query(models.Command).get(original_command)
        if register_entry and register_entry.success:
            return True
        return False
