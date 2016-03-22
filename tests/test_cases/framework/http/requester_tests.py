from tests.testing_framework.base_test_cases import BaseTestCase
from hamcrest import *
from flexmock import flexmock
from framework.http.requester import Requester
import re


class RequesterTests(BaseTestCase):

    def before(self):
        self.core_mock = flexmock()
        self.core_mock.Config = flexmock()
        self.core_mock.Config.should_receive("Get").and_return("user agent")
        self.requester = Requester(self.core_mock, None)
        flexmock(self.requester)

    def test_Request_should_be_successful(self):
        url = "http://someurl"
        self.requester.should_receive("perform_request").once().ordered()
        self.requester.should_receive("set_succesful_transaction").once().ordered()
        self.requester.should_receive("log_transaction").once().ordered()
        self.core_mock.should_receive("IsInScopeURL").and_return(True).once()
        self.core_mock.Timer = flexmock()
        self.core_mock.Timer.should_receive("StartTimer").once()

        self.requester.Request(url)

    def test_StringToDict(self):
        params = "key=value"

        result = self.requester.StringToDict(params)

        assert_that(result["key"], is_("value"))

    def test_ProcessHTTPErrorCode_with_connection_refused(self):
        error = flexmock()
        error.reason = "[Errno 111]"

        error_output = self.requester.ProcessHTTPErrorCode(error, "someurl")

        assert_that(error_output, contains_string("was refused"))

    def test_ProcessHTTPErrorCode_with_unkwown_error(self):
        error = flexmock()
        error.reason = "unkwown error"

        error_output = self.requester.ProcessHTTPErrorCode(error, "someurl")

        assert_that(error_output, contains_string("unknown error"))

    def test_ProcessHTTPErrorCode_with_hostname_resolving_error(self):
        error = flexmock()
        error.reason = "[Errno -2]"
        self.core_mock.Error = flexmock()
        expected_arg = re.compile(".*cannot resolve hostname.*")
        self.core_mock.Error.should_receive("FrameworkAbort").with_args(expected_arg)

        error_output = self.requester.ProcessHTTPErrorCode(error, "someurl")

    def test_ProxyCheck_with_no_proxy_settings_is_ok(self):
        assert_that(self.requester.ProxyCheck()[0], is_(True))

    def test_ProxyCheck_with_proxy_should_be_succesful(self):
        flexmock(self.requester)
        self.requester.should_receive("is_request_possible").and_return(True).once()
        self.requester.should_receive("is_transaction_already_added").and_return(False).once()
        self.requester.should_receive("GET").once()
        self.core_mock.Config.should_receive("Get").with_args("PROXY_CHECK_URL").once()
        self.requester.Proxy = flexmock()

        assert_that(self.requester.ProxyCheck()[0], is_(True))
