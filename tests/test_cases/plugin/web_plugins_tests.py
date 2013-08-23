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

    def test_Spiders_Robots_and_Crawlers(self):
        robots_path = self.get_abs_path("test_cases/resources/www")
        self.set_custom_handler("/(.*)", tornado.web.StaticFileHandler, {"path": robots_path})
        self.start_server()

        self.owtf("-g web -t semi_passive -o Spiders_Robots_and_Crawlers")

        self.assert_that_output_contains("/private")
        self.assert_that_output_contains("/public")

    def test_HTTP_Methods_and_XST(self):
        self.set_get_response("/",
                              "",
                              headers={"Location": "/login"},
                              status_code=302)
        self.set_head_response("/", "")
        self.set_options_response("/", "", headers={"Allow": "GET, HEAD, OPTIONS"})
        self.start_server()

        self.owtf("-g web -t semi_passive -o HTTP_Methods_and_XST")

        self.assert_that_output_contains("Allow: GET, HEAD, OPTIONS")  # curl output

    def test_for_Cross_site_flashing(self):
        files_path = self.get_abs_path("test_cases/resources/www")
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

    def test_Web_Application_Fingerprint(self):
        self.set_get_response("/",
                              "<html><body><h1>Hello</h1></body></html>",
                              headers={"Server": "CustomServer/1.0"})
        self.start_server()

        self.owtf("-g web -t semi_passive -o Web_Application_Fingerprint")

        self.assert_that_output_contains("CustomServer/1.0")
        self.assert_that_output_contains("HTTPServer[CustomServer/1.0]")  # Whatweb output

    #  Grep plugins  #

    def test_Application_Configuration_Management(self):
        content = "<html><body><!--HTML comment--><script>/*JS comment*/</script></body></html>"
        self.set_get_response("/appConfManagement", content)
        self.start_server()
        self.visit_url(self.get_url("/appConfManagement"))

        self.owtf("-g web -t grep -o Application_Configuration_Management")

        self.assert_that_output_contains("Unique HTML Comments found")
        self.assert_that_output_contains("Unique CSS/JS Comments found")

    def test_Clickjacking(self):
        clickjacking_headers = ["X-Frame-Options", "X-Content-Security-Policy"]
        headers = self.generate_headers_with_tokens(clickjacking_headers)
        self.set_get_response("/clickjacking", "", headers=headers)
        self.start_server()
        self.visit_url(self.get_url("/clickjacking"))

        self.owtf("-g web -t grep -o Clickjacking")

        self.assert_that_output_contains(headers[clickjacking_headers[0]])
        self.assert_that_output_contains(headers[clickjacking_headers[0]])

    def test_Cookies_attributes(self):
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

    def test_CORS(self):
        cors_headers = ["Access-Control-Allow-Origin",
                        "Access-Control-Allow-Credentials"]
        headers = self.generate_headers_with_tokens(cors_headers)
        self.set_get_response("/cors", "", headers=headers)
        self.start_server()
        self.visit_url(self.get_url("/cors"))

        self.owtf("-g web -t grep -o CORS")

        self.assert_that_output_contains(headers[cors_headers[0]])
        self.assert_that_output_contains(headers[cors_headers[1]])

    def test_Credentials_transport_over_an_encrypted_channel(self):
        html_file = self.get_abs_path("test_cases/resources/www/login_form.html")
        self.set_get_response_from_file("/credentials", html_file)
        self.start_server()
        self.visit_url(self.get_url("/credentials", https=False))

        self.owtf("-g web -t grep -o Credentials_transport_over_an_encrypted_channel")

        self.assert_that_output_contains("Total insecure matches: 1")
