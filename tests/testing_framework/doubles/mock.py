from collections import deque


class ExecutionOrderError(Exception):
    pass


class MissingExecutionError(Exception):
    pass


class MissingRegisteredCalls(Exception):
    pass


class OrderedExecutionMock():

    def __init__(self, target_obj):
        self.target_obj = target_obj
        self.ordering = []
        self.execution = []

    def register(self, method_name, *args):
        self.ordering.append(method_name)
        method = ReplacedMethod(self, method_name, args)
        if hasattr(self.target_obj, method_name) and isinstance(getattr(self.target_obj, method_name), MultipleCallHandler):
            call_handler = getattr(self.target_obj, method_name)
            call_handler.addMethod(method)
        else:
            call_handler = MultipleCallHandler(method)
            setattr(self.target_obj, method_name, call_handler)

    def verify_order(self):
        if len(self.ordering) > len(self.execution):
            missing_calls = self._get_missing_calls()
            raise MissingExecutionError("Missing calls: " + missing_calls + ".")
        for i, method in enumerate(self.ordering):
            if (method != self.execution[i]):
                raise ExecutionOrderError("Execution order not satisfied. Invoked: " + method + ". Expected: " + self.execution[i] + ".")

    def _get_missing_calls(self):
        return ", ".join(self.ordering[len(self.execution):])

    def register_execution(self, method_name):
        self.execution.append(method_name)


class BadArgumentException(Exception):
    pass


class MultipleCallHandler():

    def __init__(self, method):
        self.mock_methods = deque()
        self.mock_methods.append(method)
        self.method_name = method.method_name

    def __call__(self, *args):
        if len(self.mock_methods) == 0:
            raise MissingRegisteredCalls("No more calls expected for " + self.method_name)
        else:
            current_method = self.mock_methods.popleft()
            current_method(*args)

    def addMethod(self, method):
        self.mock_methods.append(method)


class ReplacedMethod():

    def __init__(self, execution_mock, method_name, args):
        self.execution_mock = execution_mock
        self.method_name = method_name
        self.args = args if len(args) > 0 else None

    def __call__(self, *args):
        if (self.args is not None):
            self._check_arguments(args)
        self.execution_mock.register_execution(self.method_name)

    def _check_arguments(self, args):
        error_message = "Arguments for method " + self.method_name + " do not match. Expected (" + ",".join(self.args) + ") but received: (" + ",".join(args) + ")."
        if len(self.args) != len(args):
            raise BadArgumentException(error_message)
        for i, arg in enumerate(self.args):
            if (arg != args[i]):
                raise BadArgumentException(error_message)


class StreamMock():

    def __init__(self):
        self.content = []

    def write(self, arg):
        self.content.append(arg)

    def flush(self):
        pass

    def get_content(self):
        return "\n".join(self.content)
