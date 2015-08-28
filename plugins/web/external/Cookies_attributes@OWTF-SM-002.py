from framework.dependency_management.dependency_resolver import ServiceLocator
import string, re
import cgi

DESCRIPTION = "Cookie Attributes Plugin to assist manual testing"

def run(PluginInfo):
  #ServiceLocator.get_component("config").Show()
  Content = ServiceLocator.get_component("plugin_helper").ResourceLinkList('Online Hash Cracking Resources', ServiceLocator.get_component("resource").GetResources('ExternalCookiesAttributes'))
  return Content
