from tests.testing_framework.base_test_cases import BaseTestCase
from hamcrest import *
from flexmock import flexmock
from tests.testing_framework.db.environments import DBEnvironmentBuilder
from framework.db.url_manager import URLManager


class URLManagerTests(BaseTestCase):

    def before(self):
        environment_builder = DBEnvironmentBuilder()
        environment_builder._create_core_mock()
        self.core_mock = environment_builder.core_mock
        self.url_manager = URLManager(self.core_mock)

    def test_IsFileURL(self):
        file_url = "http://test.com/file.exe"
        non_file_url = "http://test.com/"

        assert_that(self.url_manager.IsFileURL(file_url))
        assert_that(self.url_manager.IsFileURL(non_file_url), is_(False))

    def test_IsImageURL(self):
        image_url = "http://test.com/file.png"
        non_image_url = "http://test.com/"

        assert_that(self.url_manager.IsImageURL(image_url))
        assert_that(self.url_manager.IsImageURL(non_image_url), is_(False))

    def test_GetURLsToVisit_filters_image_urls(self):
        url_list = ["http://test.com/",
                    "http://test.com/one",
                    "http://test.com/two.png",
                    "http://test.com/three",
                    "http://test.com/four.jpg"]

        assert_that(self.url_manager.GetURLsToVisit(url_list), has_length(equal_to(3)))

    def test_IsURL(self):
        http = "http://test.com/"
        ftp = "ftp://test.com/"
        non_url = "test.com"

        assert_that(self.url_manager.IsURL(http))
        assert_that(self.url_manager.IsURL(ftp))
        assert_that(self.url_manager.IsURL(non_url), is_(False))

    def test_AddURLToDB_should_call_the_DB_instance_to_perform_the_work(self):
        urls = ["http://test.com/file.exe",
                "http://test.com/two.png",
                "http://notinscope.com"]
        self.core_mock.IsInScopeURL = lambda url: url != "http://notinscope.com"
        self.core_mock.DB = flexmock()
        self.core_mock.DB.DBHandler = flexmock()
        self.core_mock.DB.should_receive("Add").times(5)  # The two first URLs will be stored twice
        flexmock(self.url_manager)
        self.url_manager.should_receive("IsURLAlreadyAdded").and_return(False)

        for url in urls:
            self.url_manager.AddURL(url)
