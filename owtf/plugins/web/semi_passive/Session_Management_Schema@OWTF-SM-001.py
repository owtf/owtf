"""
SEMI-PASSIVE Plugin for Testing for Session Management Schema (OWASP-SM-001)
https://www.owasp.org/index.php/Testing_for_Session_Management_Schema_%28OWASP-SM-001%29
"""
from collections import defaultdict
import json

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Normal requests to gather session managament info"


def run(PluginInfo):
    # True = Use Transaction Cache if possible: Visit the start URLs if not already visited
    # Step 1 - Find transactions that set cookies
    # Step 2 - Request 10 times per URL that sets cookies
    # Step 3 - Compare values and calculate randomness
    url_list = []
    cookie_dict = defaultdict(list)

    # Get all possible values of the cookie names and values
    transaction = ServiceLocator.get_component("transaction")
    for id in transaction.search_by_regex_names(
            [ServiceLocator.get_component("config").get('HEADERS_FOR_COOKIES')]):  # Transactions with cookies
        url = transaction.get_by_id(id).URL  # Limitation: Not Checking POST, normally not a problem
        if url not in url_list:  # Only if URL not already processed!
            url_list.append(url)  # Keep track of processed URLs
            for _ in range(0, 10):  # Get more cookies to perform analysis
                transaction = ServiceLocator.get_component("requester").get_transaction(False, url)
                cookies = transaction.get_session_tokens()
                for cookie in cookies:
                    cookie_dict[cookie.name].append(str(cookie.value))
    # Leave the randomness test upto the user
    return json.dumps(cookie_dict)
