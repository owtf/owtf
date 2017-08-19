"""
# This module analyze and format the results
"""

import string


def analyze_responses(responses, http_helper, detection_struct):
    det_resp = []
    undet_resp = []
    det_payloads = []
    undet_payloads = []
    for response in responses:
        detected = False
        for detection in detection_struct:
            if detection["method"](response, detection["arguments"]):
                det_resp.append(response)
                detected = True
                break
        if not detected:
            undet_resp.append(response)
    print "Detected Requests"
    for resp in det_resp:
        print
        payload = http_helper.get_payload(resp)
        print_request(resp, payload)
        det_payloads.append(payload)
    print
    print "Undetected Requests"
    for resp in undet_resp:
        print
        payload = http_helper.get_payload(resp)
        print_request(resp, payload)
        undet_payloads.append(payload)
    print
    print "List of Detected Payloads"
    for payload in sorted(det_payloads):
        print payload
    print
    print "List of UnDetected Payloads"
    for payload in sorted(undet_payloads):
        print payload
    print
    print "Number 0f HTTP requests: %s" % str(len(responses))
    print "Number 0f Detected HTTP requests: %s" % str(len(det_resp))
    print "Number 0f UnDetected HTTP requests: %s" % str(len(undet_resp))
    print
    return {"detected": det_payloads, "undetected": undet_payloads}


def print_request(response, payload=None):
    print "URL: %s" % response.request.url
    print "Method: %s" % response.request.method
    if response.request.body is not None:
        print "Post Data: %s" % response.request.body
    if response.request.headers:
        print "Request Headers: %s" % format_headers(response.request.headers)
    if payload is not None:
        print "Payload: %s" % payload


def print_response(response):
    print "Code: %s" % str(response.code)
    if response.headers:
        print "Headers: %s" % format_headers(response.headers)
    body = response.body
    if len(body) > 140:
        print "Body (140 chars): %s ... %s" % (body[:70], body[-70:])
    else:
        print "Body: %s" % body


def format_headers(headers):
    formatted_headers = ""
    for header_name, header_value in headers.iteritems():
        formatted_headers += "%s: %s, " % (header_name, header_value)
    if formatted_headers is "":
        return format_headers
    return formatted_headers[:-2]


def analyze_chars(responses, http_helper, detection_struct):
    problematic_chars = ["\n", "\r", "\t", chr(11), chr(12)]
    det_resp = []
    undet_resp = []
    det_payloads = []
    undet_payloads = []
    for response in responses:
        detected = False
        for detection in detection_struct:
            if detection["method"](response, detection["arguments"]):
                det_resp.append(response)
                detected = True
                break
        if not detected:
            undet_resp.append(response)
    for resp in det_resp:
        payload = http_helper.get_payload(resp)
        det_payloads.append(payload)
    for resp in undet_resp:
        payload = http_helper.get_payload(resp)
        undet_payloads.append(payload)
    print "List of Detected Characters"
    counter = 0
    for payload in sorted(det_payloads):
        if payload in string.printable and payload not in problematic_chars:
            print "Char: %s ascii(%s)" % (payload, str(ord(payload)))
        else:
            print "Special char ascii(%s)" % str(ord(payload))
        counter += 1
        if counter % 4 == 0:
            print "\t"
    print
    print "List of UnDetected Characters"
    counter = 0
    for payload in sorted(undet_payloads):
        if payload in string.printable and payload not in problematic_chars:
            print "Char: %s ascii(%s)" % (payload, str(ord(payload)))
        else:
            print "Special char ascii(%s)" % str(ord(payload))
        counter += 1
        if counter % 4 == 0:
            print "\t"
    print
    print "Number 0f HTTP requests: %s" % str(len(responses))
    print "Number 0f Detected HTTP requests: %s" % str(len(det_resp))
    print "Number 0f UnDetected HTTP requests: %s" % str(len(undet_resp))
    print
    return {"detected": det_payloads, "undetected": undet_payloads}


def analyze_encoded_chars(responses, http_helper, detection_struct):
    det_resp = []
    undet_resp = []
    det_payloads = []
    undet_payloads = []
    for response in responses:
        detected = False
        for detection in detection_struct:
            if detection["method"](response, detection["arguments"]):
                det_resp.append(response)
                detected = True
                break
        if not detected:
            undet_resp.append(response)
    for resp in det_resp:
        payload = http_helper.get_payload(resp)
        det_payloads.append(payload)
    for resp in undet_resp:
        payload = http_helper.get_payload(resp)
        undet_payloads.append(payload)
    print "List of Detected Characters"
    counter = 0
    for payload in sorted(det_payloads):
        print "URL encoded char: %s" % payload,
        counter += 1
        if counter % 4 == 0:
            print "\t"
    print
    print "List of UnDetected Characters"
    counter = 0
    for payload in sorted(undet_payloads):
        print "Char: %s" % payload,
        counter += 1
        if counter % 4 == 0:
            print "\t"
    print
    print "Number 0f HTTP requests: %s" % str(len(responses))
    print "Number 0f Detected HTTP requests: %s" % str(len(det_resp))
    print "Number 0f UnDetected HTTP requests: %s" % str(len(undet_resp))
    print
    return {"detected": det_payloads, "undetected": undet_payloads}


def analyze_accepted_sources(responses, detection_struct):
    det_resp = []
    undet_resp = []
    for response in responses:
        detected = False
        for detection in detection_struct:
            if detection["method"](response, detection["arguments"]):
                det_resp.append(response)
                detected = True
                break
        if not detected:
            undet_resp.append(response)

    print "Sources with matched detection criteria: "
    print
    for resp in det_resp:
        print "[->]Request"
        print_request(resp)
        print "[<-]Response: "
        print_response(resp)
        print ""
