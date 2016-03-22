

class FileMock():
    """
    This class simulates a file object, in order to be sure about the content
    of the file, and speed up the execution of tests, avoiding the access to
    the filesystem.
    """

    def __init__(self, lines):
        self.lines = lines
        self.max = len(lines) - 1
        self.iterator_counter = 0

    def __iter__(self):
        # A file object has to be iterable
        return self

    def next(self):
        # Iterable implementation
        if self.iterator_counter > self.max:
            self.iterator_counter = 0
            raise StopIteration
        else:
            line = self.lines[self.iterator_counter]
            self.iterator_counter += 1
            return line

    def __next__(self):  # For python 3.x compatibility
        self.next()

    def read(self):
        return "".join(self.lines)

    def close(self):
        pass
