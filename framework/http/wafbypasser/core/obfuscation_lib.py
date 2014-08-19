from urllib2 import *
from base64 import *


# Each transformation function should be added to this dictionary
def get_transformations():
    return {
        "base64": base64,
        "urlsafe_base64": urlsafe_base64,
        "hex": hex,
        "remove_spaces": remove_spaces,
        "urlencode": urlencode,
        "xmlcharrefreplace": xmlcharrefreplace,
        "html_escape": html_escape,
        "utf8": utf8,
        "utf16": utf16,
        "utf32": utf32,
        "replace": replace,
        "reverse": reverse,
        "remove_newlines": remove_newlines,
        "unicode_urlencode": unicode_urlencode
    }


def transformations_info():
        info = ""
        info += "Base64 encoding. Usage <base64>...</base64>\n"
        info += "URL safe base64 encoding. Usage <urlsafe_base64>..." \
                "</urlsafe_base64>\n"
        info += "HEX encoding. Usage <hex>...</hex>\n"
        info += "remove_space transformation. Usage <remove_space>..." \
                "</remove_spaces>\n"
        info += "Urlencode encoding. Usage <urlencode>...</urlencode>\n"
        info += "Xmlcharrefreplace encoding. Usage <xmlcharrefreplace>..." \
                "</xmlcharrefreplace>\n"
        info += "Html_escape encoding. Usage <html_escape>...</html_escape>\n"
        info += "UTF-8 encoding. Usage <utf8>...</utf8>\n"
        info += "UTF-16 encoding. Usage <utf16>...</utf16>\n"
        info += "UTF-32 encoding. Usage <utf32>...</utf32>\n"
        info += "Replace tranformation. Usage <replace string1=\"A\" " \
                "string2=\"B\" >...</replace>\n. This will replace A with B." \
                " It is important to have the attribute in the correct" \
                " order.\n"
        info += "Remove new lines transformation. Usage <remove_newlines>..." \
                "</remove_newlines>\n"
        info += "Unicode urlencode encoding. Usage <unicode_urlencode>..." \
                "</unicode_urlencode>\n"
        info += "loading payloads from file <payload/>. You need to specify " \
                "the file with the payloads. Example, encoding payloads to" \
                " base64 <base64><payload/></base64>"
        return info

#credits to wafw00f and http://packetstormsecurity.org/web/unicode-fun.txt
urlunicodechars = {' ': '%u0020',
                   '/': '%u2215',
                   '\\': '%u2215',
                   "'": '%u02b9',
                   '"': '%u0022',
                   '>': '%u003e',
                   '<': '%u003c',
                   '#': '%uff03',
                   '!': '%uff01',
                   '$': '%uff04',
                   '*': '%uff0a',
                   '@': '%u0040',
                   '.': '%uff0e',
                   '_': '%uff3f',
                   '(': '%uff08',
                   ')': '%uff09',
                   ',': '%uff0c',
                   '%': '%u0025',
                   '-': '%uff0d',
                   ';': '%uff1b',
                   ':': '%uff1a',
                   '|': '%uff5c',
                   '&': '%uff06',
                   '+': '%uff0b',
                   '=': '%uff1d',
                   'a': '%uff41',
                   'A': '%uff21',
                   'b': '%uff42',
                   'B': '%uff22',
                   'c': '%uff43',
                   'C': '%uff23',
                   'd': '%uff44',
                   'D': '%uff24',
                   'e': '%uff45',
                   'E': '%uff25',
                   'f': '%uff46',
                   'F': '%uff26',
                   'g': '%uff47',
                   'G': '%uff27',
                   'h': '%uff48',
                   'H': '%uff28',
                   'i': '%uff49',
                   'I': '%uff29',
                   'j': '%uff4a',
                   'J': '%uff2a',
                   'k': '%uff4b',
                   'K': '%uff2b',
                   'l': '%uff4c',
                   'L': '%uff2c',
                   'm': '%uff4d',
                   'M': '%uff2d',
                   'n': '%uff4e',
                   'N': '%uff2e',
                   'o': '%uff4f',
                   'O': '%uff2f',
                   'p': '%uff50',
                   'P': '%uff30',
                   'q': '%uff51',
                   'Q': '%uff31',
                   'r': '%uff52',
                   'R': '%uff32',
                   's': '%uff53',
                   'S': '%uff33',
                   't': '%uff54',
                   'T': '%uff34',
                   'u': '%uff55',
                   'U': '%uff35',
                   'v': '%uff56',
                   'V': '%uff36',
                   'w': '%uff57',
                   'W': '%uff37',
                   'x': '%uff58',
                   'X': '%uff38',
                   'y': '%uff59',
                   'Y': '%uff39',
                   'z': '%uff5a',
                   'Z': '%uff3a',
                   '0': '%uff10',
                   '1': '%uff11',
                   '2': '%uff12',
                   '3': '%uff13',
                   '4': '%uff14',
                   '5': '%uff15',
                   '6': '%uff16',
                   '7': '%uff17',
                   '8': '%uff18',
                   '9': '%uff19'}


def base64(string):
    return standard_b64encode(string)


def urlsafe_base64(string):
    return urlsafe_b64encode(string)


def hex(string):
    return string.encode("hex")


def remove_spaces(string):
    return string.replace(" ", "")


def urlencode(string):
    return quote(string)


def xmlcharrefreplace(string):
    return string.encode('ascii', 'xmlcharrefreplace')


html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
}


# credits https://wiki.python.org/moin/EscapingHtml
def html_escape(text):
    """Produce entities within text."""
    return "".join(html_escape_table.get(c, c) for c in text)


def utf8(string):
    return string.encode('utf-8')


def utf16(string):
    return string.encode('utf-16')


def utf32(string):
    return string.encode('utf-32')


def replace(string, old, new):
    return string.replace(old, new)


def reverse(string):
    return string[::-1]


def remove_newlines(string):
    string = string.replace("\n", "")
    return string.replace("\r", "")


def unicode_urlencode(string):
    encoded_str = str()
    for char in string:

        if char in urlunicodechars:
            encoded_str += urlunicodechars[char]
        else:
            encoded_str += char
    return encoded_str