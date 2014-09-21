from framework.dependency_management.dependency_resolver import ServiceLocator

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
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

DESCRIPTION = "Mounts and/or uploads/downloads files to an SMB share -i.e. for IDS testing-"


def run(Core, PluginInfo):
    # ServiceLocator.get_component("config").Show()
    Content = DESCRIPTION + " Results:<br />"
    Iteration = 1  # Iteration counter initialisation
    plugin_params = ServiceLocator.get_component("plugin_params")
    config = ServiceLocator.get_component("config")
    smb = ServiceLocator.get_component("smb")
    for Args in plugin_params.GetArgs({
                                                                          'Description': DESCRIPTION,
                                                                          'Mandatory': {
                                                                              'SMB_HOST': config.Get('SMB_HOST_DESCRIP'),
                                                                              'SMB_SHARE': config.Get(
                                                                                      'SMB_SHARE_DESCRIP'),
                                                                              'SMB_MOUNT_POINT': config.Get(
                                                                                      'SMB_MOUNT_POINT_DESCRIP'),
                                                                          },
                                                                          'Optional': {
                                                                              'SMB_USER': config.Get('SMB_USER_DESCRIP'),
                                                                              'SMB_PASS': config.Get('SMB_PASS_DESCRIP'),
                                                                              'SMB_DOWNLOAD': config.Get(
                                                                                      'SMB_DOWNLOAD_DESCRIP'),
                                                                              'SMB_UPLOAD': config.Get(
                                                                                      'SMB_UPLOAD_DESCRIP'),
                                                                              'REPEAT_DELIM': config.Get(
                                                                                      'REPEAT_DELIM_DESCRIP')
                                                                          }}, PluginInfo):
        plugin_params.SetConfig(Args)  # Sets the aux plugin arguments as config
        smb.Mount(Args, PluginInfo)
        smb.Transfer()
    if not smb.IsClosed():  # Ensure clean exit if reusing connection
        smb.UnMount(PluginInfo)
    return Content