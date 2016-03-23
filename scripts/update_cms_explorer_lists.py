#!/usr/bin/env python
"""
2015/12/13 - Viyat Bhalodia (@delta24) - Updates CMS Explorer lists and merge them with original ones
"""
from __future__ import print_function
from lxml import html
import os
import urllib2

abs_path = os.path.dirname(os.path.abspath(__file__))
CMS_EXPLORER_DIR = os.path.join(abs_path, "../tools/restricted/cms-explorer/cms-explorer-1.0")


# get plugins from http://plugins.svn.wordpress.org
def get_plugins_wp():
    r = urllib2.Request("http://plugins.svn.wordpress.org")
    content = urllib2.urlopen(r)

    tree = html.fromstring(content.read())
    el_list = tree.find('body').find('ul').findall('li')
    plugins = []
    for el in el_list:
        plugins.append(el.text_content())

    with open("%s/wp_plugins.txt.new" % CMS_EXPLORER_DIR, "w+") as file:
        for plugin in plugins:
            file.write("wp-content/plugins/%s\n" % plugin.encode('ascii','ignore'))
    print("WP plugins list updated!")


def get_themes_wp():
    r = urllib2.Request("http://themes.svn.wordpress.org/")
    content = urllib2.urlopen(r)

    tree = html.fromstring(content.read())
    el_list = tree.find('body').find('ul').findall('li')
    themes = []
    for el in el_list:
        themes.append(el.text_content())

    with open("%s/wp_themes.txt.new" % CMS_EXPLORER_DIR, "w+") as file:
        for theme in themes:
            file.write("wp-content/themes/%s\n" % theme.encode('ascii','ignore'))
    print("WP themes list updated!")


def get_drupal_plugins():
    r = urllib2.Request("https://www.drupal.org/project/project_module/index")
    content = urllib2.urlopen(r)

    tree = html.fromstring(content.read())
    links = tree.xpath('//*[@id="block-system-main"]/div/div/div/div[2]/div/ol/li/div/span/a')
    modules = []

    for el in links:
        # lxml.etree.Element stores attributes in a dict interface
        string = el.get('href')
        module = string.replace("/project", "modules")
        modules.append(module)

    with open("%s/drupal_plugins.txt.new" % CMS_EXPLORER_DIR, "w+") as file:
        for module in modules:
            file.write("%s\n" % module.encode('ascii','ignore'))
    print("Drupal plugins list updated!")


def get_drupal_themes():
    r = urllib2.Request("https://www.drupal.org/project/project_theme/index")
    content = urllib2.urlopen(r)

    tree = html.fromstring(content.read())
    links = tree.xpath('//*[@id="block-system-main"]/div/div/div/div[2]/div/ol/li/div/span/a')
    themes = []
    for el in links:
        # lxml.etree.Element stores attributes in a dict interface
        string = el.get('href')
        theme = string.replace("/project", "themes")
        themes.append(theme)

    with open("%s/drupal_themes.txt.new" % CMS_EXPLORER_DIR, "w+") as file:
        for theme in themes:
            file.write('%s\n' % theme.encode('ascii','ignore'))
    print("Drupal themes list updated!")

if __name__ == '__main__':
    get_plugins_wp()
    get_themes_wp()
    get_drupal_plugins()
    get_drupal_themes()
