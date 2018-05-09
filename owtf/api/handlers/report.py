"""
owtf.api.handlers.report
~~~~~~~~~~~~~~~~~~~~~~~~

"""
import collections
from collections import defaultdict
from time import gmtime, strftime

from owtf.api.handlers.base import APIRequestHandler
from owtf.constants import RANKS, MAPPINGS, SUPPORTED_MAPPINGS
from owtf.lib import exceptions
from owtf.lib.exceptions import APIError
from owtf.managers.poutput import get_all_poutputs
from owtf.managers.target import get_target_config_by_id
from owtf.models.test_group import TestGroup
from owtf.utils.pycompat import iteritems


__all__ = ["ReportExportHandler"]


class ReportExportHandler(APIRequestHandler):
    """Class handling API methods related to export report funtionality.
    This API returns all information about a target scan present in OWTF.

    :raise InvalidTargetReference: If target doesn't exists.
    :raise InvalidParameterType: If some unknown parameter in `filter_data`.
    """

    SUPPORTED_METHODS = ["GET"]

    def get(self, target_id=None):
        """Returns JSON(data) for the template.

        **Example request**:

        .. sourcecode:: http

            GET /api/v1/targets/2/export HTTP/1.1
            Accept: application/json

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "success",
                "data": {
                    "top_url": "https://google.com:443",
                    "top_domain": "com",
                    "target_url": "https://google.com",
                    "time": "2018-04-03 09:21:27",
                    "max_user_rank": -1,
                    "url_scheme": "https",
                    "host_path": "google.com",
                    "ip_url": "https://104.28.0.9",
                    "host_ip": "104.28.0.9",
                    "vulnerabilities": [],
                    "max_owtf_rank": -1,
                    "port_number": "443",
                    "host_name": "google.com",
                    "alternative_ips": "['104.28.1.9']",
                    "scope": true,
                    "id": 2
                }
            }
        """
        if not target_id:
            raise APIError(400, "Missing target id")
        try:
            filter_data = dict(self.request.arguments)
            plugin_outputs = get_all_poutputs(filter_data, target_id=target_id, inc_output=True)
        except exceptions.InvalidTargetReference:
            raise APIError(400, "Invalid target reference provided")
        except exceptions.InvalidParameterType:
            raise APIError(400, "Invalid parameter type provided")
        # Group the plugin outputs to make it easier in template
        grouped_plugin_outputs = defaultdict(list)
        for output in plugin_outputs:
            output["rank"] = RANKS.get(max(output["user_rank"], output["owtf_rank"]))
            grouped_plugin_outputs[output["plugin_code"]].append(output)

        # Needed ordered list for ease in templates
        grouped_plugin_outputs = collections.OrderedDict(sorted(grouped_plugin_outputs.items()))

        # Get mappings
        mapping_type = self.get_argument("mapping", None)
        mappings = {}
        if mapping_type and mapping_type in SUPPORTED_MAPPINGS:
            for k, v in iteritems(MAPPINGS):
                if v.get(mapping_type, None) is not None:
                    mappings[k] = v[mapping_type]

        # Get test groups as well, for names and info links
        test_groups = {}
        for test_group in TestGroup.get_all(self.session):
            test_group["mapped_code"] = test_group["code"]
            test_group["mapped_descrip"] = test_group["descrip"]
            if mappings and test_group["code"] in mappings:
                code, description = mappings[test_group["code"]]
                test_group["mapped_code"] = code
                test_group["mapped_descrip"] = description
            test_groups[test_group["code"]] = test_group

        vulnerabilities = []
        for key, value in list(grouped_plugin_outputs.items()):
            test_groups[key]["data"] = value
            vulnerabilities.append(test_groups[key])

        result = get_target_config_by_id(target_id)
        result["vulnerabilities"] = vulnerabilities
        result["time"] = strftime("%Y-%m-%d %H:%M:%S", gmtime())

        if result:
            self.success(result)
        else:
            raise APIError(500, "No config object exists for the given target")
