from tests.testing_framework.base_test_cases import WebPluginTestCase
from hamcrest import *
import os
import tornado.web
import unittest
import cgi


class WebPluginsTests(WebPluginTestCase):

    @classmethod
    def setUpClass(cls):
        super(WebPluginsTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(WebPluginsTests, cls).tearDownClass()

    #  Semi-passive plugins  #

    def test_HTTP_Methods_and_XST_semi_passive(self):
        self.set_get_response("/",
                              "",
                              headers={"Location": "/login"},
                              status_code=302)
        self.set_head_response("/", "")
        self.set_options_response("/", "", headers={"Allow": "GET, HEAD, OPTIONS"})
        self.start_server()

        self.owtf("-g web -t semi_passive -o HTTP_Methods_and_XST")

        self.assert_that_output_contains("Allow: GET, HEAD, OPTIONS")  # curl output

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
        for line in crossdomain:
            self.assert_that_output_contains(cgi.escape(line))
        for line in clientaccesspolicy:
            self.assert_that_output_contains(cgi.escape(line))

        crossdomain.close()
        clientaccesspolicy.close()

    def test_Web_Application_Fingerprint_semi_passive(self):
        self.set_get_response("/",
                              "<html><body><h1>Hello</h1></body></html>",
                              headers={"Server": "CustomServer/1.0"})
        self.start_server()

        self.owtf("-g web -t semi_passive -o Web_Application_Fingerprint")

        self.assert_that_output_contains("CustomServer/1.0")
        self.assert_that_output_contains("HTTPServer[CustomServer/1.0]")  # Whatweb output

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

        self.assert_that_output_contains(headers[clickjacking_headers[0]])
        self.assert_that_output_contains(headers[clickjacking_headers[0]])

    def test_Cookies_attributes_grep(self):
        # Looks for transactions with cookies and finds their attributes
        cookie = "ID=" + self.generate_random_token() + ";secure;HttpOnly"
        headers = {"Set-Cookie": cookie}
        self.set_get_response("/cookies", "", headers=headers)
        self.start_server()
        self.visit_url(self.get_url("/cookies"))

        self.owtf("-g web -t grep -o Cookies_attributes")

        cookie_chunks = cookie.split(";")
        self.assert_that_output_contains(cookie_chunks[0].split("=")[1])  # ID value
        self.assert_that_output_contains(cookie_chunks[1])  # secure
        self.assert_that_output_contains(cookie_chunks[2])  # HttpOnly

    def test_CORS_grep(self):
        # Looks for some headers used for Cross-Origin resource sharing
        cors_headers = ["Access-Control-Allow-Origin",
                        "Access-Control-Allow-Credentials"]
        headers = self.generate_headers_with_tokens(cors_headers)
        self.set_get_response("/cors", "", headers=headers)
        self.start_server()
        self.visit_url(self.get_url("/cors"))

        self.owtf("-g web -t grep -o CORS")

        self.assert_that_output_contains(headers[cors_headers[0]])
        self.assert_that_output_contains(headers[cors_headers[1]])

    def test_Credentials_transport_over_an_encrypted_channel_grep(self):
        # Looks for forms with password inputs loaded through http
        self._prepare_test_with_login_form_in("/credentials")

        self.owtf("-g web -t grep -o Credentials_transport_over_an_encrypted_channel")

        self.assert_that_output_contains("Total insecure matches: 1")

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

        for value in headers.values():
            self.assert_that_output_contains(value)
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

        for value in headers.values():
            self.assert_that_output_contains(value)

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
        self._prepare_test_with_login_form_in("/credentials")

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

        for value in headers.values():
            self.assert_that_output_contains(value)

    def _prepare_test_with_login_form_in(self, relative_url):
        html_file = self.get_resource_path("www/login_form.html")
        self.set_get_response_from_file(relative_url, html_file)
        self.start_server()
        self.visit_url(self.get_url(relative_url))