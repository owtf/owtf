

class ExpensiveResourceProxy():
    """
        Class used to cache an object with a time-expensive initialization using
        a proxy pattern. It receives a callable that will instantiate the
        expensive object and use it when it is required.
    """

    def __init__(self, init_function):
        self.init_function = init_function
        self.instance = None

    def get_instance(self):
        if self.instance is None:
            self.instance = self.init_function()
        return self.instance
