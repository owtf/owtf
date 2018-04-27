"""
tests.suite.categories
~~~~~~~~~~~~~~~~~~~~~~

Test categories.
"""
from tests.functional.cli.test_empty_run import OWTFCliEmptyRunTest
from tests.functional.cli.test_list_plugins import OWTFCliListPluginsTest
from tests.functional.cli.test_nowebui import OWTFCliNoWebUITest
from tests.functional.cli.test_scope import OWTFCliScopeTest
from tests.functional.cli.test_except import OWTFCliExceptTest
from tests.functional.cli.test_only import OWTFCliOnlyPluginsTest
from tests.functional.plugins.web.test_web import OWTFCliWebPluginTest
from tests.functional.plugins.web.active.test_web_active import OWTFCliWebActivePluginTest

SUITES = [
    OWTFCliEmptyRunTest,
    OWTFCliListPluginsTest,
    OWTFCliNoWebUITest,
    OWTFCliScopeTest,
    OWTFCliExceptTest,
    OWTFCliOnlyPluginsTest,
    OWTFCliWebPluginTest,
    OWTFCliWebActivePluginTest,
]
