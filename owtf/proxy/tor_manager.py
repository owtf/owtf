"""
owtf.proxy.tor_manager
~~~~~~~~~~~~~~~~~~~~~~
TOR manager module developed by Marios Kourtesis <name.surname@gmail.com>
"""
import logging
import socket
import time
from multiprocessing import Process

from owtf.utils.error import abort_framework


class TOR_manager(object):

    # Initialization of arguments and connections
    def __init__(self, args):
        # If the args are empty it will filled with the default values
        if args[0] == "":
            self.ip = "127.0.0.1"
        else:
            self.ip = args[0]
        if args[1] == "":
            self.port = 9050
        else:
            try:
                self.port = int(args[1])
            except ValueError:
                abort_framework("Invalid TOR port")
        if args[2] == "":
            self.tor_control_port = 9051
        else:
            try:
                self.tor_control_port = int(args[2])
            except ValueError:
                abort_framework("Invalid TOR Controlport")
        if args[3] == "":
            self.password = "owtf"
        else:
            self.password = args[3]
        if args[4] == "":
            self.time = 5
        else:
            try:
                self.time = int(args[4])
            except ValueError:
                abort_framework("Invalid TOR Time")
            if self.time < 1:
                abort_framework("Invalid TOR Time")

        self.tor_conn = self.open_connection()
        self.authenticate()

    def authenticate(self):
        """This function is handling the authentication process to TOR control connection.

        :return:
        :rtype:
        """
        self.tor_conn.send('AUTHENTICATE "%s"\r\n' % self.password)
        response = self.tor_conn.recv(1024)
        if response.startswith("250"):  # 250 is the success response
            logging.info("Successfully Authenticated to TOR control")
        else:
            abort_framework("Authentication Error : %s" % response)

    def open_connection(self):
        """Opens a new connection to TOR control

        :return:
        :rtype:
        """
        try:
            s = socket.socket()
            s.connect((self.ip, self.tor_control_port))
            logging.info("Connected to TOR control")
            return s
        except Exception as error:
            abort_framework("Can't connect to the TOR daemon : %s" % str(error))

    def run(self):
        """Starts a new TOR_control_process which will renew the IP address.

        :return:
        :rtype:
        """
        tor_ctrl_proc = Process(target=self.tor_control_process, args=(self,))
        tor_ctrl_proc.start()
        return tor_ctrl_proc

    # Checks if TOR is running
    @staticmethod
    def is_tor_running():
        """Check if tor is running

        :return: True if running, else False
        :rtype: `bool`
        """
        output = commands.getoutput('ps -A|grep -a " tor$"|wc -l')
        if output == "1":
            return True
        elif output == "0":
            return False

    @staticmethod
    def msg_start_tor(self):
        logging.info("Error : TOR daemon is not running (Tips: service tor start)")

    # TOR configuration Info
    @staticmethod
    def msg_configure_tor():
        logging.info(
            """
        1)Open torrc file usually located at '/etc/tor/torrc'
          if you can't find torrc file visit https://www.torproject.org/docs/faq.html.en#torrc
        2)Enable the TOR control port by uncommenting(removing the hash(#) symbol)
          or adding the following line
          should look like this  "ControlPort 9051".
        3)Generate a new hashed password by running the following command
            "tor --hash-password 'your_password'
        4)Uncomment "HashedControlPassword" and add the previously generated hash
          should look like the following but with you hash
          HashedControlPassword 16:52B319480CED2E0860BAEA7565ECCF628A59FEE59B6E0592CD3F01C710

        Recommended Setting:
             ControlPort 9051
             HashedControlPassword 16:52B319480CED2E0860BAEA7565ECCF628A59FEE59B6E0592CD3F01C710
             The above hashed password is 'owtf'
        Advantages of recommended settings
           You can run owtf TOR mode without specifying the options
               ex.  ./owtf.py -o OWTF-WVS-001 http:my.website.com --tor ::::
                 which is the same with 127.0.0.1:9050:9051:owtf:5
        """
        )

    def renew_ip(self):
        """Sends an NEWNYM message to TOR control in order to renew the IP address

        :return: True if IP is renewed, else False
        :rtype: `bool`
        """
        self.tor_conn.send("signal NEWNYM\r\n")
        response = self.tor_conn.recv(1024)
        if response.startswith("250"):
            logging.info("TOR : IP renewed")
            return True
        else:
            logging.info("[TOR]Warning: IP can't renewed")
            return False

    def tor_control_process(self):
        """This will run in a new process in order to renew the IP address after certain time.

        :return: None
        :rtype: None
        """
        while True:
            while self.renew_ip() is True:
                time.sleep(self.time * 60)  # time converted in minutes
            else:
                time.sleep(10)  # will try again to renew IP in 10 seconds
