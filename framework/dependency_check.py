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

This is the script for checking the owtf pip dependencies

"""

import os
import uuid


try:
    # Is pip even there?
    import pip
    # We do this in order to check for really old versions of pip
    pip.get_installed_distributions()
except ImportError:
    print("We recommend you run install script before launching owtf"
          "for first time")
    print("           python2 install/install.py")
    exit(1)


def verify_dependencies(root_dir):
    # Get all the installed libraries
    # installed_libraries = {"tornado": "version"}
    installed_libraries = dict(
        (i.project_name, i.version) for i in pip.get_installed_distributions())

    # Get all the libraries required by owtf
    # owtf_libraries = ["tornado", "lxml"...]
    owtf_reqs = pip.req.parse_requirements(
        os.path.join(root_dir, "install", "owtf.pip"),
        session=uuid.uuid1())
    owtf_libraries = [req.req.project_name for req in owtf_reqs]

    # Iterate over requirements and check if existed
    missing_libraries = []
    for library_name in owtf_libraries:
        if library_name not in installed_libraries.keys():
            missing_libraries.append(library_name)

    # If there are missing libraries bail out :P
    if len(missing_libraries) > 0:
        print("The following python libraries seem missing : ")
        print("   %s\n" % (','.join(missing_libraries)))
        print("Haven't you run the install script? ")
        print("   %s\n" % ("python2 install/install.py"))
        print("If you are sure you ran the install script, "
              "install the missing libraries seperately")
        print("   %s\n" % ("pip install --upgrade -r install/owtf.pip"))
        exit(1)
