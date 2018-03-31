"""
owtf.api.utils
~~~~~~~~~~~~~~

"""
from tornado.routing import Matcher


class VersionMatches(Matcher):
    """Matches path by `version` regex."""

    def __init__(self, api_version):
        self.api_version = api_version

    def match(self, request):
        if self.api_version in request.path:
            return {}

        header_version = request.headers.get('X-API-VERSION', None)
        if "v{}".format(header_version) in request.path:
            return {}

        return None
