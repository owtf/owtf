#!/usr/bin/env python

import unittest

from selenium.common.exceptions import NoSuchElementException

from owtf.lib.general import *


class URLLauncher(unittest.TestCase):
    def __init__(self, selenium, base_url, vector_file):
        self.Selenium = selenium
        self.URLList = []
        for vector in get_file_as_list(vector_file):
            self.URLList.append(base_url + vector)

    def Run(self):
        self.SetUp()
        try:
            self.TestURLs()
        except Exception as e:
            print(e)

    def SetUp(self):
        self.verificationErrors = []

    def TestURLs(self):
        for url in self.URLList:
            cprint("Launching URL: %s" % url)
            self.Selenium.Driver.get(url)

    def is_element_present(self, how, what):
        try:
            self.Selenium.Driver.find_element(by=how, value=what)
        except NoSuchElementException:
            return False
        return True

    def tearDown(self):
        self.Selenium.Driver.quit()
        self.assertEqual([], self.verificationErrors)
