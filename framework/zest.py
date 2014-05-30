import subprocess
import os


class Zest(object):
#basic initialization of Root,Output,Zest Directories from target config
    def __init__(self, core, target_id):
            self.Core = core
            self.Target_id = target_id
            self.Core.DB.Target.SetTarget(self.Target_id)
            self.Output_Dir = self.Core.DB.Target.PathConfig['URL_OUTPUT']
            self.Root_Dir = self.Core.Config.RootDir
            self.Output_Dir = self.Root_Dir + "/" + self.Output_Dir
            self.Script_Path = self.Root_Dir + "/zest/zest.sh"
            self.Zest_Dir = self.Output_Dir + "/zest"
            self.Core.CreateMissingDirs(self.Zest_Dir)

# Script creation from single transaction, as of now name 'zest_trans_transaction-id'
# is implicitly used to keep it more automated, can be changed if required
    def ScriptCreateFromSingleTransaction(self, Transaction_id):
            Script_name = "zest_trans_" + Transaction_id
            return self.GenerateZest(Script_name, Transaction_id)

#script creation from multiple requests
    def ScriptCreateFromMultipleTransactions(self, Script_name, transactions):
            return self.GenerateZest(Script_name, transactions)

#script generation if file not already present
    def GenerateZest(self, Script, arguments):
            op_script = self.GetOutputFile(Script)
            if not self.CheckifExists(op_script):
                subprocess.call(['sh', self.Script_Path, self.Root_Dir,
                                        self.Output_Dir, op_script, arguments])
                return True
            else:
                return False

    def CheckifExists(self, File_name):
            return True if (os.path.isfile(File_name)) else False

    def GetOutputFile(self, script):
            return self.Zest_Dir + "/" + script + ".zst"


def Init(Core, Target_id):
        return Zest(Core, Target_id)
