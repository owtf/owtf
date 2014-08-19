import urlparse
from http_helper import HTTPHelper


# HPP Functions

def asp_hpp(http_helper, methods, payloads, param_name, source, url,
            headers, body=None):
    requests = []
    if "URL" in source.upper():
        for payload in payloads:
            new_url = asp_url_hpp(url, param_name, payload)
            for method in methods:
                requests.append(
                    http_helper.create_http_request(
                        method,
                        new_url,
                        body,
                        headers,
                        payload
                    )
                )
    elif "DATA" in source.upper():
        for payload in payloads:
            new_body = asp_post_hpp(body, param_name, payload)
            for method in methods:
                requests.append(
                    http_helper.create_http_request(
                        method,
                        url,
                        new_body,
                        headers,
                        payload))
    elif "COOKIE" in source.upper():
        for payload in payloads:
            new_headers = asp_cookie_hpp(headers, param_name, payload)
            for method in methods:
                requests.append(
                    http_helper.create_http_request(
                        method,
                        url,
                        body,
                        new_headers,
                        payload))
    return requests


def asp_url_hpp(url, param_name, payload):
    if urlparse.urlparse(url)[4] == '':
        sep = "?"
    else:
        sep = '&'
    for pay_token in payload.split(","):
        url += sep + param_name + "=" + pay_token
        sep = '&'
    return url


def asp_post_hpp(body, param_name, payload):
    if body is None or body == '':
        sep = ""
    else:
        sep = '&'
    for pay_token in payload.split(","):
        body += sep + param_name + "=" + pay_token
        sep = '&'
    return body


def asp_cookie_hpp(headers, param_name, payload):
    new_headers = headers.copy()
    try:
        cookie_value = new_headers.pop('Cookie')
        sep = "&"
    except KeyError:
        cookie_value = ""
        sep = ""
    for pay_token in payload.split(","):
        cookie_value += sep + param_name + "=" + pay_token
        sep = '&'
    new_headers.add("Cookie", cookie_value)
    return new_headers


def param_overwrite(http_helper, param, accepted_source, payload, url, body,
                    headers):
    requests = []
    if "URL" == accepted_source:
        new_url = HTTPHelper.add_url_param(url, param, "")
        new_body = HTTPHelper.add_body_param(body, param, payload)
        new_headers = HTTPHelper.add_cookie_param(headers, param, payload)

        requests.append(http_helper.create_http_request(
                        "GET",
                        new_url,
                        new_body,
                        headers,
                        payload))

        requests.append(http_helper.create_http_request(
                        accepted_source,
                        new_url,
                        body,
                        new_headers,
                        payload))
        #Duplicate param , first is empty and the second contains the payload
        new_url = HTTPHelper.add_url_param(new_url, param, payload)
        requests.append(http_helper.create_http_request(
                        accepted_source,
                        new_url,
                        body,
                        headers,
                        payload))
        return requests
    elif "DATA" == accepted_source:
        new_url = HTTPHelper.add_url_param(url, param, payload)
        new_body = HTTPHelper.add_body_param(body, param, "")
        new_headers = HTTPHelper.add_cookie_param(headers, param, payload)
        #Overwrite body with cookie
        requests.append(http_helper.create_http_request(
                        accepted_source,
                        url,
                        new_body,
                        new_headers,
                        payload))
        #Overwrite body with url
        requests.append(http_helper.create_http_request(
                        accepted_source,
                        new_url,
                        body,
                        headers,
                        payload))
        #Duplicate param , first is empty and the second contains the payload
        new_body = HTTPHelper.add_url_param(new_body, param, payload)
        requests.append(http_helper.create_http_request(
                        accepted_source,
                        url,
                        new_body,
                        headers,
                        payload))
        return requests

    elif "COOKIE" == accepted_source:
        new_url = HTTPHelper.add_url_param(url, param, payload)
        new_body = HTTPHelper.add_body_param(body, param, payload)
        new_headers = HTTPHelper.add_cookie_param(headers, param, "")

        requests.append(http_helper.create_http_request(
                        accepted_source,
                        new_url,
                        body,
                        new_headers,
                        payload))

        requests.append(http_helper.create_http_request(
                        accepted_source,
                        url,
                        new_body,
                        headers,
                        payload))
        #Duplicate param , first is empty and the second contains the payload
        new_headers = HTTPHelper.add_cookie_param(new_headers, param, payload)
        requests.append(http_helper.create_http_request(
                        accepted_source,
                        url,
                        body,
                        new_headers,
                        payload))
        return requests
