"""
owtf.dependency_management.interfaces
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Implements abstract interfaces for different services to build on
"""

from abc import abstractmethod, abstractproperty


class AbstractInterface():
    pass  # TODO Recalculate the currently used methods and update the abstract interfaces


class CommandRegisterInterface(AbstractInterface):

    @abstractmethod
    def add_command(self):
        pass

    @abstractmethod
    def command_already_registered(self):
        pass


class DBInterface(AbstractInterface):

    @abstractmethod
    def CreateScopedSession(self):
        pass

    @abstractmethod
    def get_category(self):
        pass


class DBConfigInterface(AbstractInterface):

    @abstractmethod
    def get(self):
        pass

    @abstractmethod
    def get_all(self):
        pass

    @abstractmethod
    def get_replacement_dict(self):
        pass

    @abstractmethod
    def update(self):
        pass


class DBErrorInterface(AbstractInterface):

    @abstractmethod
    def add(self):
        pass


class DBPluginInterface(AbstractInterface):

    @abstractmethod
    def get_all(self):
        pass

    @abstractmethod
    def get_all_test_groups(self):
        pass

    @abstractmethod
    def get_plugins_by_group(self):
        pass

    @abstractmethod
    def get_plugins_by_group_type(self):
        pass

    @abstractmethod
    def get_types_for_plugin_group(self):
        pass


class ErrorHandlerInterface(AbstractInterface):

    @abstractmethod
    def add(self):
        pass

    @abstractmethod
    def add_github_issue(self):
        pass

    @abstractmethod
    def abort_framework(self):
        pass

    @abstractmethod
    def set_command(self):
        pass

    @abstractmethod
    def user_abort(self):
        pass


class MappingDBInterface(AbstractInterface):

    @abstractmethod
    def get_mapping_types(self):
        pass

    @abstractmethod
    def get_mappings(self):
        pass


class PluginHandlerInterface(AbstractInterface):

    @abstractmethod
    def dump_output_file(self):
        pass

    @abstractmethod
    def GetPluginGroupDir(self):
        pass

    @abstractmethod
    def get_plugin_output_dir(self):
        pass

    @abstractmethod
    def NormalRequestsAllowed(self):
        pass

    @abstractmethod
    def process_plugin(self):
        pass

    @abstractmethod
    def requests_possible(self):
        pass

    @abstractmethod
    def get_abs_path(self):
        pass

    @abstractmethod
    def SwitchToTarget(self):
        pass

    @abstractmethod
    def validate_format_plugin_list(self):
        pass


class PluginOutputInterface(AbstractInterface):

    @abstractmethod
    def delete_all(self):
        pass

    @abstractmethod
    def get_all(self):
        pass

    @abstractmethod
    def get_unique(self):
        pass

    @abstractmethod
    def plugin_already_run(self):
        pass

    @abstractmethod
    def save_partial_output(self):
        pass

    @abstractmethod
    def save_plugin_output(self):
        pass

    @abstractmethod
    def update(self):
        pass


class RequesterInterface(AbstractInterface):

    @abstractmethod
    def GetTransaction(self):
        pass

    @abstractmethod
    def GetTransactions(self):
        pass

    @abstractmethod
    def Request(self):
        pass

    @abstractmethod
    def SetHeaders(self):
        pass


class ResourceInterface(AbstractInterface):

    @abstractmethod
    def get_resource_list(self):
        pass

    @abstractmethod
    def get_resources(self):
        pass


class ShellInterface(AbstractInterface):

    @abstractmethod
    def GetModifiedShellCommand(self):
        pass

    @abstractmethod
    def refresh_replacements(self):
        pass

    @abstractmethod
    def shell_exec(self):
        pass

    @abstractmethod
    def shell_exec_monitor(self):
        pass


class TimerInterface(AbstractInterface):

    @abstractmethod
    def GetElapsedTimeAsStr(self):
        pass

    @abstractmethod
    def GetEndDateTimeAsStr(self):
        pass

    @abstractmethod
    def GetStartDateTimeAsStr(self):
        pass

    @abstractmethod
    def StartTimer(self):
        pass


class TransactionInterface(AbstractInterface):

    @abstractmethod
    def delete_transaction(self):
        pass

    @abstractmethod
    def get_all_as_dicts(self):
        pass

    @abstractmethod
    def get_by_id_as_dict(self):
        pass

    @abstractmethod
    def get_by_ids(self):
        pass

    @abstractmethod
    def get_first(self):
        pass

    @abstractmethod
    def get_session_data(self):
        pass

    @abstractmethod
    def get_top_by_speed(self):
        pass

    @abstractmethod
    def is_already_added(self):
        pass

    @abstractmethod
    def LogTransaction(self):
        pass

    @abstractmethod
    def log_transactions_from_logger(self):
        pass

    @abstractmethod
    def num_transactions(self):
        pass

    @abstractmethod
    def search_all(self):
        pass

    @abstractmethod
    def search_by_regex_name(self):
        pass


