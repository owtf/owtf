from framework.dependency_management.dependency_resolver import ServiceLocator

DESCRIPTION = "Mounts and/or uploads/downloads files to an SMB share -i.e. for IDS testing-"


def run(PluginInfo):
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
