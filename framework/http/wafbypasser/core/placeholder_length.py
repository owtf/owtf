import ast

from tornado.httpclient import HTTPClient, HTTPError
from framework.http.wafbypasser.core.helper import Error


def find_length(owtf, http_helper, lsig, url, method, detection_struct, ch, headers,
                body=None):
    """This function finds the length of the fuzzing placeholder"""
    size = 8192
    minv = 0
    http_client = HTTPClient()
    new_url = url
    new_body = body
    new_headers = headers
    payload = ""
    for loop in range(0, 15):  # used to avoid potential deadloops
        payload = size * ch
        if lsig in url:
            new_url = url.replace(lsig, payload)
        elif body is not None and lsig in body:
            new_body = body.replace(lsig, payload)
        elif headers is not None and lsig in str(headers):
            raw_val = str(headers)
            raw_val = raw_val.replace(lsig, payload)
            new_headers = ast.literal_eval(str(raw_val))
        else:
            Error(owtf, "Length signature not found!")


        request = http_helper.create_http_request(method,
                                                  new_url,
                                                  new_body,
                                                  new_headers)
        try:
            response = http_client.fetch(request)
        except HTTPError as e:
            if e.response:
                response = e.response

        for struct in detection_struct:
            if struct["method"](response, struct["arguments"]):
                http_client.close()
                return binary_search(
                    http_helper,
                    lsig,
                    minv,
                    size,
                    url,
                    method,
                    detection_struct,
                    ch,
                    headers,
                    body)
        minv = size
        size *= 2


def mid_value(minv, maxv):
    return int((minv + maxv) / 2)


def binary_search(http_helper, lsig, minv, maxv, url, method, detection_struct,
                  ch,
                  headers, body=None):
    mid = mid_value(minv, maxv)
    new_url = url
    new_body = body
    new_headers = headers

    if minv > maxv:
        return maxv

    http_client = HTTPClient()
    payload = ch * mid

    if lsig in url:
        new_url = url.replace(lsig, payload)  # warning urlencode and etc
    elif body is not None and lsig in body:
        new_body = body.replace(lsig, payload)
    elif headers is not None and lsig in headers:
        raw_val = str(headers)
        raw_val = raw_val.replace(lsig, payload)
        new_headers = ast.literal_eval(str(raw_val))
    request = http_helper.create_http_request(method,
                                              new_url,
                                              new_body,
                                              new_headers)
    try:
        response = http_client.fetch(request)
    except HTTPError as e:
        response = e.response

    for struct in detection_struct:
        if struct["method"](response, struct["arguments"]):
            http_client.close()
            return binary_search(http_helper,
                                 lsig,
                                 minv,
                                 mid - 1,
                                 url,
                                 method,
                                 detection_struct,
                                 ch,
                                 headers,
                                 body)
    http_client.close()
    return binary_search(http_helper,
                         lsig,
                         mid + 1,
                         maxv,
                         url,
                         method,
                         detection_struct,
                         ch,
                         headers,
                         body)