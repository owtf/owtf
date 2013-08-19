from tests.testing_framework.base_test_cases import WebPluginTestCase
from hamcrest import *
import os
import tornado.web


class WebPluginsTests(WebPluginTestCase):

    @classmethod
    def setUpClass(cls):
        super(WebPluginsTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(WebPluginsTests, cls).tearDownClass()

    def test_Spiders_Robots_and_Crawlers(self):
        robots_path = self.get_abs_path("test_cases/resources/www")
        self.set_custom_handler("/(.*)", tornado.web.StaticFileHandler, {"path": robots_path})
        self.start_server()

        self.owtf("-g web -t semi_passive -o Spiders_Robots_and_Crawlers")

        assert_that(self.owtf_output, contains_string("/private"))
        assert_that(self.owtf_output, contains_string("/public"))
