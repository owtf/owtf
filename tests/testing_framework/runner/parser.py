import argparse

TEST_CASES_FOLDER = "test_cases"


class ArgumentParser():

    def __init__(self):
        self.parser = self.create_parser()

    def create_parser(self):
        """Uses argparse to create the parser for the run_tests.py script."""
        parser = argparse.ArgumentParser(description="OWTF Testing framework Command Line Tool")
        parser.add_argument("category", nargs="?", help="Category of the tests to run. The possible values are: plugin, framework and testing_framework")
        parser.add_argument("-a", "--all", action="store_true", default=False, dest="all", help="This flag tells the framework to run all the tests.")
        parser.add_argument("-m", "--modules", dest="modules", metavar="module1,module2...", help="Comma separated list of test classes to run (the name of the class has to be in CamelCase).")
        parser.add_argument("-o", "--only", dest="only", metavar="file1.py,file2.py", help="Comma separated list of files containing tests.")
        parser.add_argument("-c", "--with-coverage", dest="coverage", action="store_true", default=None, help="Tell the runner to perform test coverage analysis. Only compatible with the --all option.")
        return parser

    def parse_arguments(self, arguments):
        self.parsed_arguments = self.parser.parse_args(arguments)
        validArguments, message = self.arguments_are_valid()
        if (validArguments):
            return self.parsed_arguments
        else:
            print "Arguments are not valid: " + message
            self.print_usage()
            return None

    def arguments_are_valid(self):
        validArguments, message = self.validate_combinations()
        return validArguments, message

    def validate_combinations(self):
        """Validates if some arguments provided are incompatible"""
        validArguments, message = True, ""
        if (self.has_category()):
            if (self.all_modules() and self.has_module_restriction()):
                validArguments = False
                message = "--all option is not compatible with -m option."
            elif (self.has_only_restriction()):
                validArguments = False
                message = "Category is not compatible with -o option."
        elif (self.has_only_restriction() and (self.all_modules() or self.has_module_restriction())):
            validArguments = False
            message = "-o is not compatible with any other option."
        elif (self.all_tests() and (self.has_only_restriction() or self.has_module_restriction())):
            validArguments = False
            message = "when running all tests is not possible to apply restrictions."
        return validArguments, message

    def has_category(self):
        return self.parsed_arguments.category is not None

    def has_only_restriction(self):
        return self.parsed_arguments.only is not None

    def has_module_restriction(self):
        return self.parsed_arguments.modules is not None

    def all_modules(self):
        return self.parsed_arguments.all

    def all_tests(self):
        return self.parsed_arguments.category == "all"

    def print_usage(self):
        self.parser.print_usage()