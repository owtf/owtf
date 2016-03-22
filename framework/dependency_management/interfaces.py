from abc import ABCMeta, abstractmethod, abstractproperty


class AbstractInterface():
    #__metaclass__ = ABCMeta
    pass # TODO Recalculate the currently used methods and update the abstract interfaces


class CommandRegisterInterface(AbstractInterface):

    @abstractmethod
    def AddCommand(self): pass

    @abstractmethod
    def CommandAlreadyRegistered(self): pass


class DBInterface(AbstractInterface):

    @abstractmethod
    def CreateScopedSession(self): pass

    # @abstractmethod
    # def CreateSession(self): pass
    #
    # @abstractmethod
    # def EnsureDBWithBase(self): pass
    #
    # @abstractmethod
    # def SaveDBs(self): pass

    @abstractmethod
    def get_category(self): pass


class DBConfigInterface(AbstractInterface):

    @abstractmethod
    def Get(self): pass

    @abstractmethod
    def GetAll(self): pass

    @abstractmethod
    def GetReplacementDict(self): pass

    @abstractmethod
    def Update(self): pass


class DBErrorInterface(AbstractInterface):

    @abstractmethod
    def Add(self): pass


class DBPluginInterface(AbstractInterface):

    @abstractmethod
    def GetAll(self): pass

    @abstractmethod
    def GetAllTestGroups(self): pass

    @abstractmethod
    def GetPluginsByGroup(self): pass

    @abstractmethod
    def GetPluginsByGroupType(self): pass

    @abstractmethod
    def GetTypesForGroup(self): pass


class ErrorHandlerInterface(AbstractInterface):

    @abstractmethod
    def Add(self): pass

    @abstractmethod
    def AddGithubIssue(self): pass

    @abstractmethod
    def FrameworkAbort(self): pass

    @abstractmethod
    def SetCommand(self): pass

    @abstractmethod
    def UserAbort(self): pass


class MappingDBInterface(AbstractInterface):

    @abstractmethod
    def GetMappingTypes(self): pass

    @abstractmethod
    def GetMappings(self): pass


class PluginHandlerInterface(AbstractInterface):

    @abstractmethod
    def DumpOutputFile(self): pass

    @abstractmethod
    def GetPluginGroupDir(self): pass

    @abstractmethod
    def GetPluginOutputDir(self): pass

    @abstractmethod
    def NormalRequestsAllowed(self): pass

    @abstractmethod
    def ProcessPlugin(self): pass

    @abstractmethod
    def RequestsPossible(self): pass

    @abstractmethod
    def RetrieveAbsPath(self): pass

    @abstractmethod
    def SwitchToTarget(self): pass

    @abstractmethod
    def ValidateAndFormatPluginList(self): pass


class PluginOutputInterface(AbstractInterface):

    @abstractmethod
    def DeleteAll(self): pass

    @abstractmethod
    def GetAll(self): pass

    @abstractmethod
    def GetUnique(self): pass

    @abstractmethod
    def PluginAlreadyRun(self): pass

    @abstractmethod
    def SavePartialPluginOutput(self): pass

    @abstractmethod
    def SavePluginOutput(self): pass

    @abstractmethod
    def Update(self): pass


class RequesterInterface(AbstractInterface):

    @abstractmethod
    def GetTransaction(self): pass

    @abstractmethod
    def GetTransactions(self): pass

    @abstractmethod
    def Request(self): pass

    @abstractmethod
    def SetHeaders(self): pass


class ResourceInterface(AbstractInterface):

    @abstractmethod
    def GetResourceList(self): pass

    @abstractmethod
    def GetResources(self): pass


class ShellInterface(AbstractInterface):

    @abstractmethod
    def GetModifiedShellCommand(self): pass

    @abstractmethod
    def RefreshReplacements(self): pass

    @abstractmethod
    def shell_exec(self): pass

    @abstractmethod
    def shell_exec_monitor(self): pass


class TimerInterface(AbstractInterface):

    @abstractmethod
    def GetElapsedTimeAsStr(self): pass

    @abstractmethod
    def GetEndDateTimeAsStr(self): pass

    @abstractmethod
    def GetStartDateTimeAsStr(self): pass

    @abstractmethod
    def StartTimer(self): pass


class TransactionInterface(AbstractInterface):

    @abstractmethod
    def DeleteTransaction(self): pass

    @abstractmethod
    def GetAllAsDicts(self): pass

    @abstractmethod
    def GetByIDAsDict(self): pass

    @abstractmethod
    def GetByIDs(self): pass

    @abstractmethod
    def GetFirst(self): pass

    @abstractmethod
    def GetSessionData(self): pass

    @abstractmethod
    def GetTopTransactionsBySpeed(self): pass

    @abstractmethod
    def IsTransactionAlreadyAdded(self): pass

    @abstractmethod
    def LogTransaction(self): pass

    @abstractmethod
    def LogTransactionsFromLogger(self): pass

    @abstractmethod
    def NumTransactions(self): pass

    @abstractmethod
    def SearchAll(self): pass

    @abstractmethod
    def SearchByRegexName(self): pass


