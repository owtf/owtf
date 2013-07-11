

class ExpensiveResourceProxy():

    def __init__(self, init_function):
        self.init_function = init_function
        self.instance = None

    def get_instance(self):
        if self.instance is None:
            self.instance = self.init_function()
        return self.instance
