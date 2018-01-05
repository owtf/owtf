from owtf.lib.exceptions import APIError


HTTP_METHODS = ["GET", "PUT", "POST", "PATCH", "DELETE", "HEAD", "OPTIONS"]


def api_assert(condition, *args, **kwargs):
    """Assertion to fail with if not ``condition``
    Asserts that ``condition`` is ``True``, else raises an ``APIError``
    with the provided ``args`` and ``kwargs``
    :type  condition: bool
    """
    if not condition:
        raise APIError(*args, **kwargs)
