import os
import tempfile
import unittest
from types import SimpleNamespace

from owtf.proxy.interceptor_manager import InterceptorManager


class TestInterceptorManagerResponseChain(unittest.TestCase):
    """InterceptorManager.add_interceptor() only ever appended to
    request_interceptors; response_interceptors was sorted but never
    populated, so intercept_response() was a permanent no-op despite every
    BaseInterceptor subclass implementing modify_response().
    """

    def setUp(self):
        # Point at a throwaway, guaranteed-nonexistent config path so no
        # real /tmp/owtf/interceptor_config.json state leaks into the test.
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.remove(path)
        self.manager = InterceptorManager(config_file=path)

    def test_default_interceptors_are_registered_on_both_chains(self):
        request_names = sorted(i.name for i in self.manager.request_interceptors)
        response_names = sorted(i.name for i in self.manager.response_interceptors)
        self.assertEqual(request_names, response_names)
        self.assertGreater(len(self.manager.response_interceptors), 0)

    def test_remove_interceptor_removes_from_both_chains(self):
        target_name = self.manager.request_interceptors[0].name

        self.manager.remove_interceptor(target_name)

        self.assertNotIn(target_name, [i.name for i in self.manager.request_interceptors])
        self.assertNotIn(target_name, [i.name for i in self.manager.response_interceptors])

    def test_default_header_modifier_now_actually_applies_to_responses(self):
        response = SimpleNamespace(headers={})

        modified = self.manager.intercept_response(response)

        self.assertEqual(modified.headers.get("X-Intercepted"), "true")
        self.assertEqual(modified.headers.get("X-OWTF-Proxy"), "1.0")

    def test_body_interceptors_are_noop_on_bytes_body_response(self):
        # A real Tornado HTTPResponse body is bytes; on the response path the
        # default BodyModifier/URLRewriter must not raise or corrupt it (they
        # early-return on empty/non-str bodies with default empty patterns).
        # This guards against the newly-live response chain touching the body.
        original = b"<html><body>ok</body></html>"
        response = SimpleNamespace(headers={"Content-Type": "text/html"}, body=original)

        modified = self.manager.intercept_response(response)

        self.assertEqual(modified.body, original)


if __name__ == "__main__":
    unittest.main()
