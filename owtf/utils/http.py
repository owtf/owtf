"""
owtf.utils.http
~~~~~~~~~~~~~~~

"""
import collections
import types

try:  # PY3
    from urllib.parse import urlparse
except ImportError:  # PY2
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
    if d_method is None or d_method == "":
        d_method = "GET"
        if data != "" and data is not None:
            d_method = "POST"
    return d_method


def deep_update(source, overrides):
    """Update a nested dictionary or similar mapping.

    Modify ``source`` in place.

    :type source: collections.Mapping
    :type overrides: collections.Mapping
    :rtype: collections.Mapping
    """
    for key, value in overrides.items():
        if isinstance(value, collections.Mapping) and value:
            returned = deep_update(source.get(key, {}), value)
            source[key] = returned
        else:
            source[key] = overrides[key]
    return source


def extract_method(wrapped_method):
    """Gets original method if wrapped_method was decorated

    :rtype: any([types.FunctionType, types.MethodType])
    """
    # If method was decorated with validate, the original method
    #   is available as orig_func thanks to our container decorator
    return wrapped_method.orig_func if hasattr(wrapped_method, "orig_func") else wrapped_method


def is_method(method):
    method = extract_method(method)
    # Can be either a method or a function
    return type(method) in [types.MethodType, types.FunctionType]
