from tests.testing_framework.base_test_cases import BaseTestCase
from hamcrest import *
from tests.testing_framework.utils import ExpensiveResourceProxy

EXPENSIVE_RESOURCE_STUB = "Expensive resource"


class ExpensiveResourceProxyTests(BaseTestCase):

    def test_init_function_is_called_when_invoking_get_instance(self):
        init_function = FunctionMock()
        proxy = ExpensiveResourceProxy(init_function)

        proxy.get_instance()

        assert_that(init_function.has_been_called)

    def test_init_function_is_used_for_getting_the_instance(self):
        proxy = ExpensiveResourceProxy(FunctionMock())

        instance = proxy.get_instance()

        assert_that(instance, equal_to(EXPENSIVE_RESOURCE_STUB))

    def test_result_of_init_function_is_cached_by_the_proxy(self):
        init_function = FunctionMock()
        proxy = ExpensiveResourceProxy(init_function)

        first_instance = proxy.get_instance()
        second_instance = proxy.get_instance()

        assert_that(init_function.number_of_calls, equal_to(1))
        assert_that(first_instance is second_instance)


class FunctionMock():

    def __init__(self):
        self.has_been_called = False
        self.number_of_calls = 0

    def __call__(self):
        self.has_been_called = True
        self.number_of_calls += 1
        return EXPENSIVE_RESOURCE_STUB
