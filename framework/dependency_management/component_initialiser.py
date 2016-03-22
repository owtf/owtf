
import logging
import multiprocessing
from datetime import time

from framework.config.config import Config
from framework.db.command_register import CommandRegister
from framework.db.config_manager import ConfigDB
from framework.db.db import DB
from framework.db.error_manager import ErrorDB
from framework.db.mapping_manager import MappingDB
from framework.db.plugin_manager import PluginDB
from framework.db.poutput_manager import POutputDB
from framework.db.resource_manager import ResourceDB
from framework.db.session_manager import OWTFSessionDB
from framework.db.target_manager import TargetDB
from framework.db.transaction_manager import TransactionManager
from framework.db.url_manager import URLManager
from framework.db.worklist_manager import WorklistManager
from framework.dependency_management.dependency_resolver import ServiceLocator
from framework.error_handler import ErrorHandler
from framework.http.proxy.outbound_proxyminer import Proxy_Miner
from framework.http.proxy.proxy_manager import Proxy_manager, Proxy_Checker
from framework.http.requester import Requester
from framework.interface.reporter import Reporter
from framework.lib.general import cprint
from framework.plugin.plugin_handler import PluginHandler
from framework.plugin.plugin_helper import PluginHelper
from framework.plugin.plugin_params import PluginParams
from framework.protocols.smtp import SMTP
from framework.shell.blocking_shell import Shell
from framework.timer import Timer
from framework.zap import ZAP_API
from framework.zest import Zest


class ComponentInitialiser():
    """
        Initialises all the components for the OWTF framework. The order is important as
        there are dependencies between modules. Cyclic dependencies are solved using a
        two-step initialization process through an init() method.
    """

    @staticmethod
    def initialisation_phase_1(root_dir, owtf_pid):
        """First phase of the initialization.

        :param str root_dir: Absolute path to the OWTF root.
        :param int owtf_pid: PID for the OWTF process.

        """
        config = Config(root_dir, owtf_pid)
        ErrorHandler()
        DB()
        try:
            OWTFSessionDB()
        except:
            raise DatabaseNotRunningException()
        WorklistManager()
        db_config = ConfigDB()
        CommandRegister()
        TargetDB()
        ResourceDB()
        ErrorDB()
        MappingDB()
        Timer(db_config.Get('DATE_TIME_FORMAT'))
        PluginDB()
        zest = Zest()
        URLManager()
        TransactionManager()
        config.init()
        zest.init()

    @staticmethod
    def initialisation_phase_2(args):
        """ Second phase of the initialization process.

        :param dict args: parsed arguments from the command line.
        """
        PluginHandler(args)
        Reporter()
        POutputDB()
        ServiceLocator.get_component("command_register").init()
        ServiceLocator.get_component("worklist_manager").init()
        Shell()
        PluginParams(args)
        SMTP()
        #DebugDB()
        ZAP_API()

    @staticmethod
    def initialisation_phase_3(proxy, options):
        """ Third phase of the initialization process.

        :param list proxy: Proxy configuration parameters
        :param dict options: Options from command line.
        """
        ServiceLocator.get_component("db").init()
        ServiceLocator.get_component("error_handler").init()
        Requester(proxy)
        PluginHelper()
        ServiceLocator.get_component("plugin_handler").init(options)
        ServiceLocator.get_component("reporter").init()

    @staticmethod
    def intialise_proxy_manager(options):
        """ Proxy Manager initialization.

        :param dict options: Proxy manager configuration parameters.
        """
        proxy_manager = None
        if options['Botnet_mode'] is not None:
            proxy_manager = Proxy_manager()
            answer = "Yes"
            proxies = []
            if options['Botnet_mode'][0] == "miner":
                miner = Proxy_Miner()
                proxies = miner.start_miner()

            if options['Botnet_mode'][0] == "list":  # load proxies from list
                proxies = proxy_manager.load_proxy_list(
                    options['Botnet_mode'][1]
                )
                answer = raw_input(
                    "[#] Do you want to check the proxy list? [Yes/no] : "
                )

            if answer.upper() in ["", "YES", "Y"]:
                proxy_q = multiprocessing.Queue()
                proxy_checker = multiprocessing.Process(
                    target=Proxy_Checker.check_proxies,
                    args=(proxy_q, proxies,)
                )
                logging.info("Checking Proxies...")
                start_time = time.time()
                proxy_checker.start()
                proxies = proxy_q.get()
                proxy_checker.join()

            proxy_manager.proxies = proxies
            proxy_manager.number_of_proxies = len(proxies)

            if options['Botnet_mode'][0] == "miner":
                logging.info("Writing proxies to disk(~/.owtf/proxy_miner/proxies.txt)")
                miner.export_proxies_to_file("proxies.txt", proxies)
            if answer.upper() in ["", "YES", "Y"]:
                logging.info(
                    "Proxy Check Time: %s",
                    time.strftime(
                        '%H:%M:%S',
                        time.localtime(time.time() - start_time - 3600)
                    )
                )
                cprint("Done")

            if proxy_manager.number_of_proxies is 0:
                ServiceLocator.get_component("error_handler").FrameworkAbort("No Alive proxies.")

            proxy = proxy_manager.get_next_available_proxy()

            # check proxy var... http:// sock://
            options['OutboundProxy'] = []
            options['OutboundProxy'].append(proxy["proxy"][0])
            options['OutboundProxy'].append(proxy["proxy"][1])


class DatabaseNotRunningException(Exception):
    pass
