import tornado.web
import json

class APIRequestHandler(tornado.web.RequestHandler):
    def write(self, chunk):
        if isinstance(chunk, list):
            super(APIRequestHandler, self).write(json.dumps(chunk))
            self.set_header("Content-Type", "application/json; charset=UTF-8")
        else:
            super(APIRequestHandler, self).write(chunk)
