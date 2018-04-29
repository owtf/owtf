"""
owtf.api.handlers.targets
~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from owtf.api.handlers.base import APIRequestHandler
from owtf.lib import exceptions
from owtf.lib.exceptions import InvalidTargetReference, APIError
from owtf.managers.target import (
    add_targets,
    delete_target,
    get_target_config_by_id,
    get_target_config_dicts,
    get_targets_by_severity_count,
    search_target_configs,
    update_target,
)

__all__ = ["TargetConfigSearchHandler", "TargetSeverityChartHandler", "TargetConfigHandler"]


class TargetConfigHandler(APIRequestHandler):
    """Manage target config data."""

    SUPPORTED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]

    def get(self, target_id=None):
        """Get target config data by id or fetch all target configs.

        **Example request**:

        .. sourcecode:: http

            GET /api/v1/targets/2 HTTP/1.1
            X-Requested-With: XMLHttpRequest

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json; charset=UTF-8

            {
                "status": "success",
                "data": {
                    "top_url": "https://google.com:443",
                    "top_domain": "com",
                    "target_url": "https://google.com",
                    "max_user_rank": 0,
                    "url_scheme": "https",
                    "host_path": "google.com",
                    "ip_url": "https://172.217.10.238",
                    "host_ip": "172.217.10.238",
                    "max_owtf_rank": -1,
                    "port_number": "443",
                    "host_name": "google.com",
                    "alternative_ips": "['172.217.10.238']",
                    "scope": true,
                    "id": 2
                }
            }
        """
        try:
            # If no target_id, means /target is accessed with or without filters
            if not target_id:
                # Get all filter data here, so that it can be passed
                filter_data = dict(self.request.arguments)
                self.success(get_target_config_dicts(self.session, filter_data))
            else:
                self.success(get_target_config_by_id(self.session, target_id))
        except InvalidTargetReference:
            raise APIError(400, "Invalid target reference provided")

    def post(self, target_id=None):
        """Add a target to the current session.

        **Example request**:

        .. sourcecode:: http

            POST /api/v1/targets/ HTTP/1.1
            Content-Type: application/x-www-form-urlencoded; charset=UTF-8
            X-Requested-With: XMLHttpRequest

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 201 Created
            Content-Length: 0
            Content-Type: application/json

            {
                "status": "success",
                "data": null
            }
        """
        if (target_id) or (not self.get_argument("target_url", default=None)):  # How can one post using an id xD
            raise APIError(400, "Incorrect query parameters")
        try:
            add_targets(self.session, dict(self.request.arguments)["target_url"])
            self.set_status(201)  # Stands for "201 Created"
            self.success(None)
        except exceptions.DBIntegrityException:
            raise APIError(400, "An unknown exception occurred when performing a DB operation")
        except exceptions.UnresolvableTargetException:
            raise APIError(400, "The target url can not be resolved")

    def put(self, target_id=None):
        return self.patch(target_id)

    def patch(self, target_id=None):
        """Update a target.

        **Example request**:

        .. sourcecode:: http

            PATCH /api/v1/targets/1 HTTP/1.1
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
        if not target_id or not self.request.arguments:
            raise APIError(400, "Incorrect query parameters")
        try:
            patch_data = dict(self.request.arguments)
            update_target(self.session, patch_data, id=target_id)
            self.success(None)
        except InvalidTargetReference:
            raise APIError(400, "Invalid target reference provided")

    def delete(self, target_id=None):
        """Delete a target.

        **Example request**:

        .. sourcecode:: http

            DELETE /api/v1/targets/4 HTTP/1.1
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
        if not target_id:
            raise APIError(400, "Missing target_id")
        try:
            delete_target(self.session, id=target_id)
            self.success(None)
        except InvalidTargetReference:
            raise APIError(400, "Invalid target reference provided")


class TargetConfigSearchHandler(APIRequestHandler):
    """Filter targets."""
    SUPPORTED_METHODS = ["GET"]

    def get(self):
        """Get target config data based on user filter.

        **Example request**:

        .. sourcecode:: http

            GET /api/v1/targets/search/?limit=100&offset=0&target_url=google HTTP/1.1
            Accept: application/json, text/javascript, */*; q=0.01
            X-Requested-With: XMLHttpRequest

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json; charset=UTF-8

            {
                "status": "success",
                "data": {
                    "records_total": 4,
                    "records_filtered": 2,
                    "data": [
                        {
                            "top_url": "https://google.com:443",
                            "top_domain": "com",
                            "target_url": "https://google.com",
                            "max_user_rank": -1,
                            "url_scheme": "https",
                            "host_path": "google.com",
                            "ip_url": "https://172.217.10.238",
                            "host_ip": "172.217.10.238",
                            "max_owtf_rank": -1,
                            "port_number": "443",
                            "host_name": "google.com",
                            "alternative_ips": "['172.217.10.238']",
                            "scope": true,
                            "id": 2
                        },
                        {
                            "top_url": "http://google.com:80",
                            "top_domain": "com",
                            "target_url": "http://google.com",
                            "max_user_rank": -1,
                            "url_scheme": "http",
                            "host_path": "google.com",
                            "ip_url": "http://172.217.10.238",
                            "host_ip": "172.217.10.238",
                            "max_owtf_rank": -1,
                            "port_number": "80",
                            "host_name": "google.com",
                            "alternative_ips": "['172.217.10.238']",
                            "scope": true,
                            "id": 1
                        }
                    ]
                }
            }
        """
        try:
            filter_data = dict(self.request.arguments)
            filter_data["search"] = True
            self.success(search_target_configs(self.session, filter_data=filter_data))
        except exceptions.InvalidParameterType:
            raise APIError(400, "Invalid parameter type provided")


class TargetSeverityChartHandler(APIRequestHandler):
    """Get targets with severity."""
    SUPPORTED_METHODS = ["GET"]

    def get(self):
        """Get data for target severity chart.

        **Example request**:

        .. sourcecode:: http

            GET /api/targets/severitychart/ HTTP/1.1
            X-Requested-With: XMLHttpRequest

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json; charset=UTF-8

            {
                "status": "success",
                "data": {
                    "data": [
                        {
                            "color": "#A9A9A9",
                            "id": 0,
                            "value": 100,
                            "label": "Not Ranked"
                        }
                    ]
                }
            }
        """
        try:
            self.success(get_targets_by_severity_count(self.session))
        except exceptions.InvalidParameterType:
            raise APIError(400, "Invalid parameter type provided")
