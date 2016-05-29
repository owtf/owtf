from lxml import etree
from framework.http.wafbypasser.core import obfuscation_lib


class XMLAnalyzer(object):

    """Analyzes the XML input tags and performs multiple transformations.

    The multiple trans are defined by the XML tags.
    It is a helper class for template parser.
    The methods that it contains are the parsing events.

    In the stack there are stored 3 types of values (A F and D):

        + A stands for ATTRIBUTE. The XML attributes are translated as
          parameters for the equivalant function.
        + D stands for DATA.
        + F stands for FUNCTION.

    """

    def __init__(self, linking_table):
        self.stack = []
        self.encoded_string = ""
        self.linking_table = linking_table
        #print "Parser Info: Parsing Started"

    def start(self, tag, attrib):
        try:
            function = self.linking_table[tag]
        except KeyError:
            print "Parser Warning: Unknown starting tag found ("\
                  + tag + "). Ignoring..."
            return

        self.stack.append(["F", function])
        if dict(attrib):
            self.stack.append(["A", attrib])

    def end(self, tag):
        data = ""
        arglist = []

        if tag not in[key for key in self.linking_table]:
            print "Parser Warning: Unknown ending tag found (" + tag + \
                  "). Ignoring..."
            return

        while True:
            element = self.stack.pop()
            if element[0] == 'D':
                data += element[1]
                continue
            break

        if element[0] == 'A':
            args = element[1]
            for value in args.itervalues():
                arglist.append(value)
            function = self.stack.pop()[1]
        else:
            function = element[1]

        if data:
            arglist.append(data)
            arglist.reverse()

        data = function(*arglist)
        self.stack.append(["D", data])

    def data(self, data):
        self.stack.append(['D', data])

    def comment(self, text):
        print("Parser Info: Comment Found: (%s). Ignoring ..." % text)

    def close(self):
        #print("Parser Info: Parsing Complete")
        return self.stack.pop()[1]


class TemplateParser(object):
    """Manage the fuzzing templates."""

    def __init__(self):
        self.payload_data = None
        self.linking_table = obfuscation_lib.get_transformations()
        self.linking_table.update({"payload": self.payload})
        self.linking_table.update(
            {"transform_payload": self.transform_payload})

    def transform_payload(self, string):
        """Return the output.

        This function is needed to be called at the end of the parsing in order
        to return the output.

        """
        return string

    def set_payload(self, string):
        self.payload_data = string

    def add_functions(self, functions):
        self.linking_table(functions)

    def transform(self, xml_string, signature="@@@"):
        xml_string = xml_string.replace(signature, "<transform_payload>", 1)
        xml_string = xml_string.replace(signature, "</transform_payload>", 1)
        self.parser = etree.XMLParser(target=XMLAnalyzer(self.linking_table))
        return etree.XML(xml_string, self.parser)

    def payload(self):
        return self.payload_data or ''
