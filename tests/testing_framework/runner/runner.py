from coverage import coverage
from os import path
import nose
import shlex


class Runner():

    def __init__(self, args):
        self.args = args

    def run_nose_with_coverage(self):
        framework_path = path.abspath('..')
        cov = coverage(source=[path.join(framework_path, "framework"),
                               path.join(framework_path, "tests/testing_framework")])
        cov.start()
        self.run_nose()
        cov.stop()
        print "Generating coverage reports..."
        cov.html_report(directory="cover")

    def run_nose(self):
        nose.run(argv=shlex.split(self.args))
