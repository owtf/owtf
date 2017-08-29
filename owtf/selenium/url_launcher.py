"""
owtf.selenium.url_launcher

URL testing machine through a Selenium driver instance
"""

import unittest

from selenium.common.exceptions import NoSuchElementException

from owtf.lib.general import *


class URLLauncher(unittest.TestCase):
    def __init__(self, selenium, base_url, vector_file):
        self.selenium = selenium
        self.url_list = []
        for vector in get_file_as_list(vector_file):
            self.url_list.append(base_url + vector)

    def run(self):
        self.set_up()
        try:
            self.test_urls()
        except Exception as e:
            print(e)

    def set_up(self):
        self.verification_errors = []

    def test_urls(self):
        for url in self.url_list:
            cprint("Launching URL: %s" % url)
            self.selenium.driver.get(url)

    def is_element_present(self, how, what):
        try:
            self.selenium.driver.find_element(by=how, value=what)
        except NoSuchElementException:
            return False
        return True

    def tear_down(self):
        self.selenium.driver.quit()
        self.assertEqual([], self.verification_errors)
