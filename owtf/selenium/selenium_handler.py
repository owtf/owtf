"""
owtf.selenium.selenium_handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Launch and browse URLs using Selenium
"""

from pyvirtualdisplay import Display
from selenium import webdriver

from owtf.selenium import url_launcher
from owtf.dependency_management.dependency_resolver import BaseComponent
from owtf.dependency_management.interfaces import AbstractInterface
from owtf.lib.general import *


class Selenium(BaseComponent, AbstractInterface):

    COMPONENT_NAME = "selenium_handler"

    def __init__(self):
        self.register_in_service_locator()
        self.init = False

    def set_display(self):
        """Sets the display element for Selenium

        :return: None
        :rtype: None
        """
        cprint("Setting Selenium's display ..")
        self.display = Display(visible=0, size=(800, 600))
        self.display.start()

    def set_driver(self):
        """Loads up the Firefox driver

        :return: None
        :rtype: None
        """
        cprint("Setting Selenium's driver ..")
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(30)

    def init_selenium(self):
        """Set up Selenium instance

        :return: None
        :rtype: None
        """
        if not self.init:  # Perform this expensive operation only once.
            self.init = True
            cprint("Initialising Selenium please wait ..")
            self.set_display()
            try:
                self.set_driver()
            except Exception as e:
                print(e)

    def create_url_launcher(self, args):
        """Init Selenium and URL launcher

        :param args: User supplied args
        :type args: `dict`
        :return: None
        :rtype: None
        """
        self.init_selenium()
        return url_launcher.URLLauncher(self, args['BASE_URL'], args['INPUT_FILE'])
