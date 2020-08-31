"""
PASSIVE Plugin for Testing for Open Amazon S3 Buckets(OWASP-CL-001)
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "GrayhatWarfare for Public S3 Buckets"


def run(PluginInfo):
    resource = get_resources("PassiveOpenS3Buckets")

    # Grayhat Warfare works better when we use Second Level Domain to search
    domain = resource[0][1]
    # Extract Second Level Domain
    extract_sld = domain.rsplit(".", 1)
    # Replace it in the resource
    resource[0][1] = extract_sld[0]

    Content = plugin_helper.resource_linklist("Online Resources", resource)

    return Content
