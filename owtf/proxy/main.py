"""
owtf.proxy.main
~~~~~~~~~~~~~~~
"""
import logging
import os
import re
import socket

import tornado
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from owtf.lib.owtf_process import OWTFProcess
from owtf.proxy.proxy import ProxyHandler
from owtf.settings import (
    BLACKLIST_COOKIES,
    CA_CERT,
    CA_KEY,
    CA_PASS_FILE,
    CERTS_FOLDER,
    HTTP_AUTH_HOST,
    HTTP_AUTH_MODE,
    HTTP_AUTH_PASSWORD,
    HTTP_AUTH_USERNAME,
    INBOUND_PROXY_CACHE_DIR,
    INBOUND_PROXY_IP,
    INBOUND_PROXY_PORT,
    INBOUND_PROXY_PROCESSES,
    OUTBOUND_PROXY_AUTH,
    PROXY_LOG,
    PROXY_RESTRICTED_REQUEST_HEADERS,
    PROXY_RESTRICTED_RESPONSE_HEADERS,
    USE_OUTBOUND_PROXY,
    WHITELIST_COOKIES,
)
from owtf.utils.error import abort_framework
from owtf.utils.file import FileOperations


class ProxyProcess(OWTFProcess):

    def initialize(self, outbound_options=None, outbound_auth=""):
        """Initialize the proxy process

        :param outbound_options: Outbound proxy options
        :type outbound_options: `list`
        :param outbound_auth: Authentication string
        :type outbound_auth: `str`
        :return: None
        :rtype: None
        """
        # The tornado application, which is used to pass variables to request handler
        self.application = tornado.web.Application(
            handlers=[(r".*", ProxyHandler)], debug=False, gzip=True
        )
        # All required variables in request handler
        # Required variables are added as attributes to application, so that request handler can access these
        self.application.inbound_ip = INBOUND_PROXY_IP
        self.application.inbound_port = int(INBOUND_PROXY_PORT)
        self.instances = INBOUND_PROXY_PROCESSES

        # Proxy CACHE
        # Cache related settings, including creating required folders according to cache folder structure
        self.application.cache_dir = INBOUND_PROXY_CACHE_DIR
        # Clean possible older cache directory.
        if os.path.exists(self.application.cache_dir):
            FileOperations.rm_tree(self.application.cache_dir)
        FileOperations.make_dirs(self.application.cache_dir)

        # SSL MiTM
        # SSL certs, keys and other settings (os.path.expanduser because they are stored in users home directory
        # ~/.owtf/proxy)
        self.application.ca_cert = os.path.expanduser(CA_CERT)
        self.application.ca_key = os.path.expanduser(CA_KEY)
        # To stop OWTF from breaking for our beloved users :P
        try:
            self.application.ca_key_pass = FileOperations.open(
                os.path.expanduser(CA_PASS_FILE), "r", owtf_clean=False
            ).read().strip()
        except IOError:
            self.application.ca_key_pass = "owtf"  # XXX: Legacy CA key pass for older versions.
        self.application.proxy_folder = os.path.dirname(self.application.ca_cert)
        self.application.certs_folder = os.path.expanduser(CERTS_FOLDER)

        try:  # Ensure CA.crt and Key exist.
            assert os.path.exists(self.application.ca_cert)
            assert os.path.exists(self.application.ca_key)
        except AssertionError:
            abort_framework(
                "Files required for SSL MiTM are missing.Please run the install script"
            )

        try:  # If certs folder missing, create that.
            assert os.path.exists(self.application.certs_folder)
        except AssertionError:
            FileOperations.make_dirs(self.application.certs_folder)

        # Blacklist (or) Whitelist Cookies
        # Building cookie regex to be used for cookie filtering for caching
        if WHITELIST_COOKIES == "None":
            cookies_list = BLACKLIST_COOKIES.split(",")
            self.application.cookie_blacklist = True
        else:
            cookies_list = WHITELIST_COOKIES.split(",")
            self.application.cookie_blacklist = False
        if self.application.cookie_blacklist:
            regex_cookies_list = [cookie + "=([^;]+;?)" for cookie in cookies_list]
        else:
            regex_cookies_list = ["(" + cookie + "=[^;]+;?)" for cookie in cookies_list]
        regex_string = "|".join(regex_cookies_list)
        self.application.cookie_regex = re.compile(regex_string)

        # Outbound Proxy
        # Outbound proxy settings to be used inside request handler
        if outbound_options and outbound_options is not None:
            if len(outbound_options) == 3:
                self.application.outbound_proxy_type = outbound_options[0]
                self.application.outbound_ip = outbound_options[1]
                self.application.outbound_port = int(outbound_options[2])
            else:
                self.application.outbound_proxy_type = "http"
                self.application.outbound_ip = outbound_options[0]
                self.application.outbound_port = int(outbound_options[1])
        else:
            self.application.outbound_ip = None
            self.application.outbound_port = None
            self.application.outbound_proxy_type = None
        if outbound_auth:
            self.application.outbound_username, self.application.outbound_password = outbound_auth.split(
                ":"
            )
        else:
            self.application.outbound_username = None
            self.application.outbound_password = None

        self.server = tornado.httpserver.HTTPServer(self.application)
        # server has to be a class variable, because it is used inside request handler to attach sockets for monitoring
        ProxyHandler.server = self.server

        # Header filters
        # These headers are removed from the response obtained from webserver, before sending it to browser
        ProxyHandler.restricted_response_headers = PROXY_RESTRICTED_RESPONSE_HEADERS
        # These headers are removed from request obtained from browser, before sending it to webserver
        ProxyHandler.restricted_request_headers = PROXY_RESTRICTED_REQUEST_HEADERS

        # HTTP Auth options
        if HTTP_AUTH_HOST is not None:
            self.application.http_auth = True
            # All the variables are lists
            self.application.http_auth_hosts = HTTP_AUTH_HOST.strip().split(",")
            self.application.http_auth_usernames = HTTP_AUTH_USERNAME.strip().split(",")
            self.application.http_auth_passwords = HTTP_AUTH_PASSWORD.strip().split(",")
            self.application.http_auth_modes = HTTP_AUTH_MODE.strip().split(",")
        else:
            self.application.http_auth = False

    def pseudo_run(self):
        """Run function for the multiprocessing proxy

        :return: None
        :rtype: None
        """
        try:
            # Disable console logging
            self.logger.disable_console_logging()
            self.server.bind(
                self.application.inbound_port, address=self.application.inbound_ip
            )
            # Useful for using custom loggers because of relative paths in secure requests
            # http://www.joet3ch.com/blog/2011/09/08/alternative-tornado-logging/
            tornado.options.parse_command_line(
                args=[
                    "dummy_arg",
                    "--log_file_prefix={}".format(PROXY_LOG),
                    "--logging=info",
                ]
            )
            # To run any number of instances
            # "0" equals the number of cores present in a machine
            self.server.start(int(self.instances))
            tornado.ioloop.IOLoop.instance().start()
        except BaseException:
            # Cleanup code
            self.clean_up()

    def clean_up(self):
        """Stop the instances

        :return: None
        :rtype: None
        """
        self.server.stop()
        tornado.ioloop.IOLoop.instance().stop()


def start_proxy():
    """ The proxy along with supporting processes are started here

    :param options: Optional arguments
    :type options: `dict`
    :return:
    :rtype: None
    """
    if True:
        # Check if port is in use
        try:
            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            temp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            temp_socket.bind((INBOUND_PROXY_IP, INBOUND_PROXY_PORT))
            temp_socket.close()
        except socket.error:
            abort_framework("Inbound proxy address already in use")
        # If everything is fine.
        proxy_process = ProxyProcess()
        logging.warn(
            "Starting HTTP(s) proxy server at %s:%d",
            INBOUND_PROXY_IP,
            INBOUND_PROXY_PORT,
        )
        proxy_process.initialize(USE_OUTBOUND_PROXY, OUTBOUND_PROXY_AUTH)
        proxy_process.start()
        logging.debug("Proxy transaction's log file at %s", PROXY_LOG)


if __name__ == "__main__":
    start_proxy()
