"""
owtf.dependency_management.component_initializer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Implements 3 phased component initialization process
"""

from owtf.config.config import Config
from owtf.db.command_register import CommandRegister
from owtf.db.config_manager import ConfigDB
from owtf.db.db import DB
from owtf.db.error_manager import ErrorDB
from owtf.db.mapping_manager import MappingDB
from owtf.db.plugin_manager import PluginDB
from owtf.db.poutput_manager import POutputDB
from owtf.db.resource_manager import ResourceDB
from owtf.db.session_manager import OWTFSessionDB
from owtf.db.target_manager import TargetDB
from owtf.db.transaction_manager import TransactionManager
from owtf.db.url_manager import URLManager
from owtf.db.worklist_manager import WorklistManager
from owtf.dependency_management.dependency_resolver import ServiceLocator
from owtf.error_handler import ErrorHandler
from owtf.http.requester import Requester
from owtf.interface.reporter import Reporter
from owtf.plugin.plugin_handler import PluginHandler
from owtf.plugin.plugin_helper import PluginHelper
from owtf.plugin.plugin_params import PluginParams
from owtf.protocols.smtp import SMTP
from owtf.protocols.smb import SMB
from owtf.selenium.selenium_handler import Selenium
from owtf.shell.blocking_shell import Shell
from owtf.shell.interactive_shell import InteractiveShell
from owtf.timer import Timer
from owtf.wrappers.set.set_handler import SETHandler


class ComponentInitialiser():
    """
        Initialises all the components for the OWTF owtf. The order is important as
        there are dependencies between modules. Cyclic dependencies are solved using a
        two-step initialization process through an init() method.
    """

    @staticmethod
    def initialisation_phase_1(root_dir, owtf_pid):
        """First phase of the initialization.

        :param str root_dir: Absolute path to the OWTF root.
        :param int owtf_pid: PID for the OWTF process.

        """
        Config(root_dir, owtf_pid)
        ErrorHandler()
        DB()
        try:
            OWTFSessionDB()
        except:
            raise DatabaseNotRunningException()
        WorklistManager()
        ConfigDB()
        CommandRegister()
        TargetDB()
        ResourceDB()
        ErrorDB()
        MappingDB()
        PluginDB()
        URLManager()
        TransactionManager()

    @staticmethod
    def initialisation_phase_2(args):
        """ Second phase of the initialization process.

        :param dict args: parsed arguments from the command line.
        """
        db_config = ServiceLocator.get_component("db_config")
        db_config.init()
        Timer(db_config.Get('DATE_TIME_FORMAT'))
        ServiceLocator.get_component("db_plugin").init()
        ServiceLocator.get_component("config").init()
        PluginHandler(args)
        Reporter()
        POutputDB()
        ServiceLocator.get_component("command_register").init()
        ServiceLocator.get_component("worklist_manager").init()
        Shell()
        PluginParams(args)
        SMB()
        InteractiveShell()
        Selenium()
        SMTP()
        SETHandler()

    @staticmethod
    def initialisation_phase_3(options):
        """ Third phase of the initialization process.

        :param list proxy: Proxy configuration parameters
        :param dict options: Options from command line.
        """
        ServiceLocator.get_component("resource").init()
        ServiceLocator.get_component("mapping_db").init()
        ServiceLocator.get_component("db").init()
        db_config = ServiceLocator.get_component("db_config")
        ServiceLocator.get_component("error_handler").init()
        proxy = [db_config.Get('INBOUND_PROXY_IP'), db_config.Get('INBOUND_PROXY_PORT')]
        Requester(proxy)
        PluginHelper()
        ServiceLocator.get_component("plugin_handler").init(options)
        ServiceLocator.get_component("reporter").init()


class DatabaseNotRunningException(Exception):
    pass
