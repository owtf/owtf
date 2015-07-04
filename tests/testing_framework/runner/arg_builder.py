import shlex
import subprocess
import re

TEST_CASES_FOLDER = "test_cases"
PREDEFINED_OPTIONS = ["--verbose",
                      "--no-byte-compile",
                      "--with-html",
                      "--html-file=tests.log.html"]


class IllegalArgument(Exception):
    pass


class NoseArgumentBuilder():

    def __init__(self, args):
        self.args = args
        self.nose_arguments = ""

    def build(self):
        self.add_category()
        self.find_and_add_modules()
        self.process_only_option()
        self.process_all_option()
        self.add_predefined_arguments()
        return "nosetests " + self.nose_arguments

    def add_category(self):
        all_categories = ["framework", "plugin", "testing_framework"]
        if (self.args.category in all_categories):
            self.nose_arguments = TEST_CASES_FOLDER + "/" + self.args.category + "/ "

    def find_and_add_modules(self):
        if (self.args.modules is not None):
            modules = self.args.modules.split(",")
            files = []
            for module in modules:
                # Look for files containing the name of the test class, and add it to the list
                files_for_module = self.find_files_matching(module)
                files.extend(files_for_module)
            self.nose_arguments = " ".join(files)

    def process_only_option(self):
        if (self.args.only is not None):
            self.nose_arguments = self.args.only.replace(",", " ") + " "

    def process_all_option(self):
        if (self.args.all == True):
            self.nose_arguments = TEST_CASES_FOLDER + "/ "

    def add_predefined_arguments(self):
        self.nose_arguments += " ".join(PREDEFINED_OPTIONS)

    def find_files_matching(self, module_name):
        self.check_input(module_name)
        command = "grep " + module_name + " " + TEST_CASES_FOLDER +"/ -l -r"
        return subprocess.check_output(shlex.split(command), shell=False).split("\n")

    def check_input(self, input):
        """Filters the content to avoid unexpected command injection."""
        if re.match("^[a-zA-Z_]+$", input) is None:
            raise IllegalArgument("Text contain invalid characters.")
