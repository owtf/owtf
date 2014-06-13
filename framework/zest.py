import subprocess
import os
import os.path
from os import listdir
from os.path import isfile, join


class Zest(object):
#basic initialization of Root,Output,Zest Directories from target config

    def __init__(self, core):
            self.Core = core
            self.recordedTransactions = []
            self.StopRecorder()

# Script creation from single transaction, as of now name 'zest_trans_transaction-id'
# is implicitly used to keep it more automated, can be changed if required
    def TargetScriptFromSingleTransaction(self, Transaction_id, Target_id):
            target_config = self.GetTargetConfig(Target_id)
            Script_name = "zest_trans_" + Transaction_id
            return self.GenerateZest(Script_name, str(Target_id), Transaction_id, target_config)

#script creation from multiple requests
    def TargetScriptFromMultipleTransactions(self, Target_id, Script_name, transactions):
            target_config = self.GetTargetConfig(Target_id)
            zest_args = self.ConvertToZestArgs(transactions)
            return self.GenerateZest(Script_name, str(Target_id), zest_args, target_config)

#script generation if file not already present
    def GenerateZest(self, Script, tar_arg, trans_arg, config):
            op_script = self.GetOutputFile(Script, config['Zest_Dir'])
            if not self.CheckifExists(op_script):
                subprocess.call(['sh', config['Script_Path'], config['Root_Dir'],
                                        config['Output_Dir'], config['target_db'], op_script, tar_arg, trans_arg])
                return True
            else:
                return False

    def GetTargetConfig(self, target_id):
            target_config = {}
            self.Core.DB.Target.SetTarget(target_id)
            target_config['Output_Dir'] = self.Core.DB.Target.PathConfig['URL_OUTPUT']
            target_config['Root_Dir'] = self.Core.Config.RootDir
            target_config['Output_Dir'] = target_config['Root_Dir'] + "/" + target_config['Output_Dir']
            target_config['target_db'] = self.Core.Config.FrameworkConfigGet('TCONFIG_DB_PATH')
            target_config['Script_Path'] = target_config['Root_Dir'] + "/zest/zest.sh"
            target_config['Zest_Dir'] = target_config['Output_Dir'] + "/zest"
            self.Core.CreateMissingDirs(target_config['Zest_Dir'])
            return target_config

    def CheckifExists(self, File_name):
            return True if (os.path.isfile(File_name)) else False

    def GetOutputFile(self, script, Zest_Dir):
            return Zest_Dir + "/" + script + ".zst"

    def GetAllTargetScripts(self, target_id):
        zestfiles = []
        target_config = self.GetTargetConfig(target_id)
        if os.path.exists(target_config['Zest_Dir']):
            zestfiles = [f for f in listdir(target_config['Zest_Dir']) if isfile(join(target_config['Zest_Dir'], f))]
        else:
            os.makedirs(target_config['Zest_Dir'])
        return zestfiles

    def GetAllScripts(self, target_id):
        zestfiles = self.GetAllTargetScripts(target_id)
        record_scripts = self.GetAllRecordScripts()
        return zestfiles, record_scripts

    def GetAllRecordScripts(self):
        recordfiles = []
        record_config = self.GetRecordConfig()
        if os.path.exists(record_config['Zest_Dir']):
            recordfiles = [f for f in listdir(record_config['Zest_Dir']) if isfile(join(record_config['Zest_Dir'], f))]
        else:
            os.makedirs(record_config['Zest_Dir'])
        return recordfiles

    def GetScriptContent(self, script):
        content = ""
        if os.path.isfile(script):
            with open(script, 'r') as content_file:
                content = content_file.read()
        return content

    def GetTargetScriptContent(self, target_id, scr):
        target_config = self.GetTargetConfig(target_id)
        result_script = target_config['Zest_Dir'] + "/" + scr
        return self.GetScriptContent(result_script)

    def GetRecordScriptContent(self, scr):
        record_config = self.GetRecordConfig()
        result_script = record_config['Zest_Dir'] + "/" + scr
        return self.GetScriptContent(result_script)

    def addtoRecordedTrans(self, trans_list):
        self.recordedTransactions.extend(trans_list)
        self.CreateRecordScript()

    def CreateRecordScript(self):
        target_list, transaction_list = self.GetArgumentsfromRecordedTransactions()
        target_arg = self.ConvertToZestArgs(target_list)
        trans_arg = self.ConvertToZestArgs(transaction_list)
        record_config = self.GetRecordConfig()
        self.GenerateZest("Defualt", target_arg, trans_arg, record_config)

    def GetRecordConfig(self):
        record_config = {}
        record_config['Root_Dir'] = self.Core.Config.RootDir
        record_config['Output_Dir'] = record_config['Root_Dir'] + "/" + self.Core.Config.GetOutputDirForTargets()
        record_config['target_db'] = record_config['Root_Dir'] + "/" + self.Core.Config.FrameworkConfigGetDBPath('TCONFIG_DB_PATH')
        record_config['Script_Path'] = record_config['Root_Dir'] + "/zest/zest.sh"
        record_config['Zest_Dir'] = record_config['Output_Dir'] + "/recorded_scripts"
        self.Core.CreateMissingDirs(record_config['Zest_Dir'])
        return record_config

    def GetArgumentsfromRecordedTransactions(self):
        return map(list, zip(*self.recordedTransactions))

    def StartRecorder(self):
        self.Core.DB.Config.Update("ZEST_RECORDING", "True")

    def StopRecorder(self):
        self.Core.DB.Config.Update("ZEST_RECORDING", "False")

    def IsRecording(self):
        return self.Core.DB.Config.Get("ZEST_RECORDING")

    def ConvertToZestArgs(self, arguments):
        zest_args = ""
        for trans_id in arguments:  # creating argument string
            zest_args = zest_args + " " + str(trans_id)
        zest_args = zest_args[1:]
        return zest_args
