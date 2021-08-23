"""
owtf.api.handlers.config
~~~~~~~~~~~~~~~~~~~~~~~~

"""
from owtf.api.handlers.base import APIRequestHandler
from owtf.lib import exceptions
from owtf.lib.exceptions import APIError
from owtf.managers.config import get_all_config_dicts, update_config_val

__all__ = ["ConfigurationHandler"]


class ConfigurationHandler(APIRequestHandler):
    """Update framework settings and tool paths."""

    SUPPORTED_METHODS = ["GET", "PATCH"]

    def get(self):
        """Return all configuration items.

        **Example request**:

        .. sourcecode:: http

            GET /api/v1/configuration HTTP/1.1
            Accept: application/json

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json


            {
                "status": "success",
                "data": [
                    {
                        "dirty": false,
                        "key": "ATTACHMENT_NAME",
                        "descrip": "Filename for the attachment to be sent",
                        "section": "AUX_PLUGIN_DATA",
                        "value": "report"
                    },
                    {
                        "dirty": false,
                        "key": "BRUTEFORCER",
                        "descrip": "",
                        "section": "DICTIONARIES",
                        "value": "hydra"
                    },
                ]
            }
        """
        filter_data = dict(self.request.arguments)
        configurations = get_all_config_dicts(self.session, filter_data)
        grouped_configurations = {}
        for config in configurations:
            if config["section"] not in grouped_configurations:
                grouped_configurations[config["section"]] = []
            grouped_configurations[config["section"]].append(config)
        self.success(grouped_configurations)

    def patch(self):
        """Update configuration item

        **Example request**:

        .. sourcecode:: http

            PATCH /api/v1/configuration/ HTTP/1.1
            Accept: */*
            Content-Type: application/x-www-form-urlencoded; charset=UTF-8
            X-Requested-With: XMLHttpRequest

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json


            {
                "status": "success",
                "data": null
            }
        """
        for key, value_list in list(self.request.arguments.items()):
            try:
                update_config_val(self.session, key, value_list[0])
                self.success(None)
            except exceptions.InvalidConfigurationReference:
                raise APIError(422, "Invalid configuration item specified")
