from tests.testing_framework.base_test_cases import BaseTestCase
from flexmock import flexmock
from hamcrest import *
from framework.plugin.scanner import Scanner
import re
from os import path
from StringIO import StringIO

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
        services = ["snmp","smb","smtp","ms-sql","ftp","X11","ppp","vnc","http-rpc-epmap","msrpc","http"]
        flexmock(self.scanner)
        self.scanner.should_receive("get_nmap_services_file").and_return(NMAP_SERVICES_FILE)

        for service in services:
            port_list = self.scanner.get_ports_for_service(service, "")
            assert_that(isinstance(port_list, list))
            assert_that(port_list is not None)

    def test_target_service_scans_nmap_output_file(self):
        file_content = "Host: 127.0.0.1\tPorts: 7/filtered/tcp//echo//, 80/open/tcp//http/Microsoft IIS\t\n"
        fake_file = flexmock()
        fake_file.should_receive("read").and_return(file_content).once()
        fake_file.should_receive("close").once()
        flexmock(self.scanner)
        self.scanner.should_receive("get_ports_for_service").and_return(["7", "80"])
        self.scanner.should_receive("open_file").and_return(fake_file)

        self.scanner.target_service("nmap_file", "service")

    def test_probe_service_for_hosts_sets_plugin_list_to_execute_and_returns_http_ports(self):
        flexmock(self.scanner)
        self.scanner.should_receive("target_service").and_return("127.0.0.1:80")
        self.core_mock.Config = flexmock()
        self.core_mock.Config.should_receive("Set")
        self.core_mock.PluginHandler = flexmock()
        self.core_mock.PluginHandler.should_receive("ValidateAndFormatPluginList").once()
        
        http_ports = self.scanner.probe_service_for_hosts("nmap_file", "target")
        
        assert_that(isinstance(http_ports, list))
        assert_that(http_ports, has_length(greater_than(0)))

    def _create_core_mock(self):
        self.core_mock = flexmock()
        self.core_mock.Shell = flexmock()
        self._stub_shell_method("shell_exec", None)

    def _stub_shell_method(self, method, expected_result):
        self.core_mock.Shell.should_receive(method).and_return(expected_result)

    def _mock_shell_method_with_args_once(self, method, args):
        self.core_mock.Shell.should_receive(method).with_args(args).once()
