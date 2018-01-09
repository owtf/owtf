"""
owtf.interface.reporter
~~~~~~~~~~~~~~~~~~~~~~~

The reporter module is in charge of producing the HTML Report as well as
provide plugins with common HTML Rendering functions

.note::
    This is being deprecated.
"""

import cgi

from tornado.template import Loader

from owtf.http.requester import requester
from owtf.settings import POUTPUT_TEMPLATES_DIR


class Reporter(object):
    def __init__(self):
        self.requester = None
        self.Init = False
        self.Loader = Loader(POUTPUT_TEMPLATES_DIR)
        self.mNumLinesToShow = 15
        self.CounterList = []
        self.requester = requester

    def TransactionTableFromIDs(self, TransactionIDs, NumLinesReq=15, NumLinesRes=15):
        """ Draws a table of HTTP Transactions """
        # functions to get the first lines of a long string
        transactions = self.transaction.get_by_ids(TransactionIDs)
        return self.TransactionTableForTransactions(transactions)

    def TransactionTableForURL(self, UseCache, URL, Method=None, Data=None):
        transaction = self.requester.get_transaction(UseCache, URL, method=Method, data=Data)
        return self.TransactionTableForTransactions([transaction])

    def TransactionTableForURLList(self, UseCache, URLList, Method=None, Data=None):
        transactions = self.requester.get_transactions(UseCache, URLList, method=Method, data=Data)
        return self.TransactionTableForTransactions(transactions)

    def TransactionTableForTransactions(self, Transactions):
        return self.Loader.load("transaction_table.html").generate(TransactionList=Transactions)

    def str(self, *args):
        try:
            return str(*args)
        except TypeError:
            return args[0]  # Input is already Unicode

    def reset_loader(self):
        return self.Loader.reset()

# ----------------------------------- Methods exported from plugin_helper.py ---------------------------------

    def cmd_table(self, command):
        return self.Loader.load("command_table.html").generate(Command=Command)

    def link_list(self, link_listName, Links):
        """
        Wrapper to allow rendering a bunch of links -without name- as resource
        links with name = link
        """
        return self.Loader.load("link_list.html").generate(link_listName=link_listName, Links=Links)

    def resource_linklist(self, ResourceListName, ResourceList):
        """
        Draws an HTML Search box for defined Vuln Search resources
        """
        return self.Loader.load("resource_link_list.html").generate(ResourceListName=ResourceListName,
                                                                    ResourceList=ResourceList)

    def Tabbedresource_linklist(self, ResourcesList):
        """
        ResourceList = [
            "ResourceListName", [["Name1","Resource1"],["Name2","Resource2"]]
        ]
        """
        TabData = []
        Resources = []
        for ResourceListName, ResourceList in ResourcesList:
            TabID = ResourceListName.replace(' ', '_')
            TabData.append([ResourceListName, TabID])
            Resources.append([TabID, ResourceList])
        return self.Loader.load("tabbed_resource_link_list.html").generate(TabData=TabData, Resources=Resources)

    def ListPostProcessing(self, ResourceListName, link_list, HTMLlink_list):
        return self.Loader.load("list_post_processing.html").generate(ResourceListName=ResourceListName,
                                                                      link_list=link_list, HTMLlink_list=HTMLlink_list)

    def Requestlink_list(self, ResourceListName, link_list):
        return self.Loader.load("request_link_list.html").generate(ResourceListName=ResourceListName, link_list=link_list)

    def VulnerabilitySearchBox(self, SearchStr):
        """
        Draws an HTML Search box for defined Vuln Search resources
        """
        VulnSearchResources = self.resource.get_resources('VulnSearch')
        return self.Loader.load("vulnerability_search_box.html").generate(SearchStr=SearchStr,
                                                                          VulnSearchResources=VulnSearchResources)

    def SuggestedCommandBox(self, PluginOutputDir, CommandCategoryList, Header=''):
        """
        Draws HTML tabs for a list of TabName => Resource Group (i.e. how to run hydra, etc)
        """
        TitleList = []
        CommandList = []
        for item in CommandCategoryList:
            TitleList.append(item[0])
            CommandList.append(self.resource.get_resources(item[1]))
        # TODO: Fix up the plugin
        return self.Loader.load("suggested_command_box.html").generate(Header=Header, TitleList=TitleList,
                                                                       CommandList=CommandList)

    def CommandDump(self, Name, CommandIntro, ModifiedCommand, RelativeFilePath, OutputIntro, TimeStr):
        AbsPath = self.plugin_handler.get_abs_path(RelativeFilePath)
        OutputLines = open(AbsPath, "r").readlines()
        longOutput = (len(OutputLines) > self.mNumLinesToShow)
        if (len(OutputLines) > self.mNumLinesToShow):
            OutputLines = ''.join(OutputLines[0:self.mNumLinesToShow])
        else:
            OutputLines = ''.join(OutputLines)
        table_vars = {
            "Name": Name,
            "CommandIntro": CommandIntro,
            "ModifiedCommand": ModifiedCommand,
            "FilePath": RelativeFilePath,
            "OutputIntro": OutputIntro,
            "OutputLines": OutputLines,
            "TimeStr": TimeStr,
            "mNumLinesToShow": self.mNumLinesToShow,
            "longOutput": longOutput
        }
        return self.Loader.load("command_dump.html").generate(**table_vars)

    def URLsFromStr(self, TimeStr, VisitURLs, URLList, NumFound):
        html_content = self.Loader.load("urls_from_str.html").generate(TimeStr=TimeStr, VisitURLs=VisitURLs,
                                                                       NumURLs=len(URLList), NumFound=NumFound)
        if URLList:
            html_content += self.link_list("URLs Scraped", URLList)
        return html_content

    def Robots(self, NotStr, NumLines, NumAllow, NumDisallow, NumSitemap, SavePath, EntriesList, NumAddedURLs):
        vars = {
            "robots_found": NotStr,
            "num_lines": NumLines,
            "num_allow": NumAllow,
            "num_disallow": NumDisallow,
            "num_sitemap": NumSitemap,
            "save_path": SavePath
        }
        TestResult = self.Loader.load("robots.html").generate(**vars)
        # robots.txt contains some entries, show browsable list! :)
        if NumDisallow > 0 or NumAllow > 0 or NumSitemap > 0:
            for Display, Links in EntriesList:
                if Links:  # Filters empty lists
                    TestResult += self.resource_linklist(Display, Links)
        return TestResult

    def HtmlString(self, String):
        return String

