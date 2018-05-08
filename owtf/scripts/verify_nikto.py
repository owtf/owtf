#!/usr/bin/env python
"""
Tries to put links around nikto findings to save a bit of time in manual verification
This files actually converts target urls & OSVDB codes into clickable links
"""
import re
import sys

import tornado.template

from owtf.utils.strings import to_str


if len(sys.argv) < 3:
    print("Usage: %s <nikto.txt file> <top_url>" % sys.argv[0])
    exit(-1)

osvdb_regexp = re.compile("\+ (OSVDB-[0-9]+):.*")
url_regexp = re.compile("(/[^ :]*):")
link_list = []
top_url = sys.argv[2]
origin = sys.argv[1]  # The original nikto output file
destination = "Nikto_Verify.html"
output_template = tornado.template.Template(
    """
    <html>
        <title>Nikto Verification</title>
        <body>
            {% autoescape None %}
            <p>{{ content }}</p>
        </body>
    </html>
    """
)
link_template = tornado.template.Template("<a href='{{ link }}' target='_blank'>{{ text }}</a>")

# Replace the text with links where needed
nikto_output = open(origin, "r").read()
for match in url_regexp.findall(nikto_output):
    url = top_url + match
    if url not in link_list:
        link_list.append(url)
    nikto_output = nikto_output.replace(match, link_template.generate(link=url, text=match).decode("utf-8"))

for match in osvdb_regexp.findall(nikto_output):
    osvdb_id = match.split("-")[1]
    osvdb_url = "http://osvdb.org/show/osvdb/" + osvdb_id
    nikto_output = nikto_output.replace(match, link_template.generate(link=osvdb_url, text=match).decode("utf-8"))
    if osvdb_url not in link_list:
        link_list.append(osvdb_url)

# Print here, since the links are constructed by here. Why printing? So that it is visible as command output
print(nikto_output)

# Replace newlines with breaks before writing to html file
nikto_output = nikto_output.replace("\n", "</br>")

# Generate html output directly to stdout, looks better in the report
with open(destination, "w") as file:
    out = output_template.generate(content=nikto_output)
    file.write(to_str(out))
