"""
SEMI-PASSIVE Plugin for Testing for Session Management Schema (OWASP-SM-001)
https://www.owasp.org/index.php/Testing_for_Session_Management_Schema_%28OWASP-SM-001%29
"""
import json
from collections import defaultdict

from owtf.config import config_handler
from owtf.requester.base import requester
from owtf.managers.transaction import get_transaction_by_id, search_by_regex_names

DESCRIPTION = "Normal requests to gather session management info"


def run(PluginInfo):
    # True = Use Transaction Cache if possible: Visit the start URLs if not already visited
    # Step 1 - Find transactions that set cookies
    # Step 2 - Request 10 times per URL that sets cookies
    # Step 3 - Compare values and calculate randomness
    url_list = []
    cookie_dict = defaultdict(list)

    # Get all possible values of the cookie names and values
    for id in search_by_regex_names(
        [config_handler.get_val("HEADERS_FOR_COOKIES")]
    ):  # Transactions with cookies
        url = get_transaction_by_id(id)
        if url:
            url = url.url  # Limitation: Not Checking POST, normally not a problem
        else:
            continue
        if url not in url_list:  # Only if URL not already processed!
            url_list.append(url)  # Keep track of processed URLs
            for _ in range(0, 10):  # Get more cookies to perform analysis
                transaction = requester.get_transaction(False, url)
                cookies = transaction.get_session_tokens()
                for cookie in cookies:
                    cookie_dict[cookie.name].append(str(cookie.value))
    # Leave the randomness test to the user
    return json.dumps(cookie_dict)
