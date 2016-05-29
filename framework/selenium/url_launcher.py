#!/usr/bin/env python
"""
The random module allows the rest of the framework to have access to random
functionality.
"""

import unittest

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from framework.lib.general import *


class URLLauncher(unittest.TestCase):
    def __init__(self, selenium, base_url, vector_file):
        self.Selenium = selenium
        self.URLList = []
        for vector in GetFileAsList(vector_file):
            self.URLList.append(base_url + vector)

    def Run(self):
        self.SetUp()
        self.TestURLs()

    def SetUp(self):
        self.verificationErrors = []

    def TestURLs(self):
        for url in self.URLList:
            cprint("Launching URL: " + url)
            self.Selenium.Driver.get(url)

    def is_element_present(self, how, what):
        try:
            self.Selenium.Driver.find_element(by=how, value=what)
        except NoSuchElementException:
            return False
        return True

    def is_element_present(self, how, what):
        try:
            self.Selenium.Driver.find_element(by=how, value=what)
        except NoSuchElementException:
            return False
        return True

    def tearDown(self):
        self.Selenium.Driver.quit()
        self.assertEqual([], self.verificationErrors)
