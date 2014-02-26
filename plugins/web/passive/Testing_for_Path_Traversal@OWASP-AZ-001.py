def run(Core, PluginInfo):
        #Core.Config.Show()
        Content = Core.PluginHelper.DrawSuggestedCommandBox( PluginInfo, [ [ 'All', 'Testing_for_Path_Traversal_All' ]  ], 'Testing_for_Path_Traversal - Potentially useful commands' )
        return Content
