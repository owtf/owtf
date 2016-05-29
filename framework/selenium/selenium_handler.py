#!/usr/bin/env python

from pyvirtualdisplay import Display
from selenium import webdriver

from framework.selenium import url_launcher
from framework.dependency_management.dependency_resolver import BaseComponent
from framework.lib.general import *


class Selenium(BaseComponent):

    COMPONENT_NAME = "selenium_handler"

    def __init__(self):
        self.register_in_service_locator()
        self.Init = False

    def SetDisplay(self):
        cprint("Setting Selenium's display ..")
        self.Display = Display(visible=0, size=(800, 600))
        self.Display.start()

    def SetDriver(self):
        cprint("Setting Selenium's driver ..")
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
        return url_launcher.URLLauncher(self, args['BASE_URL'], args['INPUT_FILE'])
