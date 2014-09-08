import subprocess
import os.path
from os import listdir
from os.path import isfile, join


class Zest(object):
#basic initialization of Root,Output,Zest Directories from target config

    def __init__(self, core):
        self.Core = core
        self.recordedTransactions = []  # keeps track of recorded transactions
        self.StopRecorder()  # recorded should be stopped when OWTF starts

# Script creation from single transaction
    def TargetScriptFromSingleTransaction(self, transaction_id, script_name, target_id):
        target_config = self.GetTargetConfig(target_id)
        return self.GenerateZest(script_name, str(target_id), transaction_id, target_config, "False")

#script creation from multiple requests
    def TargetScriptFromMultipleTransactions(self, Target_id, Script_name, transactions):
        target_config = self.GetTargetConfig(Target_id)
        zest_args = self.ConvertToZestArgs(transactions)
        return self.GenerateZest(Script_name, str(Target_id), zest_args, target_config, "False")

#script generation if file not already present
    def GenerateZest(self, Script, tar_arg, trans_arg, config, record):
        op_script = self.GetOutputFile(Script, config['ZEST_DIR'])
        if not self.CheckifExists(op_script) or record == "True": # create a script only if its a record script or new target script
            subprocess.call(['sh', config['CREATE_SCRIPT_PATH'], config['ROOT_DIR'],
                                     config['OUTPUT_DIR'], config['TARGET_DB'], op_script, tar_arg, trans_arg, record])
            return True
        else:
            return False

    def CreateRecordScript(self):
        target_list, transaction_list = self.GetArgumentsfromRecordedTransactions()
        target_arg = self.ConvertToZestArgs(target_list)
        trans_arg = self.ConvertToZestArgs(transaction_list)
        record_config = self.GetRecordConfig()
        self.GenerateZest(self.GetRecordScript(), target_arg, trans_arg, record_config, "True")

    def GetTargetConfig(self, target_id):
        target_config = {}
        self.Core.DB.Target.SetTarget(target_id)
        target_config['ROOT_DIR'] = self.Core.Config.RootDir
        target_config['OUTPUT_DIR'] = os.path.join(target_config['ROOT_DIR'], self.Core.DB.Target.PathConfig['url_output'])
        target_config['TARGET_DB'] = self.Core.Config.FrameworkConfigGet('TCONFIG_DB_PATH')
        target_config['ZEST_DIR'] = os.path.join(target_config['OUTPUT_DIR'], "zest")
        target_config['CREATE_SCRIPT_PATH'] = os.path.join(target_config['ROOT_DIR'], "zest", "zest_create.sh")
        target_config['RUNNER_SCRIPT_PATH'] = os.path.join(target_config['ROOT_DIR'], "zest","zest_runner.sh")
        target_config['HOST_AND_PORT'] = ((self.Core.DB.Target.GetTargetConfigForID(target_id))['host_name'] 
                                              + ":" + (self.Core.DB.Target.GetTargetConfigForID(target_id))['PORT_NUMBER'])
        self.Core.CreateMissingDirs(target_config['ZEST_DIR'])
        return target_config

    def GetRecordConfig(self):
        record_config = {}
        record_config['ROOT_DIR'] = self.Core.Config.RootDir
        record_config['OUTPUT_DIR'] = os.path.join(record_config['ROOT_DIR'], self.Core.Config.GetOutputDirForTargets())
        record_config['TARGET_DB'] = os.path.join(record_config['ROOT_DIR'], self.Core.Config.FrameworkConfigGetDBPath('TCONFIG_DB_PATH'))
        record_config['CREATE_SCRIPT_PATH'] = os.path.join(record_config['ROOT_DIR'], "zest", "zest_create.sh")
        record_config['RUNNER_SCRIPT_PATH'] = os.path.join(record_config['ROOT_DIR'], "zest", "zest_runner.sh")
        record_config['ZEST_DIR'] = os.path.join(record_config['ROOT_DIR'], self.Core.Config.FrameworkConfigGet("OUTPUT_PATH"), "misc", "recorded_scripts")
        self.Core.CreateMissingDirs(record_config['ZEST_DIR'])
        return record_config

    def CheckifExists(self, file_name):
        return True if (os.path.isfile(file_name)) else False

    def GetOutputFile(self, script, ZEST_DIR):
        return os.path.join(ZEST_DIR, script + ".zst")

    def GetAllTargetScripts(self, target_id):
        zestfiles = []
        target_config = self.GetTargetConfig(target_id)
        if os.path.exists(target_config['ZEST_DIR']):
            zestfiles = [f for f in listdir(target_config['ZEST_DIR']) if isfile(join(target_config['ZEST_DIR'], f))]
        else:
            os.makedirs(target_config['ZEST_DIR'])
        return zestfiles

    def GetAllScripts(self, target_id):
        zestfiles = self.GetAllTargetScripts(target_id)
        record_scripts = self.GetAllRecordScripts()
        return zestfiles, record_scripts

    def GetAllRecordScripts(self):
        recordfiles = []
        record_config = self.GetRecordConfig()
        if os.path.exists(record_config['ZEST_DIR']):
            recordfiles = [f for f in listdir(record_config['ZEST_DIR']) if isfile(join(record_config['ZEST_DIR'], f))]
        else:
            os.makedirs(record_config['ZEST_DIR'])
        return recordfiles

    def GetScriptContent(self, script):
        content = ""
        if os.path.isfile(script):
            with open(script, 'r') as content_file:
                content = content_file.read()
        return content

    def GetTargetScriptContent(self, target_id, scr):
        target_config = self.GetTargetConfig(target_id)
        result_script = os.path.join(target_config['ZEST_DIR'], scr)
        return self.GetScriptContent(result_script)

    def GetRecordScriptContent(self, scr):
        record_config = self.GetRecordConfig()
        result_script = os.path.join(record_config['ZEST_DIR'], scr)
        return self.GetScriptContent(result_script)

    def addtoRecordedTrans(self, trans_list):
        self.recordedTransactions.extend(trans_list)
        self.CreateRecordScript()

    def GetArgumentsfromRecordedTransactions(self):  # splits the list of tuples into two distinct lists
        return map(list, zip(*self.recordedTransactions))

    def StartRecorder(self, file_name):
        record_config = self.GetRecordConfig()
        zest_file = self.GetOutputFile(file_name, record_config['ZEST_DIR'])
        if not self.CheckifExists(zest_file):
            self.Core.DB.Config.Update("ZEST_RECORDING", "True")
            self.UpadateRecordScript(file_name)
            return True
        else:
            return False

    def StopRecorder(self):
        self.Core.DB.Config.Update("ZEST_RECORDING", "False")

    def UpadateRecordScript(self, record_script):  # saves name of record script in config db as web UI runs on different process and cant read value from here.
        self.Core.DB.Config.Update("RECORD_SCRIPT", record_script)

    def GetRecordScript(self):
        return self.Core.DB.Config.Get("RECORD_SCRIPT")

    def IsRecording(self):
        return True if (self.Core.DB.Config.Get("ZEST_RECORDING") == "True") else False

    def ConvertToZestArgs(self, arguments):  # converts to string
        zest_args = ""
        for trans_id in arguments:  # creating argument string
            zest_args = zest_args + " " + str(trans_id)
        zest_args = zest_args[1:]
        return zest_args

    def RunRecordScript(self, script):
        record_config = self.GetRecordConfig()
        return self.RunZestScript(os.path.join(record_config['ZEST_DIR'], script), record_config)

    def RunZestScript(self, script, config):
        output = subprocess.check_output(['bash', config['RUNNER_SCRIPT_PATH'], "-script", script], stderr=subprocess.STDOUT)
        return output

    def RunTargetScript(self, target_id, script):
        target_config = self.GetTargetConfig(target_id)
        return self.RunZestScript(os.path.join(target_config['ZEST_DIR'], script), target_config)
