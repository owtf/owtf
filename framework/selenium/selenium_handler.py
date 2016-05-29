#!/usr/bin/env python
"""
The random module allows the rest of the framework to have access to random
functionality.
"""
from framework.dependency_management.dependency_resolver import BaseComponent

from framework.lib.general import *


class Selenium(BaseComponent):

    COMPONENT_NAME = "selenium_handler"

    def __init__(self):
        self.register_in_service_locator()
        self.Init = False

    def SetDisplay(self):
        cprint("Setting Selenium's display ..")
        from pyvirtualdisplay import Display
        self.Display = Display(visible=0, size=(800, 600))
        self.Display.start()

    def SetDriver(self):
        cprint("Setting Selenium's driver ..")
        from selenium import webdriver
        self.Driver = webdriver.Firefox()
        self.Driver.implicitly_wait(30)

    def InitSelenium(self):
        if not self.Init:  # Perform this expensive operation only once.
            self.Init = True
            cprint("Initialising Selenium please wait ..")
            self.SetDisplay()
            self.SetDriver()

    def CreateURLLauncher(self, args):
        self.InitSelenium()
        from framework.selenium import url_launcher
        return url_launcher.URLLauncher(
            self,
            args['BASE_URL'],
            args['INPUT_FILE'])
