from tests.testing_framework.base_test_cases import BaseTestCase
from flexmock import flexmock
from hamcrest import *
from framework.plugin.scanner import Scanner
import re
from os import path
from StringIO import StringIO
from compiler.ast import And
from tests.testing_framework.doubles.files import FileMock

NMAP_SERVICES_FILE = path.abspath("test_cases/resources/nmap-services")


class ScannerTests(BaseTestCase):

    def before(self):
        self._create_core_mock()
        self.scanner = Scanner(self.core_mock)

    def test_ping_sweep_with_full_scan_executes_nmap_and_grep(self):
        nmap_regex = re.compile("nmap.*[-]PS.*")
        grep_regex = re.compile("grep.*")
        self._mock_shell_method_with_args_once("shell_exec", nmap_regex)
        self._mock_shell_method_with_args_once("shell_exec", grep_regex)

        self.scanner.ping_sweep("target", "full")

    def test_ping_sweep_with_arp_scan_executes_nmap_and_grep(self):
        nmap_regex = re.compile("nmap.*[-]PR.*")
        grep_regex = re.compile("grep.*")
        self._mock_shell_method_with_args_once("shell_exec", nmap_regex)
        self._mock_shell_method_with_args_once("shell_exec", grep_regex)

        self.scanner.ping_sweep("target", "arp")

    def test_scan_and_grab_banners_with_tcp_uses_nmap_and_amap_for_fingerprinting(self):
        nmap_regex = re.compile("nmap.*[-](sV|sS).*[-](sV|sS).*")
        amap_regex = re.compile("amap.*")
        self._mock_shell_method_with_args_once("shell_exec", nmap_regex)
        self._mock_shell_method_with_args_once("shell_exec", amap_regex)

        self.scanner.scan_and_grab_banners("file_with_ips", "file_prefix", "tcp", "")

    def test_scan_and_grab_banners_with_udp_uses_nmap_and_amap_for_fingerprinting(self):
        nmap_regex = re.compile("nmap.*[-](sV|sU).*[-](sV|sU).*")
        amap_regex = re.compile("amap.*")
        self._mock_shell_method_with_args_once("shell_exec", nmap_regex)
        self._mock_shell_method_with_args_once("shell_exec", amap_regex)

        self.scanner.scan_and_grab_banners("file_with_ips", "file_prefix", "udp", "")

    def test_get_ports_for_service_returns_the_list_of_ports_associated_to_services(self):
        services = ["snmp", "smb", "smtp", "ms-sql", "ftp", "X11", "ppp", "vnc", "http-rpc-epmap", "msrpc", "http"]
        flexmock(self.scanner)
        self.scanner.should_receive("get_nmap_services_file").and_return(NMAP_SERVICES_FILE)

        for service in services:
            port_list = self.scanner.get_ports_for_service(service, "")
            assert_that(isinstance(port_list, list))
            assert_that(port_list is not None)

    def test_target_service_scans_nmap_output_file(self):
        file_lines = ["Host: 127.0.0.1\tPorts: 7/filtered/tcp//echo//, 80/open/tcp//http/Microsoft IIS\t\n"]
        flexmock(self.scanner)
        self.scanner.should_receive("open_file").and_return(FileMock(file_lines))

        self.scanner.target_service("nmap_file", "service")

    def test_probe_service_for_hosts_sets_plugin_list_to_execute_and_returns_http_ports(self):
        flexmock(self.scanner)
        self.scanner.should_receive("target_service").and_return("127.0.0.1:80")
        self.core_mock.Config = flexmock()
        self.core_mock.Config.should_receive("Set")
        self.core_mock.PluginHandler = flexmock()
        self.core_mock.PluginHandler.should_receive("ValidateAndFormatPluginList").once()
        self.core_mock.Config.Plugin = flexmock()
        net_order = [{"Name": "ftp"},
                     {"Name": "smtp"},
                     {"Name": "vnc"}]
        self.core_mock.Config.Plugin.should_receive("GetOrder").with_args("net").and_return(net_order)

        http_ports = self.scanner.probe_service_for_hosts("nmap_file", "target")

        assert_that(isinstance(http_ports, list))
        assert_that(http_ports, has_length(greater_than(0)))

    def test_dns_sweep_looks_for_DNS_servers_and_abort_execution_if_no_domain_is_found(self):
        self._record_dns_sweep_first_steps()

        flexmock(self.scanner)
        self._stub_open_file(re.compile(".*\.dns_server.ips"), ["127.0.0.1\n", "127.0.0.1\n"])
        self.scanner.should_receive("open_file").with_args(re.compile(".*\.domain_names")).and_raise(IOError).once()

        self.scanner.dns_sweep("file_with_ips.txt", "file_prefix")

    def test_dns_sweep_looks_for_DNS_servers_and_tries_to_do_a_zone_transfer_on_found_domains(self):
        self._record_dns_sweep_first_steps()

        flexmock(self.scanner)
        self._stub_open_file(re.compile(".*\.dns_server.ips"), ["127.0.0.1\n", "127.0.0.1\n"])
        self._stub_open_file(re.compile(".*\.domain_names"), ["domain1.com"])

        self._mock_shell_method_with_args_once("shell_exec", re.compile("host [-]l.*"))  # Retrieve domains
        self._mock_shell_method_with_args_once("shell_exec", re.compile("wc\s[-]l.*cut.*"), return_value=4)  # Determines if succeeded
        self._mock_shell_method_with_args_once("shell_exec", re.compile("rm\s[-]f\s.*\.axfr.*"))

        self.scanner.dns_sweep("file_with_ips.txt", "file_prefix")

    def _create_core_mock(self):
        self.core_mock = flexmock()
        self.core_mock.Shell = flexmock()
        self._stub_shell_method("shell_exec", None)

    def _stub_shell_method(self, method, expected_result):
        self.core_mock.Shell.should_receive(method).and_return(expected_result)

    def _mock_shell_method_with_args_once(self, method, args, return_value=None):
        if (return_value is None):
            self.core_mock.Shell.should_receive(method).with_args(args).once()
        else:
            self.core_mock.Shell.should_receive(method).with_args(args).and_return(return_value).once()

    def _record_dns_sweep_first_steps(self):
        nmap_dns_discovery_regex = re.compile("nmap.*[-]sS.*[-]p\s53.*")
        grep_open_53_port_regex = re.compile("grep.*53/open")
        rm_old_files_regex = re.compile("rm [-]f .*\.domain_names")
        self._mock_shell_method_with_args_once("shell_exec", nmap_dns_discovery_regex)
        self._mock_shell_method_with_args_once("shell_exec", grep_open_53_port_regex)
        self._mock_shell_method_with_args_once("shell_exec", rm_old_files_regex)

    def _stub_open_file(self, args, file_lines):
        returned_file = FileMock(file_lines)
        self.scanner.should_receive("open_file").with_args(args).and_return(returned_file)
