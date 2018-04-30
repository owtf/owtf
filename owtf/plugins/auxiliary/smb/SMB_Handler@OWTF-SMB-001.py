from owtf.config import config_handler
from owtf.plugin.params import plugin_params
from owtf.protocols.smb import SMB

DESCRIPTION = "Mounts and/or uploads/downloads files to an SMB share -i.e. for IDS testing-"


def run(PluginInfo):
    Content = []
    smb = SMB()
    args = {
        "Description": DESCRIPTION,
        "Mandatory": {
            "SMB_HOST": config_handler.get_val("SMB_HOST_DESCRIP"),
            "SMB_SHARE": config_handler.get_val("SMB_SHARE_DESCRIP"),
            "SMB_MOUNT_POINT": config_handler.get_val("SMB_MOUNT_POINT_DESCRIP"),
        },
        "Optional": {
            "SMB_USER": config_handler.get_val("SMB_USER_DESCRIP"),
            "SMB_PASS": config_handler.get_val("SMB_PASS_DESCRIP"),
            "SMB_DOWNLOAD": config_handler.get_val("SMB_DOWNLOAD_DESCRIP"),
            "SMB_UPLOAD": config_handler.get_val("SMB_UPLOAD_DESCRIP"),
            "REPEAT_DELIM": config_handler.get_val("REPEAT_DELIM_DESCRIP"),
        },
    }

    for args in plugin_params.get_args(args, PluginInfo):
        plugin_params.set_config(args)  # Sets the auxiliary plugin arguments as config
        smb.Mount(args, PluginInfo)
        smb.Transfer()
    if not smb.IsClosed():  # Ensure clean exit if reusing connection
        smb.UnMount(PluginInfo)
    return Content
