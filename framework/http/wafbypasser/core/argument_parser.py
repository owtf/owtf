import argparse


def get_args():
        parser = argparse.ArgumentParser(description='OWTF WAF-BYPASSER MODULE')

        parser.add_argument("-X", "--method",
                            dest="METHODS",
                            action='store',
                            nargs="+",
                            help="Specify Method . (Ex: -X GET . \
                            The option @@@all@@@ loads all the HTTP methods \
                            which are listed in ./payload/HTTP/methods.txt).\
                              Custom methods can be defined in this file.")

        parser.add_argument("-C", "--cookie",
                            dest="COOKIE",
                            action='store',
                            help="Insert a cookie value. \
                            (Ex --cookie 'var=value')")

        parser.add_argument("-t", "--target",
                            dest="TARGET",
                            action='store',
                            required=True,
                            help="The target url")

        parser.add_argument("-H", "--headers",
                            dest="HEADERS",
                            action='store',
                            nargs='*',
                            help="Additional headers \
                            (ex -header 'Name:value' 'Name2:value2')")

        parser.add_argument("-L", "--length",
                            dest="LENGTH",
                            action='store',
                            nargs=1,
                            type=int,
                            help="Specify the length of accepted chars. "
                                 "Required in overchar mode")

        parser.add_argument("-d", "--data",
                            dest="DATA",
                            action='store',
                            help="POST data (ex --data 'var=value')")

        parser.add_argument("-cnt", "--contains",
                            dest="CONTAINS",
                            action='store',
                            nargs='+',
                            help="DETECTION METHOD(ex1 -cnt 'signature'  \n) \
                                 Optional Arguments:\n \
                                  Case sensitive :\n \
                                 (ex2)-cnt 'signature' cs")

        parser.add_argument("-rcd", "--response_code",
                            dest="RESP_CODE_DET",
                            action='store',
                            nargs=1,
                            help="DETECTION METHOD(Ex1 -rcd 200  \n)"
                                 "(Ex2 -rcd 400,404)+\n(ex3 rcd 200-400)\n "
                                 "(Ex4 -rcd 100,200-300)")

        parser.add_argument("-rt", "--response_time",
                            dest="RESPONSE_TIME",
                            action='store',
                            type=float,
                            nargs=1,
                            help="DETECTION METHOD(Ex -rt 30 )")

        parser.add_argument("-r", "--reverse",
                            dest="REVERSE",
                            action='store_true',
                            help="Reverse the detection method.\
                            (Negative detection)")

        parser.add_argument("-pl", "--payloads",
                            dest="PAYLOADS",
                            action='store',
                            nargs='*',
                            help="FILE with payloads')(Ex file1 , file2)")

        parser.add_argument("-fs", "--fuzzing_signature",
                            dest="FUZZING_SIG",
                            action='store',
                            help="The default fuzzing signature is @@@.\
                             You can change it with a custom signature.")

        parser.add_argument("-apv", "--accepted_value",
                            dest="ACCEPTED_VALUE",
                            action='store',
                            help="Accepted parameter value")

        parser.add_argument("-pn", "--param_name",
                            dest="PARAM_NAME",
                            action='store',
                            help="Specify parameter name")

        parser.add_argument("-ps", "--param_source",
                            dest="PARAM_SOURCE",
                            action='store',
                            choices=['URL', 'DATA', 'COOKIE', 'HEADER'],
                            help="Specifies the parameters position.")
        parser.add_argument("-dl", "--delay",
                            dest="DELAY",
                            action='store',
                            type=int,
                            help="Changes the Fuzzing method from \
                                 asynchronous to synchronous(slower). This \
                                 Allows you to follow cookies and specify a \
                                 delay time in seconds before sending a \
                                 request.")
        parser.add_argument("-fc", "--follow-cookies",
                            dest="FOLLOW_COOKIES",
                            action='store_true',
                            help="Changes the Fuzzing method from \
                                 asynchronous to synchronous(slower). This \
                                 Allows you to follow cookies and specify a \
                                 delay time in seconds before sending a \
                                 request.")

        parser.add_argument("-m", "--mode",
                            dest="MODE",
                            required=True,
                            choices=['fuzz', 'detect_chars','asp_hpp',
                                     'param_overwriting', "length",
                                     "detect_accepted_sources",
                                     "content_type_tamper",
                                     "show_transform_functions", "overchar"],
                            action='store',
                            help="Select mode:"
                                 "(fuzz)Fuzzing mode.\n"
                                 "(detect_chars)Detects the available "
                                 "characters and attempts to find bypasses.\n"
                                 "(asp_hpp)Splits the payload to comma (,) "
                                 "character and sends using HPP\n"
                                 "(param_overwriting)Overwrites a parameter"
                                 " by using HPP\n"
                                 "(length)Detects the length of a content "
                                 "placeholder\n"
                                 "(detect_accepted_sources)Detected the "
                                 "accepted sources of a parameter\n"
                                 "(content_type_tamper)Content type tampering "
                                 "is changing the Content-Type header and"
                                 " tries to detect anomalies.\n"
                                 "(show_tranform_function) Shows "
                                 "transformation functions\n"
                                 "(overchar)Sends the payloads after a stream "
                                 "of whitelisted characters\n")

        args = parser.parse_args()
        return {"target": args.TARGET,
                "payloads": args.PAYLOADS,
                "headers": args.HEADERS,
                "methods": args.METHODS,
                "data": args.DATA,
                "contains": args.CONTAINS,
                "resp_code_det": args.RESP_CODE_DET,
                "reverse": args.REVERSE,
                "fuzzing_signature": args.FUZZING_SIG,
                "accepted_value": args.ACCEPTED_VALUE,
                "param_name": args.PARAM_NAME,
                "param_source": args.PARAM_SOURCE,
                "delay": args.DELAY,
                "follow_cookies": args.FOLLOW_COOKIES,
                "cookie": args.COOKIE,
                "length": args.LENGTH,
                "response_time": args.RESPONSE_TIME,
                "mode": args.MODE
         }