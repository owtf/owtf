from framework.utils import OWTFLogger
from framework.utils import OWTFLogger
from framework.dependency_management.dependency_resolver import ServiceLocator
"""
GREP Plugin for Credentials transport over an encrypted channel (OWASP-AT-001)
https://www.owasp.org/index.php/Testing_for_credentials_transport_%28OWASP-AT-001%29
NOTE: GREP plugins do NOT send traffic to the target and only grep the HTTP Transaction Log
"""
import logging
DESCRIPTION = "Searches transaction DB for credentials protections"

def run(PluginInfo):
	#ServiceLocator.get_component("config").Show()
        # TODO: Needs fixing
        """
	Content = "This plugin looks for password fields and then checks the URL (i.e. http vs. https)<br />"
	Content += "Uniqueness in this case is performed via URL + password field"
	# This retrieves all hidden password fields found in the DB response bodies:
	Command, RegexpName, Matches = ServiceLocator.get_component("transaction").GrepMultiLineResponseRegexp(ServiceLocator.get_component("config").Get('RESPONSE_REGEXP_FOR_PASSWORDS'))
	# Now we need to check if the URL is https or not and count the insecure ones (i.e. not https)
	IDs = []
	InsecureMatches = []
	for ID, FileMatch in Matches:
		if ID not in IDs: # Retrieve Transaction from DB only once
			IDs.append(ID) # Process each transaction only once
			Transaction = ServiceLocator.get_component("transaction").GetByID(ID)
		if 'https' != Transaction.URL.split(":")[0]:
			OWTFLogger.log("Transaction: "+ID+" contains passwords fields with a URL different than https")
			InsecureMatches.append([ID, Transaction.URL+": "+FileMatch]) # Need to make the unique work by URL + password
	Message = "<br /><u>Total insecure matches: "+str(len(InsecureMatches))+'</u>'
	OWTFLogger.log(Message)
	Content += Message+"<br />"
	Content += ServiceLocator.get_component("plugin_helper").DrawResponseMatchesTables([Command, RegexpName, InsecureMatches], PluginInfo)
	return Content
        """
        return []
