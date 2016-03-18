from owtf_testing.tests_functional.cli.test_empty_run import OWTFCliEmptyRunTest
from owtf_testing.tests_functional.cli.test_list_plugins import OWTFCliListPluginsTest
from owtf_testing.tests_functional.cli.test_nowebui import OWTFCliNoWebUITest
from owtf_testing.tests_functional.cli.test_scope import OWTFCliScopeTest
from owtf_testing.tests_functional.cli.test_simulation import OWTFCliSimulationTest
from owtf_testing.tests_functional.cli.test_except import OWTFCliExceptTest
from owtf_testing.tests_functional.cli.test_only import OWTFCliOnlyPluginsTest

from owtf_testing.tests_functional.plugins.web.test_web import OWTFCliWebPluginTest

from owtf_testing.tests_functional.plugins.web.active.test_web_active import OWTFCliWebActivePluginTest


SUITES = [
    OWTFCliEmptyRunTest,
    OWTFCliListPluginsTest,
    OWTFCliNoWebUITest,
    OWTFCliScopeTest,
    OWTFCliSimulationTest,
    OWTFCliExceptTest,
    OWTFCliOnlyPluginsTest,

    OWTFCliWebPluginTest,
    OWTFCliWebActivePluginTest
]
