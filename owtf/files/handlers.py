"""
owtf.files.handlers
~~~~~~~~~~~~~~~~~~~
"""
import datetime
import email.utils
import hashlib
import mimetypes
import os
import stat
import subprocess
import time

import tornado
import tornado.template
import tornado.web

__all__ = ["StaticFileHandler"]


class StaticFileHandler(tornado.web.StaticFileHandler):

    def set_default_headers(self):
        self.add_header("Access-Control-Allow-Origin", "*")
        self.add_header("Access-Control-Allow-Methods", "GET")

    def get(self, path, include_body=True):
        """
        This is an edited method of original class so that we can show
        directory listing and set correct Content-Type
        """
        path = self.parse_url_path(path)
        abspath = os.path.abspath(os.path.join(self.root, path))
        self.absolute_path = abspath
        if not os.path.exists(abspath):
            raise tornado.web.HTTPError(404)

        # Check if a directory if so provide listing
        if os.path.isdir(abspath):
            # need to look at the request.path here for when path is empty
            # but there is some prefix to the path that was already
            # trimmed by the routing
            # Just loop once to get dirnames and filenames :P
            for abspath, dirnames, filenames in os.walk(abspath):
                break
            directory_listing_template = tornado.template.Template(
                """
                <html>
                <head>
                    <title>Directory Listing</title>
                </head>
                <body>
                    <h1>Index of</h1>
                    <hr>
                    <ul>
                        <li><a href="../">../</a></li>
                        {% if len(dirnames) > 0 %}
                            <h2>Directories</h2>
                            {% for item in dirnames %}
                                <li><a href="{{ url_escape(item, plus=False) }}/">{{ item }}/</a></li>
                            {% end %}
                        {% end %}
                        {% if len(filenames) > 0 %}
                            <h2>Files</h2>
                            {% for item in filenames %}
                                <li><a href="{{ url_escape(item, plus=False) }}">{{ item }}</a></li>
                            {% end %}
                        {% end %}
                    </ul>
                </body>
                </html>
                """
            )
            self.write(directory_listing_template.generate(dirnames=dirnames, filenames=filenames))
            return

        if os.path.isfile(abspath):  # So file
            stat_result = os.stat(abspath)
            modified = datetime.datetime.fromtimestamp(stat_result[stat.ST_MTIME])
            self.set_header("Last-Modified", modified)
            mime_type, encoding = mimetypes.guess_type(abspath)
            if mime_type:
                self.set_header("Content-Type", mime_type)
            cache_time = self.get_cache_time(path, modified, mime_type)
            if cache_time > 0:
                self.set_header("Expires", datetime.datetime.utcnow() + datetime.timedelta(seconds=cache_time))
                self.set_header("Cache-Control", "max-age={!s}".format(cache_time))
            else:
                self.set_header("Cache-Control", "public")

            self.set_extra_headers(path)

            # Check the If-Modified-Since, and don't send the result if the
            # content has not been modified
            ims_value = self.request.headers.get("If-Modified-Since")
            if ims_value is not None:
                date_tuple = email.utils.parsedate(ims_value)
                if_since = datetime.datetime.fromtimestamp(time.mktime(date_tuple))
                if if_since >= modified:
                    self.set_status(304)
                    return

            no_of_lines = self.get_argument("lines", default="-1")
            if no_of_lines != "-1":
                data = subprocess.check_output(["tail", "-" + no_of_lines, abspath])
            else:
                with open(abspath, "rb") as file:
                    data = file.read()

            hasher = hashlib.sha1()
            hasher.update(data)
            self.set_header("Etag", '"{!s}"'.format(hasher.hexdigest()))
            if include_body:
                self.write(data)
            else:
                assert self.request.method == "HEAD"
                self.set_header("Content-Length", len(data))
