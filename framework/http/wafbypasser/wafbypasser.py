#!/bin/python
from tornado.httputil import HTTPHeaders
from tornado.httpclient import HTTPRequest
from framework.http.wafbypasser.core.hpp_lib import asp_hpp, param_overwrite
from framework.http.wafbypasser.core.placeholder_length import find_length
from framework.http.wafbypasser.core.detection import *
from framework.http.wafbypasser.core.argument_parser import get_args
from framework.http.wafbypasser.core.fuzzer import Fuzzer
from framework.http.wafbypasser.core.helper import load_payload_file, Error
from framework.http.wafbypasser.core.http_helper import HTTPHelper
from framework.http.wafbypasser.core.param_source_detector import detect_accepted_sources
from framework.http.wafbypasser.core.response_analyzer import analyze_responses, print_request, \
    print_response, analyze_chars, analyze_encoded_chars, \
    analyze_accepted_sources
from framework.http.wafbypasser.core.placeholder_manager import PlaceholderManager
from framework.http.wafbypasser.core.obfuscation_lib import unicode_urlencode, urlencode, \
    transformations_info
import string


class WAFBypasser:

    def fuzz(self, args, requests):
        if args["follow_cookies"] or args["delay"]:
            delay = args["delay"] or 0
            follow_cookies = args["follow_cookies"] or False
            print "Synchronous Fuzzing: Started"
            responses = self.fuzzer.sync_fuzz(requests, delay, follow_cookies)
        else:
            print "Requests number: " + str(len(requests))
            print "Asynchronous Fuzzing: Started"
            responses = self.fuzzer.async_fuzz(requests)
        print "Fuzzing: Completed"
        return responses

    def is_detection_set(self, args):
        det_functions = ["contains", "resp_code_det", "response_time"]
        args_set = False
        for name in det_functions:
            if args[name] is not None:
                return
        Error(self.owtf, "You need to specify at least one Detection Function.")

    def require(self, args, params):
        param_missing = False
        for param in params:
            if args[param] is None:
                param_missing = True
                print "Specify: --" + param
        if param_missing:
            Error(self.owtf, "Missing Parameter(s).")

    def __init__(self, owtf):
        self.ua = "Mozilla/5.0 (X11; Linux i686; rv:6.0) Gecko/20100101 /" \
                  "Firefox/15.0"
        self.init_request = HTTPRequest("",
                                        auth_username=None,
                                        auth_password=None,
                                        follow_redirects=True,
                                        max_redirects=10,
                                        allow_nonstandard_methods=True,
                                        headers=None,
                                        proxy_host=None,
                                        proxy_port=None,
                                        proxy_username=None,
                                        proxy_password=None,
                                        user_agent=self.ua,
                                        request_timeout=40.0)
        self.sig = "@@@"
        self.length_signature = self.sig + "length" + self.sig
        self.fsig = self.sig + "fuzzhere" + self.sig  # fuzzing signature
        # Template signature regular expression
        self.template_signature_re = self.sig + "[^" + self.sig + "]+"
        self.template_signature_re += self.sig
        self.detection_struct = []
        self.pm = None  # PlaceholderManager
        self.http_helper = None
        self.fuzzer = None
        self.owtf = owtf

    def init_methods(self, args):
        methods = args["methods"] or []
        # Setting Methods
        if methods:
            if self.sig + "all" + self.sig in methods:
                methods.remove(self.sig + "all" + self.sig)
                methods.extend(
                    load_payload_file("./payloads/HTTP/methods.txt"))
                methods = list(set(methods))  # Removing doublesk
        else:
            if args["data"] is None:
                methods.append("GET")  # Autodetect Method
            else:
                methods.append("POST")  # Autodetect Method
        return methods

    def init_headers(self, args):
        headers = HTTPHeaders()
        if args["headers"]:
            for header in args["headers"]:
                values = header.split(':', 1)
                if len(values) == 2:
                    headers.add(*values)
                else:  # values == 1
                    headers.add(values[0], "")
        # Setting Cookies
        if args["cookie"]:
            headers.add("Cookie", args["cookie"])
        return headers

    def init_detection_struct(self, args):
        if args["contains"]:
            detection_args = {}
            detection_args["phrase"] = args["contains"][0]  # detection string
            detection_args["case_sensitive"] = "cs" in args["contains"][1:]
            detection_args["reverse"] = False
            if args["reverse"]:
                detection_args["reverse"] = True
            self.detection_struct.append({"method": contains,
                                          "arguments": detection_args,
                                          "info": "Contains"})
        if args["resp_code_det"]:
            detection_args = {}
            detection_args["response_codes"] = args["resp_code_det"][0]
            detection_args["reverse"] = False
            if args["reverse"]:
                detection_args["reverse"] = True
            self.detection_struct.append({"method": resp_code_detection,
                                          "arguments": detection_args,
                                          "info": "Response code detection"})
        if args["response_time"]:
            detection_args = {}
            detection_args["time"] = args["response_time"][0]
            detection_args["reverse"] = False
            if args["reverse"]:
                detection_args["reverse"] = True
            self.detection_struct.append({"method": resp_time_detection,
                                          "arguments": detection_args,
                                          "info": "Response time detection"})

    def start(self, args):
        # Initializations
        self.sig = args["fuzzing_signature"] or self.sig
        self.pm = PlaceholderManager(self.sig)
        target = args["target"]
        methods = self.init_methods(args)
        headers = self.init_headers(args)
        data = args["data"] or ""
        self.init_detection_struct(args)
        self.init_request.headers = headers
        self.http_helper = HTTPHelper(self.init_request)
        self.fuzzer = Fuzzer(self.http_helper)

        # Finding the length of a placeholder
        if args["mode"] == "length":
            self.require(args, ["accepted_value"])
            self.is_detection_set(args)
            if len(methods) > 1:
                Error(self.owtf, "Only you need to specify only one Method")
            print "Scanning mode: Length Detection"
            ch = args["accepted_value"][0]
            length = find_length(self.owtf,
                                 self.http_helper,
                                 self.length_signature,
                                 target,
                                 methods[0],
                                 self.detection_struct,
                                 ch,
                                 headers,
                                 data)
            print "Placeholder Allowed Length = " + str(length)
        # Detecting Allowed Sources
        elif args["mode"] == "detect_accepted_sources":
            self.is_detection_set(args)
            self.require(args, ["methods",
                                "param_name",
                                "accepted_value",
                                "param_source"])

            if len(methods) > 1:
                Error(self.owtf, "Only you need to specify only one Method")
            print "Scanning mode: Allowed Sources Detection"

            accepted_method = methods[0]
            param_name = args["param_name"]
            accepted_value = args["accepted_value"]
            param_source = args["param_source"]

            requests = detect_accepted_sources(self.http_helper,
                                               target,
                                               data,
                                               headers,
                                               param_name,
                                               param_source,
                                               accepted_value,
                                               accepted_method)
            responses = self.fuzz(args, requests)
            analyze_accepted_sources(responses, self.detection_struct)

        elif args["mode"] == "content_type_tamper":
            print "Tampering Content-Type mode"
            cnt_types = load_payload_file("./payloads/HTTP/content_types.txt")
            new_headers = self.http_helper.add_header_param(
                headers,
                "Content-Type", self.fsig)
            self.pm = PlaceholderManager(self.sig)
            requests = self.pm.transformed_http_requests(
                self.http_helper,
                methods,
                target,
                cnt_types,  # Payloads
                new_headers,
                data)
            responses = self.fuzz(args, requests)
            for response in responses:
                print "[->]Request"
                print_request(response)
                print "[<-]Response"
                print_response(response)
                print
        # HPP modes
        elif args["mode"] == "asp_hpp" or args["mode"] == "param_overwriting":
            self.require(args, ["param_name", "param_source", "payloads"])
            param_name = args["param_name"]
            param_source = args["param_source"]
            self.is_detection_set(args)
            payloads = []
            for p_file in args["payloads"]:
                payloads += load_payload_file(p_file)
            if args["mode"] == "asp_hpp":
                print "Scanning mode: ASP HPP Parameter Splitting"
                requests = asp_hpp(self.http_helper,
                                   methods,
                                   payloads,
                                   param_name,
                                   param_source,
                                   target,
                                   headers,
                                   data)
                responses = self.fuzz(args, requests)
            elif args["mode"] == "param_overwriting":
                requests = param_overwrite(self.http_helper,
                                           param_name,
                                           param_source,
                                           payloads[0],
                                           target,
                                           data,
                                           headers)
                responses = self.fuzz(args, requests)
            analyze_responses(responses,
                              self.http_helper,
                              self.detection_struct)

        elif args["mode"] == "detect_chars":
            self.is_detection_set(args)
            payloads = []
            for i in range(0, 256):
                payloads.append(chr(i))

            requests = self.pm.transformed_http_requests(self.http_helper,
                                                         methods,
                                                         target,
                                                         payloads,
                                                         headers,
                                                         data)
            responses = self.fuzz(args, requests)
            sent_payloads = analyze_chars(responses,
                                          self.http_helper,
                                          self.detection_struct)
            payloads = []
            if sent_payloads["detected"]:
                # urlencode blocked chars
                print
                print "URL encoding bad characters"
                for bad_char in sent_payloads["detected"]:
                    payloads.append(urlencode(bad_char))
                requests = self.pm.transformed_http_requests(self.http_helper,
                                                             methods,
                                                             target,
                                                             payloads,
                                                             headers,
                                                             data)
                responses = self.fuzz(args, requests)
                analyze_encoded_chars(responses,
                                      self.http_helper,
                                      self.detection_struct)

                print
                print "UnicodeURL encoding bad characters"
                payloads = []
                # unicode urlencode blocked chars
                for bad_char in sent_payloads["detected"]:
                    payloads.append(unicode_urlencode(bad_char))
                requests = self.pm.transformed_http_requests(self.http_helper,
                                                             methods,
                                                             target,
                                                             payloads,
                                                             headers,
                                                             data)
                responses = self.fuzz(args, requests)
                analyze_encoded_chars(responses,
                                      self.http_helper,
                                      self.detection_struct)
            # Finding a white-listed character
                good_char = None
                for char in string.letters:
                    good_char = char
                    break
                if not good_char:
                    for char in string.digits:
                        good_char = char
                        break
                if not good_char:
                    good_char = sent_payloads["undetected"][0]

                print
                print "Sending a detected char followed by an undetected"
                payloads = []
                # add an accepted char before a blocked char
                for bad_char in sent_payloads["detected"]:
                    payloads.append(bad_char + good_char)
                requests = self.pm.transformed_http_requests(self.http_helper,
                                                             methods,
                                                             target,
                                                             payloads,
                                                             headers,
                                                             data)
                responses = self.fuzz(args, requests)
                analyze_encoded_chars(responses,
                                      self.http_helper,
                                      self.detection_struct)
                print
                print "Sending a detected char after an undetected"
                payloads = []
                for bad_char in sent_payloads["detected"]:
                    payloads.append(good_char + bad_char)
                requests = self.pm.transformed_http_requests(self.http_helper,
                                                             methods,
                                                             target,
                                                             payloads,
                                                             headers,
                                                             data)
                responses = self.fuzz(args, requests)
                analyze_encoded_chars(responses,
                                      self.http_helper,
                                      self.detection_struct)

                print "Sending an undetected char after a detected"
                payloads = []
                for bad_char in sent_payloads["detected"]:
                    payloads.append(bad_char + good_char)
                requests = self.pm.transformed_http_requests(self.http_helper,
                                                             methods,
                                                             target,
                                                             payloads,
                                                             headers,
                                                             data)
                responses = self.fuzz(args, requests)
                analyze_encoded_chars(responses,
                                      self.http_helper,
                                      self.detection_struct)

                print "Sending an detected char surrounded by undetected chars"
                payloads = []
                for bad_char in sent_payloads["detected"]:
                    payloads.append(good_char + bad_char + good_char)
                requests = self.pm.transformed_http_requests(self.http_helper,
                                                             methods,
                                                             target,
                                                             payloads,
                                                             headers,
                                                             data)
                responses = self.fuzz(args, requests)
                analyze_encoded_chars(responses,
                                      self.http_helper,
                                      self.detection_struct)

        # Fuzzing mode
        elif args["mode"] == "fuzz":
            fuzzing_placeholders = PlaceholderManager.get_placeholder_number(
                    self.template_signature_re, str(args))
            if fuzzing_placeholders> 1:
                Error(self.owtf, "Multiple fuzzing placeholder signatures found. "
                      "Only one fuzzing placeholder is supported.")
            elif fuzzing_placeholders == 0:
                Error(self.owtf, "No fuzzing placeholder signatures found.")
            self.is_detection_set(args)
            payloads = []
            if args["payloads"]:
                for p_file in args["payloads"]:
                    payloads += load_payload_file(p_file)
            else:
                payloads.append("")
            print "Scanning mode: Fuzzing Using placeholders"

            requests = self.pm.transformed_http_requests(self.http_helper,
                                                         methods,
                                                         target,
                                                         payloads,
                                                         headers,
                                                         data)
            responses = self.fuzz(args, requests)
            analyze_responses(responses,
                              self.http_helper,
                              self.detection_struct)

        elif args["mode"] == "show_transform_functions":
            print transformations_info()

        elif args["mode"] == "overchar":
            self.require(args, ["payloads", "accepted_value"])
            length = int(args["length"][0])
            accepted_value = args["accepted_value"][0]
            payloads = []
            for p_file in args["payloads"]:
                payloads += load_payload_file(p_file)
            payloads = [(length - len(payload)) * accepted_value + payload
                        for payload in payloads]
            requests = self.pm.transformed_http_requests(self.http_helper,
                                                         methods,
                                                         target,
                                                         payloads,
                                                         headers,
                                                         data)
            responses = self.fuzz(args, requests)
            analyze_responses(responses,
                              self.http_helper,
                              self.detection_struct)
        else:
            Error(self.owtf, "Unknown bypassing mode.")


if __name__ == "__main__":
    wafbypasser = WAFBypasser()
    arguments = get_args()
    wafbypasser.start(arguments)