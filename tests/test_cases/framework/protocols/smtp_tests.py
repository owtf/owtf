from tests.testing_framework.base_test_cases import BaseTestCase
from hamcrest import *
from flexmock import flexmock
from framework.protocols.smtp import SMTP


class SMTPTests(BaseTestCase):

    def setUp(self):
        self.core_mock = flexmock()

    def test_Connect_if_TLS_is_not_enabled_the_execution_should_continue(self):
        smtp, connection_mock = self._mock_smtp_connection()
        connection_mock.should_receive("starttls").and_raise(Exception).once()

        mailserver_connection = smtp.Connect(self._get_connection_options())

        assert_that(mailserver_connection is not None)

    def test_Send_message_should_succeed(self):
        smtp, connection_mock = self._mock_smtp_connection()
        self._mock_BuildTargetList(smtp)
        connection_mock.should_receive("sendmail").once()

        succeeded = smtp.Send(self._get_connection_options())

        assert_that(succeeded, is_(True))

    def test_Send_message_with_unexpected_exception_should_log_the_delivery_error(self):
        self._mock_error_handler_logging_in_core_instance()
        smtp, connection_mock = self._mock_smtp_connection()
        self._mock_BuildTargetList(smtp)
        connection_mock.should_receive("sendmail").and_raise(Exception)

        succeeded = smtp.Send(self._get_connection_options())

        assert_that(succeeded, is_(False))

    def test_BuildMessage_creates_a_valid_message(self):
        smtp = self._create_smtp_instance_with_core_mock()
        message_options = {"EMAIL_BODY": "body...",
                           "EMAIL_FROM": "sender",
                           "EMAIL_TARGET": "host",
                           "EMAIL_SUBJECT": "subject..."}
        message = smtp.BuildMessage(message_options, "host").as_string()

        assert_that(message, contains_string("From: sender"))
        assert_that(message, contains_string("To: host"))
        assert_that(message, contains_string("Subject: subject..."))
        assert_that(message, contains_string("body..."))
        assert_that(message, contains_string("Content-Type"))
        assert_that(message, contains_string("MIME-Version"))

    def _mock_smtp_connection(self):
        options = self._get_connection_options()
        connection_mock = self._create_smtp_connection_mock(options)
        smtp_instance = self._create_smtp_instance_with_core_mock()
        flexmock(smtp_instance)
        smtp_instance.should_receive("create_connection_with_mail_server").and_return(connection_mock)
        return smtp_instance, connection_mock

    def _create_smtp_connection_mock(self, options):
        mock = flexmock()
        mock.should_receive("ehlo").once()
        mock.should_receive("starttls")
        mock.should_receive("login").with_args(options['SMTP_LOGIN'], options['SMTP_PASS']).once()
        return mock

    def _create_smtp_instance_with_core_mock(self):
        return SMTP(self.core_mock)

    def _get_connection_options(self):
        return {'SMTP_LOGIN': "user",
                'SMTP_PASS': "pass",
                'SMTP_HOST': "hostname",
                'SMTP_PORT': 25}

    def _mock_BuildTargetList(self, smtp):
        flexmock(smtp)
        smtp.should_receive("BuildTargetList").and_return(["target"])

    def _mock_error_handler_logging_in_core_instance(self):
        error_handler_mock = flexmock()
        error_handler_mock.should_receive("Add").with_args(str).once()
        self.core_mock.Error = error_handler_mock