# ---------------------- Grep Plugin Outputs -------------------- #
    def ResponseBodyMatches(self, ResponseRegexpName):
        RegexpName, GrepOutputs, TransactionIDS, match_percent = self.transaction.search_by_regex_name(ResponseRegexpName,
                                                                                                       stats=True)
        variables = {
            "name": RegexpName.replace("RESPONSE_REGEXP_FOR_", "").replace('_', ' '),
            "matches": GrepOutputs,
            "transaction_ids": TransactionIDS,
            "match_percent": match_percent
        }
        return self.Loader.load("response_matches.html").generate(**variables)

    def ResponseHeaderMatches(self, HeaderRegexpName):
        return self.ResearchHeaders(HeaderRegexpName)[0]

    def ResearchHeaders(self, RegexName):
        regex_name, grep_outputs, transaction_ids, match_percent = self.transaction.search_by_regex_name(RegexName,
                                                                                                         stats=True)
        # [[unique_matches, matched_transactions, matched_percentage]]
        searches = self.Loader.load("header_searches.html").generate(match_percent=match_percent, matches=grep_outputs,
                                                                     transaction_ids=transaction_ids)
        return [searches, grep_outputs]

    def FingerprintData(self):
        HeaderTable, matches = self.ResearchHeaders('HEADERS_FOR_FINGERPRINT')
        for item in matches:
            # Add Vulnerability search boxes after table
            HeaderTable += self.VulnerabilitySearchBox(item[1])
        return HeaderTable

    def TopTransactionsBySpeed(self, Order):
        transactions = self.transaction.get_top_by_speed(Order)
        return self.TransactionTableForTransactions(transactions)

    def CookieAttributeAnalysis(self, CookieValueList, Header2TransacDict):
        vars = {
            "Cookies": [{
                "Name": Cookie.split('=')[0],
                "Link": Header2TransacDict[self.config.get('HEADERS_FOR_COOKIES').lower() + Cookie],
                "Attribs": Cookie.replace(Cookie.split('=')[0] + "=", "").replace("; ", ";").split(";"),
            } for Cookie in CookieValueList],
        }
        Table = self.Render.CreateTable({'class': 'report_intro'})
        SetCookie = self.config.get('HEADERS_FOR_COOKIES').lower()
        PossibleCookieAttributes = self.config.get('COOKIE_ATTRIBUTES').split(',')
        for Cookie in CookieValueList:
            CookieName = Cookie.split('=')[0]
            CookieLink = self.Render.DrawButtonLink(cgi.escape(CookieName), Header2TransacDict[SetCookie + Cookie])
            CookieAttribs = Cookie.replace(CookieName + "=", "").replace("; ", ";").split(";")
            Table.CreateCustomRow('<tr><th colspan="2">Cookie: %s</th></tr>' % CookieLink)
            Table.CreateRow(['Attribute', 'Value'], True)
            NotFoundStr = "<b>Not Found</b>"
            if CookieAttribs[0]:
                CookieValue = CookieAttribs[0]
            else:
                CookieValue = NotFoundStr
            Table.CreateRow(['Value', CookieValue])
            for Attrib in PossibleCookieAttributes:
                DisplayAttribute = NotFoundStr
                for PresentAttrib in CookieAttribs:
                    # Avoid false positives due to cookie contents
                    if PresentAttrib.lower().startswith(Attrib.lower()):
                        DisplayAttribute = PresentAttrib
                        break
                Table.CreateRow([Attrib, DisplayAttribute])
        if Table.GetNumRows() == 0:
                return ""  # No Attributes found
        return "<h3>Cookie Attribute Analysis</h3>%s" % Table.Render()


reporter = Reporter()
