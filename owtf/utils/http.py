try: #PY3
    from urllib.parse import urlparse
except ImportError:  #PY2
     from urlparse import urlparse


def derive_http_method(method, data):
    """Derives the HTTP method from Data, etc

    :param method: Method to check
    :type method: `str`
    :param data: Data to check
    :type data: `str`
    :return: Method found
    :rtype: `str`
    """
    d_method = method
    # Method not provided: Determine method from params
    if d_method is None or d_method == '':
        d_method = 'GET'
        if data != '' and data is not None:
            d_method = 'POST'
    return d_method
