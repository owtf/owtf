from tests.tests_functional.cli.test_empty_run import OWTFCliEmptyRunTest
from tests.tests_functional.cli.test_list_plugins import OWTFCliListPluginsTest
from tests.tests_functional.cli.test_nowebui import OWTFCliNoWebUITest
from tests.tests_functional.cli.test_scope import OWTFCliScopeTest
from tests.tests_functional.cli.test_simulation import OWTFCliSimulationTest
from tests.tests_functional.cli.test_except import OWTFCliExceptTest
from tests.tests_functional.cli.test_only import OWTFCliOnlyPluginsTest

from tests.tests_functional.plugins.web.test_web import OWTFCliWebPluginTest

from tests.tests_functional.plugins.web.active.test_web_active import OWTFCliWebActivePluginTest


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
