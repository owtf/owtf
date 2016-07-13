from framework.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Mounts and/or uploads/downloads files to an SMB share -i.e. for IDS testing-"


def run(PluginInfo):
    Content = []
    plugin_params = ServiceLocator.get_component("plugin_params")
    config = ServiceLocator.get_component("config")
    smb = ServiceLocator.get_component("smb")

    args = {
        'Description': DESCRIPTION,
        'Mandatory': {
            'SMB_HOST': config.FrameworkConfigGet('SMB_HOST_DESCRIP'),
            'SMB_SHARE': config.FrameworkConfigGet('SMB_SHARE_DESCRIP'),
            'SMB_MOUNT_POINT': config.FrameworkConfigGet('SMB_MOUNT_POINT_DESCRIP'),
        },
        'Optional': {
            'SMB_USER': config.FrameworkConfigGet('SMB_USER_DESCRIP'),
            'SMB_PASS': config.FrameworkConfigGet('SMB_PASS_DESCRIP'),
            'SMB_DOWNLOAD': config.FrameworkConfigGet('SMB_DOWNLOAD_DESCRIP'),
            'SMB_UPLOAD': config.FrameworkConfigGet('SMB_UPLOAD_DESCRIP'),
            'REPEAT_DELIM': config.FrameworkConfigGet('REPEAT_DELIM_DESCRIP')
        }
    }

    for Args in plugin_params.GetArgs(args, PluginInfo):
        plugin_params.SetConfig(Args)  # Sets the auxiliary plugin arguments as config
        smb.Mount(Args, PluginInfo)
        smb.Transfer()
    if not smb.IsClosed():  # Ensure clean exit if reusing connection
        smb.UnMount(PluginInfo)
    return Content
