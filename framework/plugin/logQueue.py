class logQueue:
    """A file-like object that writes to a queue"""
    def __init__(self, q):
        self.q = q
    def write(self, t):
        self.q.put(t)
    def flush(self):
        pass
