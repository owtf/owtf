from tests.testing_framework.base_test_cases import BaseTestCase
from tests.testing_framework.doubles.mock import OrderedExecutionMock,\
    ExecutionOrderError, MissingExecutionError, MissingRegisteredCalls,\
    BadArgumentException


class ClassToTest():

    def methodA(self):
        pass

    def methodB(self):
        pass

    def methodC(self, *args):
        pass

class OrderedExecutionMockTests(BaseTestCase):

    def before(self):
        self.class_to_test = ClassToTest()

    def test_ordered_execution_should_not_raise_any_exception(self):
        order_register = OrderedExecutionMock(self.class_to_test)
        order_register.register("methodA")
        order_register.register("methodB")

        self.class_to_test.methodA()
        self.class_to_test.methodB()

        order_register.verify_order()

    def test_ordered_execution_should_raise_an_exception(self):
        order_register = OrderedExecutionMock(self.class_to_test)
        order_register.register("methodA")
        order_register.register("methodB")

        self.class_to_test.methodB()
        self.class_to_test.methodA()

        try:
            order_register.verify_order()
            self.fail("Exception expected!")
        except ExecutionOrderError:
            pass  # Test Success

    def test_ordered_execution_with_missing_method_call(self):
        order_register = OrderedExecutionMock(self.class_to_test)
        order_register.register("methodA")
        order_register.register("methodB")

        self.class_to_test.methodA()

        try:
            order_register.verify_order()
            self.fail("Exception expected!")
        except MissingExecutionError:
            pass  # Test Success

    def test_ordered_execution_with_too_many_executions(self):
        order_register = OrderedExecutionMock(self.class_to_test)
        order_register.register("methodA")
        order_register.register("methodB")

        try:
            self.class_to_test.methodA()
            self.class_to_test.methodA()
            self.fail("Exception expected!")
        except MissingRegisteredCalls:
            pass  # Test Success

    def test_ordered_execution_repeating_method_calls(self):
        order_register = OrderedExecutionMock(self.class_to_test)
        order_register.register("methodA")
        order_register.register("methodB")
        order_register.register("methodA")
        order_register.register("methodB")

        self.class_to_test.methodA()
        self.class_to_test.methodB()
        self.class_to_test.methodA()
        self.class_to_test.methodB()

        order_register.verify_order()

    def test_adding_arguments_to_method_registering(self):
        order_register = OrderedExecutionMock(self.class_to_test)
        order_register.register("methodC", "arg1", "arg2")

        self.class_to_test.methodC("arg1", "arg2")

        order_register.verify_order()

    def test_wrong_method_arguments_should_raise_an_exception(self):
        order_register = OrderedExecutionMock(self.class_to_test)
        order_register.register("methodC", "arg1", "arg2")

        try:
            self.class_to_test.methodC("bad_arg1", "bad_arg2")
        except BadArgumentException:
            pass  # Test success

    def test_adding_method_arguments_to_multiple_calls_of_the_same_method(self):
        order_register = OrderedExecutionMock(self.class_to_test)
        order_register.register("methodC", "arg1", "arg2")
        order_register.register("methodC", "arg3", "arg4")

        self.class_to_test.methodC("arg1", "arg2")
        self.class_to_test.methodC("arg3", "arg4")

        order_register.verify_order()
