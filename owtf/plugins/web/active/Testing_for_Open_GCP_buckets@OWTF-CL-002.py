"""
ACTIVE Plugin for Testing for Open GCP Buckets(OWASP-CL-002)
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "GCPBucketBrute for Open GCP Buckets"


def run(PluginInfo):
    resource = get_resources("ActiveOpenGCPBuckets")

    # GCPBrute works better when we use Second Level Domain]
    domain = resource[0][1]
    # Extract Second Level Domain
    extract_sld = domain.rsplit(".", 1)
    # Replace it in the resource
    resource[0][1] = extract_sld[0]

    Content = plugin_helper.CommandDump(
        "Test Command", "Output", resource, PluginInfo, []
    )
    return resource
