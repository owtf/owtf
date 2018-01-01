import os

from owtf.managers import target


class OutputCleaner():
    """General functions which process output"""
    @staticmethod
    def anonymise_command(command):
        """
        Anonymize the target IP and host name

        :param command: command to anonymize
        :type command: `str`
        :return: sanitized command
        :rtype: `str`
        """
        command = command.decode('utf-8', 'ignore')
        # Host name setting value for all targets in scope.
        for host in target.get_all('HOST_NAME'):
            if host:  # Value is not blank
                command = command.replace(host, 'some.target.com')
        for ip in target.get_all('HOST_IP'):
            if ip:
                command = command.replace(ip, 'xxx.xxx.xxx.xxx')
        return command


def get_command(argv):
    """Format command to remove directory and space-separated arguments.

    :params list argv: Arguments for the CLI.

    :return: Arguments without directory and space-separated arguments.
    :rtype: list

    """
    return " ".join(argv).replace(argv[0], os.path.basename(argv[0]))
