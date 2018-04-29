"""
owtf.api.utils
~~~~~~~~~~~~~~

"""
from tornado.routing import Matcher
from tornado.web import RequestHandler


class VersionMatches(Matcher):
    """Matches path by `version` regex."""

    def __init__(self, api_version):
        self.api_version = api_version

    def match(self, request):
        if self.api_version in request.path:
            return {}

        header_version = request.headers.get("X-API-VERSION", None)
        if "v{}".format(header_version) in request.path:
            return {}

        return None


def _filter_headers(header_str, simple_headers):
    header_str = header_str.lower().replace(" ", "").replace("\t", "")
    if not header_str:
        return set()

    header_set = set(value for value in header_str.split(","))
    header_set.difference_update(simple_headers)
    header_set.difference_update("")
    return header_set
