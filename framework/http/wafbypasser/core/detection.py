# ****************Detection-Methods*********************
# These methods are detecting if a request is blocked by a WAF


def contains(response, args):
    """This function detects if the body of an http response contains a
    user defined string"""
    phrase = args["phrase"]
    body = response.body
    if body is None:
        if not phrase:
            detected = True
        else:
            detected = False
    else:
        if not args["case_sensitive"]:
            phrase = phrase.lower()
            body = body.lower()
        detected = phrase in body
    if args["reverse"]:
        return not detected
    return detected


# Args Example: 200-300,402,404
def resp_code_detection(response, args):
    """This function detects if the response code of an http response is a
    a user defined number or range"""
    code_range = []
    items = []
    items = args["response_codes"].split(',')
    for item in items:
        tokens = item.split('-')
        if len(tokens) == 2:
            code_range.extend(range(int(tokens[0]), int(tokens[1]) + 1))
        else:
            code_range.append(int(tokens[0]))
    detection = response.code in code_range
    if args["reverse"]:
        return not detection
    return detection


def resp_time_detection(response, args):
    """This function detects if the response of an http response is
    timed out or takes more time than the user defined"""
    time = float(args["time"])
    detected = False
    if response.request_time > time or response.code == 599:
        detected = True
    if args["reverse"]:
        return not detected
    return detected