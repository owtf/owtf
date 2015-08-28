from framework.dependency_management.dependency_resolver import ServiceLocator

"""
SEMI-PASSIVE Plugin for Testing for Session Management Schema (OWASP-SM-001)
https://www.owasp.org/index.php/Testing_for_Session_Management_Schema_%28OWASP-SM-001%29
"""

import string, re
import cgi, logging
from framework.lib import general

DESCRIPTION = "Normal requests to gather session managament info"


def run(PluginInfo):
    # ServiceLocator.get_component("config").Show()
    # True = Use Transaction Cache if possible: Visit the start URLs if not already visited
    # Step 1 - Find transactions that set cookies
    # Step 2 - Request 10 times per URL that sets cookies
    # Step 3 - Compare values and calculate randomness
    URLList = []
    TransactionList = []
    Result = ""
    return ([])
    # TODO: Try to keep up Abe's promise ;)
    #return "Some refactoring required, maybe for BSides Vienna 2012 but no promises :)"
    transaction = ServiceLocator.get_component("transaction")
    for ID in transaction.GrepTransactionIDsForHeaders(
            [ServiceLocator.get_component("config").Get('HEADERS_FOR_COOKIES')]):  # Transactions with cookies
        URL = transaction.GetByID(ID).URL  # Limitation: Not Checking POST, normally not a problem ..
        if URL not in URLList:  # Only if URL not already processed!
            URLList.append(URL)  # Keep track of processed URLs
            AllCookieValues = {}
            for i in range(0, 2):  # Get more cookies to perform analysis
                Transaction = ServiceLocator.get_component("requester").GetTransaction(False, URL)
    return Result
