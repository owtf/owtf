"""
owtf.api.handlers.test_group
~~~~~~~~~~~~~~~~~~~~~~~~

"""


from owtf.api.handlers.base import APIRequestHandler
from owtf.models.plugin import Plugin
from owtf.models.test_group import TestGroup
from owtf.lib.exceptions import APIError
from owtf.managers.plugin import get_plugins_by_group


__all__ = ["GroupDataHandler"]


class GroupDataHandler(APIRequestHandler):
    """Get completed plugin output data from the DB."""

    SUPPORTED_METHODS = ["POST"]

    
    def post(self, action):
        """Create a new plugin group.

        **Example request**:

        .. sourcecode:: http

            POST /api/v1/group/add HTTP/1.1
            Accept: application/json
            accept-language: en-US,en;q=0.9,
            cache-control: no-cache,
            content-type: application/x-www-form-urlencoded;charset=UTF-8,
            pragma: no-cache

            plugin_data: group=network%3Btest&type=active&code=PTES-001&id=3


         **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Encoding: gzip
            Vary: Accept-Encoding
            Content-Type: application/json


            {
                "status": "success", 
                "data": "net;test"
            }


        """     
        plugin_data = self.get_argument("plugin_data", default=None)
        if action == "add":
            plugin_data_list = plugin_data.split("&")
            plugin_dict = {}
            for plugin_element in plugin_data_list:
                plugin_dict[plugin_element.split("=")[0]] = plugin_element.split("=")[1]
            custom_group_name = plugin_dict['group'].split('%3B')[-1]
            
            code_or_key = plugin_dict['type']+"@"+plugin_dict['code']
            plugin_query_code = plugin_dict['code']

            plugin = self.session.query(Plugin).filter(Plugin.key==code_or_key)
            existing_plugin_group = plugin.value(Plugin.group).replace("%3B",";")
            existing_plugin_group_list = existing_plugin_group.split(";")
            
            if len(existing_plugin_group_list) > 1:
                if custom_group_name in existing_plugin_group:
                    self.session.commit()
                    self.success(plugin.value(TestGroup.group))
                else:
                    new_group_string = f"{existing_plugin_group};{custom_group_name}"
                    plugin.update({Plugin.group:new_group_string},synchronize_session=False)

                    test_group = self.session.query(TestGroup).filter(TestGroup.code==plugin_query_code)
                    test_group.update({TestGroup.group:test_group.value(TestGroup.group)+";"+custom_group_name})
                    self.session.commit()
                    self.success(test_group.value(TestGroup.group))
            else:
                new_group_string = f"{existing_plugin_group};{custom_group_name}"
                plugin.update({Plugin.group:new_group_string},synchronize_session=False)

                test_group = self.session.query(TestGroup).filter(TestGroup.code==plugin_query_code)
                plugin_group_value_list = test_group.value(TestGroup.group).split(";")
                if custom_group_name not in plugin_group_value_list:
                    test_group.update({TestGroup.group:test_group.value(TestGroup.group)+";"+custom_group_name})
                self.session.commit()
                self.success(test_group.value(TestGroup.group))
        elif action == "delete":
            default_groups = ["network","auxillary","web"]
            plugin_data = plugin_data.split("=")
            if plugin_data[0] == "group":
                if "%" in plugin_data[1]:
                    groups = plugin_data[1].split('%2C')
                    for group in groups:
                        if group in default_groups:
                            continue

                        plugins = get_plugins_by_group(self.session,[group])

                        for plugin in plugins:

                            queried_plugin = self.session.query(Plugin).filter(Plugin.key==plugin['type']+"@"+plugin['code'])
                            queried_test_group = self.session.query(TestGroup).filter(TestGroup.code==plugin['code'])
                            
                            plugin_value_list = queried_plugin.value(Plugin.group).split(';')
                            plugin_value_list.remove(group)
                            queried_plugin.update({Plugin.group:";".join(plugin_value_list)})

                            plugin_group_value_list = queried_test_group.value(TestGroup.group).split(';')
                            plugin_group_value_list.remove(group)
                            queried_test_group.update({TestGroup.group:";".join(plugin_group_value_list)})
                            
                else:
                    group = plugin_data[1]
                    if group not in default_groups:
                        plugins = get_plugins_by_group(self.session,[group])
                        for plugin in plugins:
                            queried_plugin = self.session.query(Plugin).filter(Plugin.key==plugin['type']+"@"+plugin['code'])
                            queried_test_group = self.session.query(TestGroup).filter(TestGroup.code==plugin['code'])
                            
                            plugin_value_list = queried_plugin.value(Plugin.group).split(';')
                            if group in plugin_value_list:
                                plugin_value_list.remove(group)
                                queried_plugin.update({Plugin.group:";".join(plugin_value_list)})

                            plugin_group_value_list = queried_test_group.value(TestGroup.group).split(';')
                            if group in plugin_group_value_list:
                                plugin_group_value_list.remove(group)
                                queried_test_group.update({TestGroup.group:";".join(plugin_group_value_list)})
                            
            else:
                raise APIError(404,"Cannot delete type")
            self.session.commit()
            self.success("Group deleted")