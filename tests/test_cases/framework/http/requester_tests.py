from tests.testing_framework.base_test_cases import BaseTestCase
from hamcrest import *
from flexmock import flexmock
from framework.http.requester import Requester


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
