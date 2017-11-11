from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Mounts and/or uploads/downloads files to an SMB share -i.e. for IDS testing-"


def run(PluginInfo):
    Content = []
    plugin_params = ServiceLocator.get_component("plugin_params")
    config = ServiceLocator.get_component("config")
    smb = ServiceLocator.get_component("smb")

    args = {
        'Description': DESCRIPTION,
        'Mandatory': {
            'SMB_HOST': config.get_val('SMB_HOST_DESCRIP'),
            'SMB_SHARE': config.get_val('SMB_SHARE_DESCRIP'),
            'SMB_MOUNT_POINT': config.get_val('SMB_MOUNT_POINT_DESCRIP'),
        },
        'Optional': {
            'SMB_USER': config.get_val('SMB_USER_DESCRIP'),
            'SMB_PASS': config.get_val('SMB_PASS_DESCRIP'),
            'SMB_DOWNLOAD': config.get_val('SMB_DOWNLOAD_DESCRIP'),
            'SMB_UPLOAD': config.get_val('SMB_UPLOAD_DESCRIP'),
            'REPEAT_DELIM': config.get_val('REPEAT_DELIM_DESCRIP')
        }
    }

    for Args in plugin_params.get_args(args, PluginInfo):
        plugin_params.set_config(Args)  # Sets the auxiliary plugin arguments as config
        smb.Mount(Args, PluginInfo)
        smb.Transfer()
    if not smb.IsClosed():  # Ensure clean exit if reusing connection
        smb.UnMount(PluginInfo)
    return Content
