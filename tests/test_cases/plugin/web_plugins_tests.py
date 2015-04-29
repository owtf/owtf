from tests.testing_framework.base_test_cases import WebPluginTestCase
from hamcrest import *
import tornado.web
import cgi
import time
from nose_parameterized import parameterized
import unittest


class SlowApp(tornado.web.RequestHandler):

    def get(self):
        time.sleep(3)
        self.write("slow transaction")


class WebPluginsTests(WebPluginTestCase):

    @classmethod
    def setUpClass(cls):
        super(WebPluginsTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(WebPluginsTests, cls).tearDownClass()

    #  Active plugins  #
    # For general tools as Arachni, Nikto, Skipfish... we don't check
    # the results, only that the tool has been executed.

    def test_Application_Discovery_active(self):
        self._prepare_test_for_general_tool()

        self.owtf("-g web -t active -o Application_Discovery")

        self.assert_that_output_contains("Plugin: Application Discovery (active)")
        self.assert_external_tool_started(times=1)
        tools = ["dnsrecon"]
        self.assert_that_output_contains_lines(tools)

    def test_Arachni_Unauthenticated_active(self):
        self._prepare_test_for_general_tool()

        self.owtf("-g web -t active -o Arachni_Unauthenticated")

        arachni_banner = ["Arachni - Web Application Security Scanner Framework",
                         "Author: Tasos \"Zapotek\" Laskos"]

        # Checking for plugin banner
        self.assert_that_output_contains("Plugin: Arachni Unauthenticated (active)")
        # Checking for plugin start. Arachni plugin runs 2 tools.
        self.assert_external_tool_started(times=2)
        # Checking for Arachni banner
        self.assert_that_output_contains_lines(arachni_banner)

    def test_HTTP_Methods_and_XST_active(self):
        self._prepare_test_for_HTTP_Methods_and_XST()

        self.owtf("-g web -t active -o HTTP_Methods_and_XST")

        self.assert_that_output_contains("Plugin: Http Methods And Xst (active)")
        # This plugin runs 4 tools.
        self.assert_external_tool_started(times=4)
        tools = ["curl", "hoppy", "extract_urls.sh"]
        self.assert_that_output_contains_lines(tools)

    @unittest.skip("There is a problem with this test. If it fails, the runner process hangs. Affected by the issue #48")
    def test_Infrastructure_Configuration_Management_active(self):
        self._prepare_test_for_general_tool()

        self.owtf("-g web -t active -o Infrastructure_Configuration_Management")

        self.assert_that_output_contains("Plugin: Infrastructure Configuration Management (active)")
        # This plugin runs 5 tools
        self.assert_external_tool_started(times=5)
        tools = ["wafw00f", "lbd", "HTTP-Traceroute.py", "ua-tester"]
        self.assert_that_output_contains_lines(tools)

    def test_Old_Backup_and_Unreferenced_Files_active(self):
        self._prepare_test_for_general_tool()

        self.owtf("-g web -t active -o Old_Backup_and_Unreferenced_Files")

        self.assert_that_output_contains("Plugin: Old Backup And Unreferenced Files (active)")
        # This plugin runs 2 tools
        self.assert_external_tool_started(times=2)
        tools = ["dirbuster", "extract_urls.sh"]
        self.assert_that_output_contains_lines(tools)

    def test_Skipfish_Unauthenticated_active(self):
        self._prepare_test_for_general_tool()

        self.owtf("-g web -t active -o Skipfish_Unauthenticated")

        self.assert_that_output_contains("Plugin: Skipfish Unauthenticated (active)")
        # This plugin runs only 1 tool
        self.assert_external_tool_started(times=1)
        skipfish_banner = ["skipfish version", "by <lcamtuf@google.com>"]
        self.assert_that_output_contains_lines(skipfish_banner)

    def test_for_SSL_TLS_active(self):
        self._prepare_test_for_general_tool()

        self.owtf("-g web -t active -o Testing_for_SSL-TLS")

        self.assert_that_output_contains("Plugin: Testing For Ssl-Tls (active)")
        self.assert_external_tool_started(times=2)
        tool_banners = ["TLSSLed",
                        "based on sslscan and openssl",
                        "by Raul Siles (www.taddong.com)",
                        "verify_ssl_cipher_check.sh",
                        "Author: Abraham Aranguren @7a_ http://7-a.org"]
        self.assert_that_output_contains_lines(tool_banners)

    def test_W3AF_Unauthenticated_active(self):
        self._prepare_test_for_general_tool()

        self.owtf("-g web -t active -o W3AF_Unauthenticated")

        self.assert_that_output_contains("Plugin: W3Af Unauthenticated (active)")
        self.assert_external_tool_started(times=2)
        tools = ["run_w3af.sh", "extract_urls.sh"]
        self.assert_that_output_contains_lines(tools)

    def test_Wapiti_Unauthenticated_active(self):
        self._prepare_test_for_general_tool()

        self.owtf("-g web -t active -o Wapiti_Unauthenticated")

        self.assert_that_output_contains("Plugin: Wapiti Unauthenticated (active)")
        self.assert_external_tool_started(times=1)
        wapiti_lines = ["wapiti.py", "Wapiti", "(wapiti.sourceforge.net)"]
        self.assert_that_output_contains_lines(wapiti_lines)

    def test_Web_Application_Fingerprint_active(self):
        self._prepare_test_for_general_tool()

        self.owtf("-g web -t active -o Web_Application_Fingerprint")

        self.assert_that_output_contains("Plugin: Web Application Fingerprint (active)")
        self.assert_external_tool_started(times=2)
        tools = ["whatweb", "httprint"]

    #  Semi-passive plugins  #

    def test_HTTP_Methods_and_XST_semi_passive(self):
        self._prepare_test_for_HTTP_Methods_and_XST()

        self.owtf("-g web -t semi_passive -o HTTP_Methods_and_XST")

        self.assert_that_output_contains("Allow: GET, HEAD, OPTIONS")  # curl output

    def test_Search_engine_discovery_reconaissance_semi_passive(self):
        self._prepare_test_for_general_tool()

        self.owtf("-g web -t semi_passive -o Search_engine_discovery_reconnaissance")

        self.assert_external_tool_started(times=1)
        metagoofil_banner = ["Metagoofil Ver", "Christian Martorella", "Edge-Security.com"]
        self.assert_that_output_contains_lines(metagoofil_banner)

    def test_Spiders_Robots_and_Crawlers_semi_passive(self):
        robots_path = self.get_resource_path("www/robots") # Only 1 file in this folder
        self.set_custom_handler("/(.*)", tornado.web.StaticFileHandler, {"path": robots_path})
        self.start_server()

        self.owtf("-g web -t semi_passive -o Spiders_Robots_and_Crawlers")

        # Check allow entries
        self.assert_that_output_contains(self.ANCHOR_PATTERN % self.get_url("/private"))
        # Check disallow entries
        self.assert_that_output_contains(self.ANCHOR_PATTERN % self.get_url("/public"))
        # Check special urls, contains a space
        self.assert_that_output_contains(self.ANCHOR_PATTERN % self.get_url("/\tmalformed")) # With a tab
        # Check that other urls with misspelled key words are included (Diallow)
        self.assert_that_output_contains(self.ANCHOR_PATTERN % self.get_url("/misspelled"))
        # Check that repeated urls are showed only once
        self.assert_that_output_contains(self.ANCHOR_PATTERN % self.get_url("/repeated"), times=1)

    def test_for_Cross_site_flashing_semi_passive(self):
        files_path = self.get_resource_path("www/CSF")
        self.set_custom_handler("/(.*)", tornado.web.StaticFileHandler, {"path": files_path})
        self.start_server()

        self.owtf("-g web -t semi_passive -o Testing_for_Cross_site_flashing")

        crossdomain = open(files_path + "/crossdomain.xml", "r")
        clientaccesspolicy = open(files_path + "/clientaccesspolicy.xml", "r")

        # The plugin has to retrieve and show the content of the files
        # It shows HTML, so the content is escaped
        for line in crossdomain:
            self.assert_that_output_contains(cgi.escape(line))
        for line in clientaccesspolicy:
            self.assert_that_output_contains(cgi.escape(line))

        crossdomain.close()
        clientaccesspolicy.close()

    def test_Web_Application_Fingerprint_semi_passive(self):
        file_path = self.get_resource_path("www/hello_world.html")
        self.set_get_response_from_file("/app-fingerprint-semi-passive",
                                        file_path,
                                        headers={"Server": "CustomServer/1.0"})
        self.start_server()
        self.visit_url(self.get_url("/app-fingerprint-semi-passive"))

        self.owtf("-g web -t semi_passive -o Web_Application_Fingerprint")

        self.assert_that_output_contains("CustomServer/1.0")

    # Passive plugins #
    # Here we have parametrized tests for the passive plugins, because
    # the testing for this kind of plugin is always the same.

    @parameterized.expand([
    ("Application_Discovery", "PassiveAppDiscovery"),
    ("HTTP_Methods_and_XST", "PassiveMethods"),
    ("Old_Backup_and_Unreferenced_Files", "PassiveOldBackupUnreferencedFilesLnk"),
    ("Spiders_Robots_and_Crawlers", ["PassiveRobotsAnalysisHTTPRequests", "PassiveRobotsAnalysisLinks"]),
    ("Testing_for_Admin_Interfaces", "PassiveAdminInterfaceLnk"),
    ("Testing_for_Captcha", "PassiveCAPTCHALnk"),
    ("Testing_for_Cross_site_flashing", "PassiveCrossSiteFlashingLnk"),
    ("Testing_for_Error_Code", "PassiveErrorMessagesLnk"),
    ("Testing_for_SQL_Injection", "PassiveSQLInjectionLnk"),
    ("Testing_for_SSL-TLS", "PassiveSSL"),
    ("Web_Application_Fingerprint", "PassiveFingerPrint"),
    ("WS_Information_Gathering", "WSPassiveSearchEngineDiscoveryLnk")
    ])
    def test_passive(self, plugin_name, resource_name):
        self.owtf("-g web -t passive -o " + plugin_name)
        self.check_link_generation_for_resources(resource_name)

    def test_Search_engine_discovery_reconnaissance_passive(self):
        self.owtf("-g web -t passive -o Search_engine_discovery_reconnaissance")
        self.assert_external_tool_started(times=2)
        tools = ["theharvester", "search_email_collector"]
        self.assert_that_output_contains_lines(tools)
        self.check_link_generation_for_resources("PassiveSearchEngineDiscoveryLnk")

    #  Grep plugins  #

    def test_Application_Configuration_Management_grep(self):
        # Looks for comments in html, css, js...
        content = "<html><body><!--HTML comment--><script>/*JS comment*/</script></body></html>"
        self.set_get_response("/appConfManagement", content)
        self.start_server()
        self.visit_url(self.get_url("/appConfManagement"))

        self.owtf("-g web -t grep -o Application_Configuration_Management")

        self.assert_that_output_contains("Unique HTML Comments found")
        self.assert_that_output_contains("Unique CSS/JS Comments found")

    def test_Clickjacking_grep(self):
        # Looks for headers used to mitigate clickjacking attacks
        clickjacking_headers = ["X-Frame-Options", "X-Content-Security-Policy"]
        headers = self.generate_headers_with_tokens(clickjacking_headers)
        self.set_get_response("/clickjacking", "", headers=headers)
        self.start_server()
        self.visit_url(self.get_url("/clickjacking"))

        self.owtf("-g web -t grep -o Clickjacking")

        self.assert_that_output_contains_lines(headers.values())

    def test_Cookies_attributes_grep(self):
        # Looks for transactions with cookies and finds their attributes
        token = self.generate_random_token()
        cookie = "ID=" + token + ";secure;HttpOnly"
        headers = {"Set-Cookie": cookie}
        self.set_get_response("/cookies", "", headers=headers)
        self.start_server()
        self.visit_url(self.get_url("/cookies"))

        self.owtf("-g web -t grep -o Cookies_attributes")

        self.assert_that_output_contains_lines([token, "secure", "HttpOnly"])

    def test_CORS_grep(self):
        # Looks for some headers used for Cross-Origin resource sharing
        cors_headers = ["Access-Control-Allow-Origin",
                        "Access-Control-Allow-Credentials"]
        headers = self.generate_headers_with_tokens(cors_headers)
        self.set_get_response("/cors", "", headers=headers)
        self.start_server()
        self.visit_url(self.get_url("/cors"))

        self.owtf("-g web -t grep -o CORS")

        self.assert_that_output_contains_lines(headers.values())

    def test_Credentials_transport_over_an_encrypted_channel_grep(self):
        # Looks for forms with password inputs loaded through http
        self._prepare_test_with_login_form_in("/credentials-encrypted_channel")

        self.owtf("-g web -t grep -o Credentials_transport_over_an_encrypted_channel")

        self.assert_that_output_contains("Total insecure matches: 1")

    def test_DoS_Failure_to_Release_Resources_grep(self):
        self.set_custom_handler("/slow-transaction", SlowApp)
        self.start_server()
        self.visit_url(self.get_url("/slow-transaction"))

        self.owtf("-g web -t grep -o DoS_Failure_to_Release_Resources")

        self.fail("The transaction log in txt format is not written, so the plugin does not find transactions")
        # TODO: To determine which assertions are necessary, the bug has to be fixed

    def test_Logout_and_Browser_Cache_Management_grep(self):
        # Looks for some cache headers and meta tags in the response and HTML content
        header_names = ["Cache-Control", "Pragma", "Expires"]
        headers = self.generate_headers_with_tokens(header_names)
        content = "<html><head><META HTTP-EQUIV=\"Cache-Control\" CONTENT=\"%s\"></head><body></body></html>"
        meta_tag_content = self.generate_random_token()
        self.set_get_response("/logout-and-cache", content % meta_tag_content, headers=headers)
        self.start_server()
        self.visit_url(self.get_url("/logout-and-cache"))

        self.owtf("-g web -t grep -o Logout_and_Browser_Cache_Management")

        self.assert_that_output_contains_lines(headers.values())
        self.assert_that_output_contains("1 Unique Cache Control Meta Tags found")

    def test_Old_Backup_and_Unreferenced_Files_grep(self):
        # Looks for URLs to files
        file_path = self.get_resource_path("www/backup")
        self.set_custom_handler("/(.*)", tornado.web.StaticFileHandler, {"path": file_path})
        self.start_server()
        file_url = self.get_url("/old.bak")
        self.visit_url(file_url)

        self.owtf("-g web -t grep -o Old_Backup_and_Unreferenced_Files")

        self.assert_that_output_contains(file_url)

    def test_Reflected_Cross_Site_Scripting_grep(self):
        # Looks for some XSS protection headers
        header_names = ["X-Content-Security-Policy", "X-XSS-Protection"]
        headers = self.generate_headers_with_tokens(header_names)
        self.set_get_response("/reflected-xss", "", headers=headers)
        self.start_server()
        self.visit_url(self.get_url("/reflected-xss"))

        self.owtf("-g web -t grep -o Reflected_Cross_Site_Scripting")

        self.assert_that_output_contains_lines(headers.values())

    def test_for_CSRF_grep(self):
        # Looks for hidden input fields
        content = "<html><body><form><input type=\"hidden\" name=\"csrf_token\"></form></body></html>"
        self.set_get_response("/csrf-field", content)
        self.start_server()
        self.visit_url(self.get_url("/csrf-field"))

        self.owtf("-g web -t grep -o Testing_for_CSRF")

        self.assert_that_output_contains("1 Unique Hidden fields found")

    def test_for_SSI_Injection_grep(self):
        # Looks for SSI directives in the source code of the page
        content = "<html><body><!--#echo var=\"DATE_LOCAL\" --></body></html>" # Directive taken from the OWASP Testing Guide v3
        self.set_get_response("/ssi-in-html", content)
        self.start_server()
        self.visit_url(self.get_url("/ssi-in-html"))

        self.owtf("-g web -t grep -o Testing_for_SSI_Injection")

        self.assert_that_output_contains("1 Unique Server Side Includes found")

    def test_for_SSL_TLS_grep(self):
        # Looks for the Strict-Transport-Security header
        headers = self.generate_headers_with_tokens(["Strict-Transport-Security"])
        self.set_get_response("/ssl-tls-header", "", headers=headers)
        self.start_server()
        self.visit_url(self.get_url("/ssl-tls-header"))

        self.owtf("-g web -t grep -o Testing_for_SSL-TLS")

        self.assert_that_output_contains(headers["Strict-Transport-Security"])

    def test_Vulnerable_Remember_Password_and_Pwd_Reset_grep(self):
        # Looks for forms and password inputs

        # Repeat the transaction path to avoid more results in the plugin output
        self._prepare_test_with_login_form_in("/credentials-password")

        self.owtf("-g web -t grep -o Vulnerable_Remember_Password_and_Pwd_Reset")

        self.assert_that_output_contains("2 Unique Autocomplete fields found")

    def test_Web_Application_Fingerprint_grep(self):
        # Looks for specific headers in the HTTP transactions
        header_names = ["Server",
                        "X-Powered-By",
                        "X-AspNet-Version",
                        "X-Runtime",
                        "X-Version",
                        "MicrosoftSharePointTeamServices"]
        headers = self.generate_headers_with_tokens(header_names)
        self.set_get_response("/app-fingerprint-grep", "", headers=headers)
        self.start_server()
        self.visit_url(self.get_url("/app-fingerprint-grep"))

        self.owtf("-g web -t grep -o Web_Application_Fingerprint")

        self.assert_that_output_contains_lines(headers.values())

    def _prepare_test_with_login_form_in(self, relative_url):
        html_file = self.get_resource_path("www/login_form.html")
        self.set_get_response_from_file(relative_url, html_file)
        self.start_server()
        self.visit_url(self.get_url(relative_url))

    def _prepare_test_for_general_tool(self):
        html = self.get_resource_path("www/hello_world.html")
        self.set_get_response_from_file("/", html)
        self.start_server()

    def _prepare_test_for_HTTP_Methods_and_XST(self):
        self.set_get_response("/",
                              "",
                              headers={"Location": "/login"},
                              status_code=302)
        self.set_head_response("/", "")
        self.set_options_response("/", "", headers={"Allow": "GET, HEAD, OPTIONS"})
        self.start_server()
