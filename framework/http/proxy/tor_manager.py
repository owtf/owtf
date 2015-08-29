#!/usr/bin/env python
#TOR manager module developed by Marios Kourtesis <name.surname@gmail.com>

import commands
import socket
import time
from multiprocessing import Process
from framework.dependency_management.dependency_resolver import BaseComponent
from framework.lib.general import cprint



class TOR_manager(BaseComponent):
    '''
    This class is responsible for TOR management.
    '''

    COMPONENT_NAME = "tor_manager"

    #here is done the initialization of arguments and connections
    def __init__(self, args):
        self.register_in_service_locator()
        #If the args are empty it will filled with the default values
        self.error_handler = self.get_component("error_handler")
        if args[0] == '':
            self.ip = "127.0.0.1"
        else:
            self.ip = args[0]
        if args[1] == '':
            self.port = 9050
        else:
            try:
                self.port = int(args[1])
            except ValueError:
                self.error_handler.FrameworkAbort("Invalid TOR port")
        if args[2] == '':
            self.TOR_control_port = 9051
        else:
            try:
                self.TOR_control_port = int(args[2])
            except ValueError:
                self.error_handler.FrameworkAbort("Invalid TOR Controlport")
        if args[3] == '':
            self.password = "owtf"
        else:
            self.password = args[3]
        if args[4] == '':
            self.time = 5
        else:
            try:
                self.time = int(args[4])
            except ValueError:
                self.error_handler.FrameworkAbort("Invalid TOR Time")
            if self.time < 1:   
                self.error_handler.FrameworkAbort("Invalid TOR Time")

        self.TOR_Connection = self.Open_connection()
        self.Authenticate()

    #This function is handling the authentication process to TOR control connection.
    def Authenticate(self):
        self.TOR_Connection.send('AUTHENTICATE "{0}"\r\n'.format(self.password))
        responce = self.TOR_Connection.recv(1024)
        if responce.startswith('250'):  #250 is the success responce
            cprint("Successfully Authenticated to TOR control")
        else:
            self.error_handler.FrameworkAbort("Authentication Error : " + responce)
    
    #Opens a new connection to TOR control
    def Open_connection(self):
        try:
            s = socket.socket()
            s.connect((self.ip, self.TOR_control_port))
            cprint("Connected to TOR control")
            return s
        except Exception as error:
            self.error_handler.FrameworkAbort("Can't connect to the TOR daemon : " + error.strerror)

    #Starts a new TOR_control_process which will renew the IP address.
    def Run(self):
        tor_ctrl_proc = Process(target=TOR_control_process, args=(self,))
        tor_ctrl_proc.start()
        return tor_ctrl_proc

    #checks if TOR is running
    @staticmethod
    def is_tor_running():
        output = commands.getoutput("ps -A|grep -a \" tor$\"|wc -l")
        if output == "1":
            return True
        elif output == "0":
            return False
    
    @staticmethod
    def msg_start_tor(self):
        cprint ("""Error : TOR daemon is not running
                (Tips: service tor start)""")
        
    #TOR configuration Info
    @staticmethod
    def msg_configure_tor():
        cprint("""
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
        """)
        
        
    #Sends an NEWNYM message to TOR control in order to renew the IP address
    def renew_ip(self):
        self.TOR_Connection.send("signal NEWNYM\r\n")
        responce = self.TOR_Connection.recv(1024)
        if responce.startswith('250'):
            cprint("TOR : IP renewed")
            return True
        else:
            cprint("[TOR]Warning: IP can't renewed")
            return False

#This will run in a new process in order to renew the IP address after certain time.
def TOR_control_process(self):
    while 1:
        while self.renew_ip() == True:
            time.sleep(self.time * 60)  # time converted in minutes
        else:
            time.sleep(10)  # will try again to renew IP in 10 seconds

