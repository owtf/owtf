import subprocess
import os
import os.path
from os import listdir
from os.path import isfile, join


class Zest(object):
#basic initialization of Root,Output,Zest Directories from target config

    def __init__(self, core):
            self.Core = core
            self.recordedTransactions = []  # keeps track of recorded transactions
            self.StopRecorder()  # recorded should be stopped when OWTF starts
            self.activerecordscript = "Default"

# Script creation from single transaction, as of now name 'zest_trans_transaction-id'
# is implicitly used to keep it more automated, can be changed if required
    def TargetScriptFromSingleTransaction(self, Transaction_id,Script_name, Target_id):
            target_config = self.GetTargetConfig(Target_id)
            return self.GenerateZest(Script_name, str(Target_id), Transaction_id, target_config, False)

#script creation from multiple requests
    def TargetScriptFromMultipleTransactions(self, Target_id, Script_name, transactions):
            target_config = self.GetTargetConfig(Target_id)
            zest_args = self.ConvertToZestArgs(transactions)
            return self.GenerateZest(Script_name, str(Target_id), zest_args, target_config, False)

#script generation if file not already present
    def GenerateZest(self, Script, tar_arg, trans_arg, config, record):
            op_script = self.GetOutputFile(Script, config['Zest_Dir'])
            if not self.CheckifExists(op_script) or record is True:
                subprocess.call(['sh', config['Create_Script_Path'], config['Root_Dir'],
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
            target_config['Zest_Dir'] = target_config['Output_Dir'] + "/zest"
            target_config['Create_Script_Path'] = target_config['Root_Dir'] + "/zest/zest_create.sh"
            target_config['Runner_Script_Path'] = target_config['Root_Dir'] + "/zest/zest_runner.sh"
            target_config['Host_and_Port'] = ((self.Core.DB.Target.GetTargetConfigForID(target_id))['HOST_NAME'] 
                                              + ":" + (self.Core.DB.Target.GetTargetConfigForID(target_id))['PORT_NUMBER'])
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
        self.GenerateZest(self.activerecordscript, target_arg, trans_arg, record_config, True)

    def GetRecordConfig(self):
        record_config = {}
        record_config['Root_Dir'] = self.Core.Config.RootDir
        record_config['Output_Dir'] = record_config['Root_Dir'] + "/" + self.Core.Config.GetOutputDirForTargets()
        record_config['target_db'] = record_config['Root_Dir'] + "/" + self.Core.Config.FrameworkConfigGetDBPath('TCONFIG_DB_PATH')
        record_config['Create_Script_Path'] = record_config['Root_Dir'] + "/zest/zest_create.sh"
        record_config['Runner_Script_Path'] = record_config['Root_Dir'] + "/zest/zest_runner.sh"
        record_config['Zest_Dir'] = record_config['Output_Dir'] + "/recorded_scripts"
        self.Core.CreateMissingDirs(record_config['Zest_Dir'])
        return record_config

    def GetArgumentsfromRecordedTransactions(self):  # splits the list of tuples into two distinct lists
        return map(list, zip(*self.recordedTransactions))

    def StartRecorder(self, file_name):
        record_config = self.GetRecordConfig()
        if not self.CheckifExists(self.GetOutputFile(file_name, record_config['Zest_Dir'])):
            self.Core.DB.Config.Update("ZEST_RECORDING", "True")
            self.activerecordscript = file_name
            return True
        else:
            return False

    def StopRecorder(self):
        self.Core.DB.Config.Update("ZEST_RECORDING", "False")

    def IsRecording(self):
        return self.Core.DB.Config.Get("ZEST_RECORDING")

    def ConvertToZestArgs(self, arguments):  # converts to string
        zest_args = ""
        for trans_id in arguments:  # creating argument string
            zest_args = zest_args + " " + str(trans_id)
        zest_args = zest_args[1:]
        return zest_args

    def RunRecordScript(self, script):
        record_config = self.GetRecordConfig()
        return self.RunZestScript(os.path.join(record_config['Zest_Dir'], script), record_config)

    def RunZestScript(self, script, config):
        output = subprocess.check_output(['bash', config['Runner_Script_Path'], "-script", script], stderr=subprocess.STDOUT)
        return output

    def RunTargetScript(self, target_id, script):
        target_config = self.GetTargetConfig(target_id)
        return self.RunZestScript(os.path.join(target_config['Zest_Dir'], script), target_config)
