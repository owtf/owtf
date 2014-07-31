#!/usr/bin/env python
"""
owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the copyright owner nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The cookie module is responsible for parsing the cookies recieved during transactions
and run analysis for user HTTP sessions.

Developed by Viyat Bhalodia (delta24) as a part of Google Summer of Code 2014 project

- Replaces the old, broken cookie manager

Custom implementation of Cookie.py (python stdlib module) is used because of following reasons:

* Rendering according to the excellent new RFC 6265
  (rather than using a unique ad hoc format inconsistently relating to
  unrealistic, very old RFCs which everyone ignored). Uses URL encoding to
  represent non-ASCII by default, like many other languages' libraries
* Liberal parsing, incorporating many complaints about Cookie.py barfing
  on common cookie formats which can be reliably parsed (e.g. search 'cookie'
  on the Python issue tracker)
* Well-documented code, with chapter and verse from RFCs
  (rather than arbitrary, undocumented decisions and huge tables of magic
  values, as you see in Cookie.py).
* Test coverage at 100%, with a much more comprehensive test suite
  than Cookie.py
* Single-source compatible with the following Python versions:
  2.6, 2.7, 3.2, 3.3 and PyPy (2.7).
* Cleaner, less surprising API
* Friendly to customization, extension, and reuse of its parts.

Things it does NOT do:

* Maintain backward compatibility with Cookie.py, which would mean
  inheriting its confusions and bugs
* Implement RFCs 2109 or 2965, which have always been ignored by almost
  everyone and are now obsolete as well
* Handle every conceivable output from terrible legacy apps, which is not
  possible to do without lots of silent data loss and corruption (the
  parser does try to be liberal as possible otherwise, though)
* Provide a means to store pickled Python objects in cookie values
  (that's a big security hole)

"""

from framework.http.cookies.cookies import Cookies


def parse(string):
    """ Returns a list of dict from the `Set-Cookie` header. """
    # Several cookies can be set at once separated by ","
    try:
        # resulting cookies object can used like a dict of Cookie objects
        # c = Cookies.parse_response("Set-Cookie: a=b; c=d; e=f")
        # c.keys()  -->  ['a', 'c', 'e']
        # c['a'].value = "b"
        cookies = Cookies.parse_response("Set-Cookie: {}".format(string))
        return cookies
    except Exception, e:
        raise e