class URLManagerInterface(AbstractInterface):

    @abstractmethod
    def AddURL(self): pass

    @abstractmethod
    def AddURLsEnd(self): pass

    @abstractmethod
    def AddURLsStart(self): pass

    @abstractmethod
    def GetAll(self): pass

    @abstractmethod
    def GetURLsToVisit(self): pass

    @abstractmethod
    def ImportProcessedURLs(self): pass

    @abstractmethod
    def ImportURLs(self): pass

    @abstractmethod
    def IsURL(self): pass

    @abstractmethod
    def SearchAll(self): pass


class WorkerManagerInterface(AbstractInterface):

    @abstractmethod
    def create_worker(self): pass

    @abstractmethod
    def delete_worker(self): pass

    @abstractmethod
    def fill_work_list(self): pass

    @abstractmethod
    def filter_work_list(self): pass

    @abstractmethod
    def get_work_list(self): pass

    @abstractmethod
    def get_worker_details(self): pass

    @abstractmethod
    def manage_workers(self): pass


class ZapAPIInterface(AbstractInterface):

    @abstractmethod
    def ForwardRequest(self): pass


class ZestInterface(AbstractInterface):

    @abstractmethod
    def GetAllScripts(self): pass

    @abstractmethod
    def GetRecordScriptContent(self): pass

    @abstractmethod
    def GetTargetConfig(self): pass

    @abstractmethod
    def GetTargetScriptContent(self): pass

    @abstractmethod
    def IsRecording(self): pass

    @abstractmethod
    def RunRecordScript(self): pass

    @abstractmethod
    def RunTargetScript(self): pass

    @abstractmethod
    def StartRecorder(self): pass

    @abstractmethod
    def StopRecorder(self): pass

    @abstractmethod
    def TargetScriptFromMultipleTransactions(self): pass

    @abstractmethod
    def TargetScriptFromSingleTransaction(self): pass

    @abstractmethod
    def addtoRecordedTrans(self): pass


class TargetInterface(AbstractInterface):

    @abstractmethod
    def AddTarget(self): pass

    @abstractmethod
    def DeleteTarget(self): pass

    @abstractmethod
    def Get(self): pass

    @abstractmethod
    def GetAll(self): pass

    @abstractmethod
    def GetAllInScope(self): pass

    @abstractmethod
    def GetIndexedTargets(self): pass

    @abstractmethod
    def GetPath(self): pass

    @abstractmethod
    def GetTargetConfig(self): pass

    @abstractmethod
    def GetTargetConfigForID(self): pass

    @abstractmethod
    def GetTargetConfigs(self): pass

    @abstractmethod
    def GetTargetID(self): pass

    @abstractmethod
    def GetTargetURL(self): pass

    @abstractmethod
    def IsInScopeURL(self): pass

    @abstractmethod
    def PathConfig(self): pass

    @abstractmethod
    def SetPath(self): pass

    @abstractmethod
    def SetTarget(self): pass

    @abstractmethod
    def UpdateTarget(self): pass


class ConfigInterface(AbstractInterface):

    @abstractmethod
    def CleanUpForTarget(self): pass

    @abstractmethod
    def ConvertStrToBool(self): pass

    @abstractmethod
    def CreateOutputDirForTarget(self): pass

    @abstractmethod
    def DeriveConfigFromURL(self): pass

    @abstractmethod
    def FrameworkConfigGet(self): pass

    @abstractmethod
    def FrameworkConfigGetDBPath(self): pass

    @abstractmethod
    def FrameworkConfigGetLogPath(self): pass

    @abstractmethod
    def FrameworkConfigGetLogsDir(self): pass

    @abstractmethod
    def GetAsList(self): pass

    @abstractmethod
    def GetFrameworkConfigDict(self): pass

    @abstractmethod
    def GetHeaderList(self): pass

    @abstractmethod
    def GetOutputDBPathForTarget(self): pass

    @abstractmethod
    def GetOutputDirForTarget(self): pass

    @abstractmethod
    def GetOutputDirForTargets(self): pass

    @abstractmethod
    def GetReplacementDict(self): pass

    @abstractmethod
    def GetResources(self): pass

    @abstractmethod
    def GetTransactionDBPathForTarget(self): pass

    @abstractmethod
    def GetUrlDBPathForTarget(self): pass

    @abstractmethod
    def IsSet(self): pass

    @abstractmethod
    def MultipleReplace(self): pass

    @abstractproperty
    def OwtfPid(self): pass

    @abstractmethod
    def ProcessOptions(self): pass

    @abstractproperty
    def Profiles(self): pass

    @abstractproperty
    def RootDir(self): pass

    @abstractmethod
    def Set(self): pass


class ReporterInterface(AbstractInterface):

    @abstractmethod
    def reset_loader(self): pass

    @abstractmethod
    def sanitize_html(self): pass
