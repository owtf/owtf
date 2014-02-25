DESCRIPTION = "Local File Inclusion Vulnerability Scanning with Panoptic"
def run(Core, PluginInfo):
    #Core.Config.Show()
    return Core.PluginHelper.DrawCommandDump('Test Command', 'Output', Core.Config.GetResources('Testing_for_Path_Traversal'), PluginInfo,"")
