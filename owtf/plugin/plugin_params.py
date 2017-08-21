"""
owtf.plugin.plugin_params.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

from owtf.dependency_management.dependency_resolver import BaseComponent
from owtf.lib.general import *


class PluginParams(BaseComponent):

    COMPONENT_NAME = "plugin_params"

    def __init__(self, Options):
        self.register_in_service_locator()
        self.config = self.get_component("config")
        self.error_handler = self.get_component("error_handler")
        self.RawArgs = Options['Args']
        self.Init = False
        self.NoArgs = []

    def ProcessArgs(self):
        self.Args = defaultdict(list)
        for Arg in self.RawArgs:
            Chunks = Arg.split('=')
            if len(Chunks) < 2:
                self.error_handler.add("USER ERROR: %s arguments should be in NAME=VALUE format" % str(Chunks), 'user')
                return False
            ArgName = Chunks[0]
            try:
                ArgValue = Arg.replace(ArgName, '')[1:]
            except ValueError:
                self.error_handler.add("USER ERROR: %s arguments should be in NAME=VALUE format" % str(ArgName), 'user')
                return False
            self.Args[ArgName] = ArgValue
        return True

    def ListArgs(self, Args, Mandatory=True):
        cprint("")  # Newline
        if Mandatory:
            cprint("Mandatory parameters:")
        else:
            cprint("Optional parameters:")
        for ArgName, ArgDescrip in list(Args.items()):
            if ArgDescrip is None:
                ArgDescrip = ""
            cprint("- %s%s%s" % (ArgName, (30 - len(ArgName)) * '_', ArgDescrip.replace('\n', "\n")))

    def GetArgsExample(self, FullArgList, Plugin):
        ArgsStr = []
        for Key, Value in list(merge_dicts(FullArgList['Mandatory'], FullArgList['Optional']).items()):
            ArgsStr.append(Key)
        Pad = '=? '
        return Pad.join(ArgsStr) + Pad

    def ShowParamInfo(self, FullArgList, Plugin):
        cprint("\nInformation for %s" % self.ShowPlugin(Plugin))
        cprint("\nDescription: %s" % str(FullArgList['Description']))
        self.ListArgs(FullArgList['Mandatory'], True)
        if len(FullArgList['Optional']) > 0:
            self.ListArgs(FullArgList['Optional'], False)
        cprint("\nUsage: %s\n" % self.GetArgsExample(FullArgList, Plugin))
        self.error_handler.abort_framework("User is only viewing options, exiting", False)

    def ShowPlugin(self, Plugin):
        return "Plugin: %s/%s" % (Plugin['type'], Plugin['file'])

    def DefaultArgFromConfig(self, Args, ArgName, SettingList):
        DefaultOrderStr = " (Default order is: %s)" % str(SettingList)
        for Setting in SettingList:
            if self.config.is_set(Setting):  # Argument is set in config
                Args[ArgName] = self.config.get_val(Setting)
                cprint("Defaulted not passed '%s' to '%s'%s" % (ArgName, str(Args[ArgName]), DefaultOrderStr))
                return True
        cprint("Could not default not passed: '%s'%s" % (ArgName, DefaultOrderStr))
        return False

    def GetArgList(self, ArgList, Plugin, Mandatory=True):
        if not self.Init:
            self.Init = True
            if not self.ProcessArgs():  # Process Passed arguments the first time only
                return self.RetArgError({}, Plugin)  # Abort processing (invalid data)
        Args = {}
        for ArgName in ArgList:
            if ArgName not in self.Args:
                ConfigDefaultOrder = ["%s_%s_%s" % (Plugin['code'], Plugin['type'], ArgName),
                                      '%s_%s' % (Plugin['code'], ArgName), ArgName]
                Defaulted = self.DefaultArgFromConfig(Args, ArgName, ConfigDefaultOrder)
                if Defaulted or Mandatory is False:
                    # The Parameter has been defaulted, must skip loop to avoid assignment at the bottom or
                    # Argument is optional = ok to skip
                    continue
                self.error_handler.add("USER ERROR: %s requires argument: '%s'" % (self.ShowPlugin(Plugin), ArgName),
                                       'user')
                return self.RetArgError({}, Plugin)  # Abort processing (invalid data)
            Args[ArgName] = self.Args[ArgName]
        return Args

    def GetArgError(self, Plugin):
        return Plugin['ArgError']

    def SetArgError(self, Plugin, Error=True):
        Plugin['ArgError'] = Error

    def RetArgError(self, ReturnValue, Plugin):
        self.SetArgError(Plugin, True)
        return ReturnValue

    def CheckArgList(self, FullArgList, Plugin):
        if ('Mandatory' not in FullArgList) or ('Optional' not in FullArgList):
            self.error_handler.add("OWTF PLUGIN BUG: %s requires declared Mandatory and Optional arguments" %
                                   self.ShowPlugin(Plugin))
            return self.RetArgError(True, Plugin)
        if 'Description' not in FullArgList:
            self.error_handler.add("OWTF PLUGIN BUG: %s  requires a Description" % self.ShowPlugin(Plugin))
            return self.RetArgError(False, Plugin)
        return True

    def SetArgsBasic(self, AllArgs, Plugin):
        if not AllArgs:
            return self.NoArgs
        ArgsStr = []
        for ArgName, ArgValue in list(AllArgs.items()):
            ArgsStr.append(ArgName + "=" + str(self.Args[ArgName]))
            AllArgs[ArgName] = ArgValue
        Plugin['Args'] = ' '.join(ArgsStr)  # Record arguments in Plugin dictionary
        return [AllArgs]

    def SetConfig(self, Args):
        for ArgName, ArgValue in list(Args.items()):
            cprint("Overriding configuration setting '_%s' with value %s.." % (ArgName, str(ArgValue)))
            self.config.set_general_val('string', '%s_' % ArgName, ArgValue)  # Pre-pend "_" to avoid naming collisions

    def GetPermutations(self, Args):
        Permutations = defaultdict(list)
        if 'REPEAT_DELIM' not in Args:
            return Permutations  # No permutations
        Separator = Args['REPEAT_DELIM']
        for ArgName, ArgValue in list(Args.items()):
            if ArgName == 'REPEAT_DELIM':
                continue  # The repeat delimiter is not considered a permutation: It's the permutation delimiter :)
            Chunks = ArgValue.split(Separator)
            if len(Chunks) > 1:
                Permutations[ArgName] = Chunks
        return Permutations

    def SetPermutation(self, ArgName, Permutations, PermutationList):
        for i in range(0, len(PermutationList)):
            Count = 0
            for Perm in Permutations:
                PermArgs = PermutationList[i].copy()  # 1st copy by value original arguments
                PermArgs[ArgName] = Perm  # 2nd override argument with permutation
                if Count == 0:  # Modify 1st existing record with permutation
                    PermutationList[i] = PermArgs
                else:
                    PermutationList.append(PermArgs)  # 3rd store each subsequent permutation as a different set of args
                Count += 1

    def SetArgs(self, AllArgs, Plugin):
        ArgList = self.SetArgsBasic(AllArgs, Plugin)
        if not ArgList:
            return ArgList  # Nothing to do
        Args = ArgList[0]
        PermutationList = [Args]
        for ArgName, Permutations in list(self.GetPermutations(Args).items()):
            self.SetPermutation(ArgName, Permutations, PermutationList)
        if not PermutationList:
            return ArgList  # No permutations, return original arguments
        return PermutationList

    def GetArgs(self, FullArgList, Plugin):
        self.SetArgError(Plugin, False)
        if not self.CheckArgList(FullArgList, Plugin):
            return self.NoArgs
        if 'O' in self.RawArgs:  # To view available options
            self.ShowParamInfo(FullArgList, Plugin)
            return self.NoArgs  # Abort processing, just showing options
        Mandatory = self.GetArgList(FullArgList['Mandatory'], Plugin, True)
        Optional = self.GetArgList(FullArgList['Optional'], Plugin, False)
        if self.GetArgError(Plugin):
            cprint("")
            cprint("ERROR: Aborting argument processing, please correct the errors above and try again")
            cprint("")
            return self.NoArgs  # Error processing arguments, must abort processing
        AllArgs = merge_dicts(Mandatory, Optional)
        return self.SetArgs(AllArgs, Plugin)
