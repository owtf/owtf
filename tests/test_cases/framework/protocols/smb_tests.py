from tests.testing_framework.base_test_cases import BaseTestCase
from flexmock import flexmock
from hamcrest import *
from framework.protocols.smb import SMB


class SMBTests(BaseTestCase):

    def before(self):
        self.smb = SMB(None)

    def test_Mount_should_be_succesful(self):
        password = "pass"
        options = self._get_options(password)
        self._record_interaction_with_superclass(password)

        self.smb.Mount(options, None)

        assert_that(self.smb.Mounted)

    def test_Mount_with_no_password_should_send_empty_string(self):
        empty_password = ""
        options = self._get_options(None)
        self._record_interaction_with_superclass(empty_password)

        self.smb.Mount(options, None)

        assert_that(self.smb.Mounted)

    def test_Mount_does_not_do_anything_when_already_mounted(self):
        self.smb.Mounted = True

        self.smb.Mount(None, None)

        assert_that(self.smb.Mounted)

    def test_UnMount_should_close_the_smb_connection(self):
        self._mock_shell_and_create_smb()
        self.smb.Mounted = True
        self.smb.Options = {"SMB_MOUNT_POINT": "mount/point"}
        flexmock(self.smb)
        self.smb.should_receive("Close").once()

        self.smb.UnMount(None)

        assert_that(is_not(self.smb.Mounted))

    def test_Upload_should_use_core_shell_to_transfer_the_file(self):
        self._mock_shell_and_create_smb()

        self.smb.Upload("FilePath", "MountPoint")

    def test_Download_should_use_core_shell_to_transfer_the_file(self):
        self._mock_shell_and_create_smb()

        self.smb.Download("RemoteFilePath", "TargetDir")

    def test_Transfer_should_be_used_to_upload_or_download_files(self):
        flexmock(self.smb)
        self.smb.should_receive("Download").once()
        self.smb.should_receive("Upload").once()
        self.smb.Options = {"SMB_DOWNLOAD": "file",
                            "SMB_UPLOAD": "file",
                            "SMB_MOUNT_POINT": "mount/point"}

        self.smb.Transfer()

    def test_Transfer_with_no_options_should_only_print_warning(self):
        self.smb.Options = {"SMB_DOWNLOAD": None,
                            "SMB_UPLOAD": None,
                            "SMB_MOUNT_POINT": None}

        self.init_stdout_recording()
        self.smb.Transfer()
        warning = self.get_recorded_stdout_and_close()

        assert_that(warning is not None)
        assert_that(warning, has_length(greater_than(0)))

    def _mock_shell_and_create_smb(self):
        self._mock_and_assert_shell_call()
        self.smb = SMB(self.core_mock)

    def _mock_and_assert_shell_call(self):
        self.core_mock = flexmock()
        shell = flexmock()
        shell.should_receive("shell_exec_monitor").with_args(str).once()
        self.core_mock.Shell = shell

    def _get_options(self, password):
        return {"SMB_MOUNT_POINT": "mount/point",
                "SMB_HOST": "localhost",
                "SMB_SHARE": "resource",
                "SMB_USER": "user",
                "SMB_PASS": password}

    def _record_interaction_with_superclass(self, password):
        flexmock(self.smb)
        self.smb.should_receive("Open").ordered()
        self.smb.should_receive("check_mount_point_existence").ordered()
        self.smb.should_receive("Run").ordered()
        self.smb.should_receive("Expect").with_args("Password:").ordered()
        self.smb.should_receive("Run").with_args(password).ordered()
        self.smb.should_receive("Expect").with_args("#").ordered()
