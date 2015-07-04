from framework.http.wafbypasser.core.http_helper import HTTPHelper


def detect_accepted_sources(http_helper, url, data, headers, param_name,
                            param_source, param_value, method):
    requests = []
    new_url = url
    new_data = data
    new_headers = headers.copy()
    sources = ['URL', 'DATA', 'COOKIE', 'HEADER']
    for source in sources:
        new_url = url
        new_data = data
        new_headers = headers.copy()

        if source is "URL":
            new_url = HTTPHelper.add_url_param(url,
                                               param_name,
                                               param_value)
        elif source is "DATA":
            new_data = HTTPHelper.add_body_param(data,
                                                 param_name,
                                                 param_value)
        elif source is "COOKIE":
            new_headers = HTTPHelper.add_cookie_param(new_headers,
                                                      param_name,
                                                      param_value)
        elif source is "HEADER":
            new_headers = HTTPHelper.add_cookie_param(new_headers,
                                                      param_name,
                                                      param_value)

        request = http_helper.create_http_request(
            method,
            new_url,
            new_data,
            new_headers
        )
        requests.append(request)

    return requests