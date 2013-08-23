from tests.testing_framework.base_test_cases import BaseTestCase
from hamcrest import *
from tests.testing_framework.server import HandlerBuilder
from tornado.web import RequestHandler


class HandlerBuilderTests(BaseTestCase):

    def before(self):
        self.builder = HandlerBuilder()

    def test_that_create_method_implementation_returns_a_callable(self):
        obj = self.builder.create_method_implementation({}, "", 200)
        assert_that(callable(obj))

    def test_that_create_handler_class_returns_a_subclass_of_RequestHandler(self):
        handler_class = self.builder.create_handler_class({})
        assert_that(issubclass(handler_class, RequestHandler))

    def test_that_get_handler_returns_a_class_with_the_specified_methods(self):
        params = {"get": {"headers": {}, "content": "", "code": 200},
                  "post": {"headers": {}, "content": "", "code": 200}}

        handler_class = self.builder.get_handler(params)

        assert_that(hasattr(handler_class, "get"))
        assert_that(hasattr(handler_class, "post"))
