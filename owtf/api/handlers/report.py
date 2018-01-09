"""
owtf.api.handlers.report
~~~~~~~~~~~~~~~~~~~~~

"""

import collections
import logging
from collections import defaultdict
from time import gmtime, strftime

import tornado.gen
import tornado.httpclient
import tornado.web

from owtf.api.handlers.base import APIRequestHandler
from owtf.constants import RANKS
from owtf.lib import exceptions
from owtf.managers.mapping import get_mappings
from owtf.managers.plugin import get_all_test_groups
from owtf.managers.poutput import get_all_poutputs
from owtf.managers.target import get_target_config_by_id


class ReportExportHandler(APIRequestHandler):
    """
    Class handling API methods related to export report funtionality.
    This API returns all information about a target scan present in OWTF.
    :raise InvalidTargetReference: If target doesn't exists.
    :raise InvalidParameterType: If some unknown parameter in `filter_data`.
    """
    # TODO: Add API documentation.

    SUPPORTED_METHODS = ['GET']

    def get(self, target_id=None):
        """
        REST API - /api/targets/<target_id>/export/ returns JSON(data) for template.
        """
        if not target_id:
            raise tornado.web.HTTPError(400)
        try:
            filter_data = dict(self.request.arguments)
            plugin_outputs = get_all_poutputs(filter_data, target_id=target_id, inc_output=True)
        except exceptions.InvalidTargetReference as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)
        # Group the plugin outputs to make it easier in template
        grouped_plugin_outputs = defaultdict(list)
        for output in plugin_outputs:
            output['rank'] = RANKS.get(max(output['user_rank'], output['owtf_rank']))
            grouped_plugin_outputs[output['plugin_code']].append(output)

        # Needed ordered list for ease in templates
        grouped_plugin_outputs = collections.OrderedDict(sorted(grouped_plugin_outputs.items()))

        # Get mappings
        mappings = self.get_argument("mapping", None)
        if mappings:
            mappings = get_mappings(self.session, mappings)

        # Get test groups as well, for names and info links
        test_groups = {}
        for test_group in get_all_test_groups(self.session):
            test_group["mapped_code"] = test_group["code"]
            test_group["mapped_descrip"] = test_group["descrip"]
            if mappings and test_group['code'] in mappings:
                code, description = mappings[test_group['code']]
                test_group["mapped_code"] = code
                test_group["mapped_descrip"] = description
            test_groups[test_group['code']] = test_group

        vulnerabilities = []
        for key, value in list(grouped_plugin_outputs.items()):
            test_groups[key]["data"] = value
            vulnerabilities.append(test_groups[key])

        result = get_target_config_by_id(target_id)
        result["vulnerabilities"] = vulnerabilities
        result["time"] = strftime("%Y-%m-%d %H:%M:%S", gmtime())

        if result:
            self.write(result)
        else:
            raise tornado.web.HTTPError(400)
