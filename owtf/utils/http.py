try: #PY3
    from urllib.parse import urlparse
except ImportError:  #PY2
     from urlparse import urlparse

from owtf.managers.target import TARGET_CONFIG
from owtf.lib.exceptions import UnresolvableTargetException
from owtf.utils.ip import get_ip_from_hostname, get_ips_from_hostname


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


def derive_config_from_url(target_url):
    """Automatically find target information based on target name.

    .note::
        If target does not start with 'http' or 'https', then it is considered as a network target.

    :param target_URL: Target url supplied
    :type target_URL: `str`
    :return: Target config dictionary
    :rtype: `dict`
    """
    target_config = dict(TARGET_CONFIG)
    target_config['target_url'] = target_url
    try:
        parsed_url = urlparse(target_url)
        if not parsed_url.hostname and not parsed_url.path:  # No hostname and no path, urlparse failed.
            raise ValueError
    except ValueError:  # Occurs sometimes when parsing invalid IPv6 host for instance
        raise UnresolvableTargetException("Invalid hostname '{}'".format(str(target_url)))

    host = parsed_url.hostname
    if not host:  # Happens when target is an IP (e.g. 127.0.0.1)
        host = parsed_url.path  # Use the path as host (e.g. 127.0.0.1 => host = '' and path = '127.0.0.1')
        host_path = host
    else:
        host_path = parsed_url.hostname + parsed_url.path

    url_scheme = parsed_url.scheme
    protocol = parsed_url.scheme
    if parsed_url.port is None:  # Port is blank: Derive from scheme (default port set to 80).
        try:
            host, port = host.rsplit(':')
        except ValueError:  # Raised when target doesn't contain the port (e.g. google.fr)
            port = '80'
            if 'https' == url_scheme:
                port = '443'
    else:  # Port found by urlparse.
        port = str(parsed_url.port)

    # Needed for google resource search.
    target_config['host_path'] = host_path
    # Some tools need this!
    target_config['url_scheme'] = url_scheme
    # Some tools need this!
    target_config['port_number'] = port
    # Set the top URL.
    target_config['host_name'] = host

    host_ip = get_ip_from_hostname(host)
    host_ips = get_ips_from_hostname(host)
    target_config['host_ip'] = host_ip
    target_config['alternative_ips'] = host_ips

    ip_url = target_config['target_url'].replace(host, host_ip)
    target_config['ip_url'] = ip_url
    target_config['top_domain'] = target_config['host_name']

    hostname_chunks = target_config['host_name'].split('.')
    if target_config['target_url'].startswith(('http', 'https')):  # target considered as hostname (web plugins)
        if not target_config['host_name'] in target_config['alternative_ips']:
            target_config['top_domain'] = '.'.join(hostname_chunks[1:])
        # Set the top URL (get "example.com" from "www.example.com").
        target_config['top_url'] = "{0}://{1}:{2}".format(protocol, host, port)
    else:  # target considered as IP (net plugins)
        target_config['top_domain'] = ''
        target_config['top_url'] = ''
    return target_config