class URLManagerInterface(AbstractInterface):

    @abstractmethod
    def add_url(self):
        pass

    @abstractmethod
    def AddURLsEnd(self):
        pass

    @abstractmethod
    def AddURLsStart(self):
        pass

    @abstractmethod
    def get_all(self):
        pass

    @abstractmethod
    def get_urls_to_visit(self):
        pass

    @abstractmethod
    def import_processed_url(self):
        pass

    @abstractmethod
    def import_urls(self):
        pass

    @abstractmethod
    def is_url(self):
        pass

    @abstractmethod
    def search_all(self):
        pass


class WorkerManagerInterface(AbstractInterface):

    @abstractmethod
    def create_worker(self):
        pass

    @abstractmethod
    def delete_worker(self):
        pass

    @abstractmethod
    def fill_work_list(self):
        pass

    @abstractmethod
    def filter_work_list(self):
        pass

    @abstractmethod
    def get_work_list(self):
        pass

    @abstractmethod
    def get_worker_details(self):
        pass

    @abstractmethod
    def manage_workers(self):
        pass


class ZapAPIInterface(AbstractInterface):

    @abstractmethod
    def ForwardRequest(self):
        pass


class ZestInterface(AbstractInterface):

    @abstractmethod
    def GetAllScripts(self):
        pass

    @abstractmethod
    def GetRecordScriptContent(self):
        pass

    @abstractmethod
    def GetTargetConfig(self):
        pass

    @abstractmethod
    def GetTargetScriptContent(self):
        pass

    @abstractmethod
    def IsRecording(self):
        pass

    @abstractmethod
    def RunRecordScript(self):
        pass

    @abstractmethod
    def RunTargetScript(self):
        pass

    @abstractmethod
    def StartRecorder(self):
        pass

    @abstractmethod
    def StopRecorder(self):
        pass

    @abstractmethod
    def TargetScriptFromMultipleTransactions(self):
        pass

    @abstractmethod
    def TargetScriptFromSingleTransaction(self):
        pass

    @abstractmethod
    def addtoRecordedTrans(self):
        pass


class TargetInterface(AbstractInterface):

    @abstractmethod
    def add_target(self):
        pass

    @abstractmethod
    def delete_target(self):
        pass

    @abstractmethod
    def get(self):
        pass

    @abstractmethod
    def GetAll(self):
        pass

    @abstractmethod
    def get_all_in_scope(self):
        pass

    @abstractmethod
    def get_indexed_targets(self):
        pass

    @abstractmethod
    def GetPath(self):
        pass

    @abstractmethod
    def GetTargetConfig(self):
        pass

    @abstractmethod
    def GetTargetConfigForID(self):
        pass

    @abstractmethod
    def GetTargetConfigs(self):
        pass

    @abstractmethod
    def GetTargetID(self):
        pass

    @abstractmethod
    def get_target_url(self):
        pass

    @abstractmethod
    def is_url_in_scope(self):
        pass

    @abstractmethod
    def PathConfig(self):
        pass

    @abstractmethod
    def SetPath(self):
        pass

    @abstractmethod
    def set_target(self):
        pass

    @abstractmethod
    def update_target(self):
        pass


class ConfigInterface(AbstractInterface):

    @abstractmethod
    def cleanup_target_dirs(self):
        pass

    @abstractmethod
    def ConvertStrToBool(self):
        pass

    @abstractmethod
    def create_output_dir_target(self):
        pass

    @abstractmethod
    def derive_config_from_url(self):
        pass

    @abstractmethod
    def get_val(self):
        pass

    @abstractmethod
    def FrameworkConfigGetDBPath(self):
        pass

    @abstractmethod
    def get_log_path(self):
        pass

    @abstractmethod
    def get_logs_dir(self):
        pass

    @abstractmethod
    def get_as_list(self):
        pass

    @abstractmethod
    def get_framework_config_dict(self):
        pass

    @abstractmethod
    def get_header_list(self):
        pass

    @abstractmethod
    def GetOutputDBPathForTarget(self):
        pass

    @abstractmethod
    def get_target_dir(self):
        pass

    @abstractmethod
    def get_output_dir_target(self):
        pass

    @abstractmethod
    def get_replacement_dict(self):
        pass

    @abstractmethod
    def get_resources(self):
        pass

    @abstractmethod
    def GetTransactionDBPathForTarget(self):
        pass

    @abstractmethod
    def GetUrlDBPathForTarget(self):
        pass

    @abstractmethod
    def is_set(self):
        pass

    @abstractmethod
    def MultipleReplace(self):
        pass

    @abstractproperty
    def owtf_pid(self):
        pass

    @abstractmethod
    def ProcessOptions(self):
        pass

    @abstractproperty
    def Profiles(self):
        pass

    @abstractproperty
    def RootDir(self):
        pass

    @abstractmethod
    def Set(self):
        pass


class ReporterInterface(AbstractInterface):

    @abstractmethod
    def reset_loader(self):
        pass

    @abstractmethod
    def sanitize_html(self):
        pass
