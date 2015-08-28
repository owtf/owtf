#!/usr/bin/env python
'''
The DB stores HTTP transactions, unique URLs and more.
'''
from framework.dependency_management.dependency_resolver import BaseComponent
from framework.dependency_management.interfaces import URLManagerInterface
from framework.lib.exceptions import InvalidParameterType
from framework.lib.general import *
from framework.db.target_manager import target_required
from framework.db import models
import re
import logging


class URLManager(BaseComponent, URLManagerInterface):
    NumURLsBefore = 0

    COMPONENT_NAME = "url_manager"

    def __init__(self):
        self.register_in_service_locator()
        self.config = self.get_component("config")
        self.target = self.get_component("target")
        self.db = self.get_component("db")
        # Compile regular expressions once at the beginning for speed purposes:
        self.IsFileRegexp = re.compile(self.config.FrameworkConfigGet('REGEXP_FILE_URL'), re.IGNORECASE)
        self.IsSmallFileRegexp = re.compile(self.config.FrameworkConfigGet('REGEXP_SMALL_FILE_URL'), re.IGNORECASE)
        self.IsImageRegexp = re.compile(self.config.FrameworkConfigGet('REGEXP_IMAGE_URL'), re.IGNORECASE)
        self.IsURLRegexp = re.compile(self.config.FrameworkConfigGet('REGEXP_VALID_URL'), re.IGNORECASE)
        self.IsSSIRegexp = re.compile(self.config.FrameworkConfigGet('REGEXP_SSI_URL'), re.IGNORECASE)

    def IsRegexpURL(self, URL, Regexp):
        return len(Regexp.findall(URL)) > 0

    def IsSmallFileURL(self, URL):
        return self.IsRegexpURL(URL, self.IsSmallFileRegexp)

    def IsFileURL(self, URL):
        return self.IsRegexpURL(URL, self.IsFileRegexp)

    def IsImageURL(self, URL):
        return self.IsRegexpURL(URL, self.IsImageRegexp)

    def IsSSIURL(self, URL):
        return self.IsRegexpURL(URL, self.IsSSIRegexp)
    @target_required
    def AddURLToDB(self, url, visited, found=None, target_id=None):
        if self.IsURL(url):  # New URL
            # Make sure URL is clean prior to saving in DB, nasty bugs
            # can happen without this
            url = url.strip()
            scope = self.target.IsInScopeURL(url)
            self.db.session.merge(models.Url(
                target_id=target_id,
                url=url,
                visited=visited,
                scope=scope))
            self.db.session.commit()

    def GetURLsToVisit(self, target=None):
        urls = self.db.session.query(models.Url.url).filter_by(visited=False).all()
        urls = [i[0] for i in urls]
        return (urls)

    def IsURL(self, URL):
        return self.IsRegexpURL(URL, self.IsURLRegexp)

    @target_required
    def AddURL(self, url, found=None, target_id=None):
        """
        Adds a URL to the relevant DBs if not already added
        """
        visited = False
        if found is not None:  # Visited URL -> Found in [ True, False ]
            visited = True
        return self.AddURLToDB(url, visited, found=found, target_id=target_id)

    @target_required
    def ImportProcessedURLs(self, urls_list, target_id=None):
        for url, visited, scope in urls_list:
            self.db.session.merge(models.Url(
                target_id=target_id,
                url=url,
                visited=visited,
                scope=scope))
        self.db.session.commit()

    @target_required
    def ImportURLs(self, url_list, target_id=None):
        """
        Extracts and classifies all URLs passed. Expects a newline separated
        URL list
        """
        imported_urls = []

        for url in url_list:
            if self.IsURL(url):
                imported_urls.append(url)
                self.db.session.merge(models.Url(url=url, target_id=target_id))
        self.db.session.commit()
        return(imported_urls)  # Return imported urls

# ------------------------------- API Methods--------------------------------
    def DeriveUrlDict(self, url_obj):
        udict = dict(url_obj.__dict__)
        udict.pop("_sa_instance_state")
        return udict

    def DeriveUrlDicts(self, url_obj_list):
        dict_list = []
        for url_obj in url_obj_list:
            dict_list.append(self.DeriveUrlDict(url_obj))
        return dict_list

    def GenerateQueryUsingSession(
            self,
            criteria,
            target_id,
            for_stats=False):
        query = self.db.session.query(models.Url).filter_by(target_id=target_id)
        # Check if criteria is url search
        if criteria.get('search', None):
            if criteria.get('url', None):
                if isinstance(criteria.get('url'), list):
                    criteria['url'] = criteria['url'][0]
                query = query.filter(models.Url.url.like(
                    '%'+criteria['url']+'%'))
        else:  # If not search
            if criteria.get('url', None):
                if isinstance(criteria.get('url'), (str, unicode)):
                    query = query.filter_by(url=criteria['url'])
                if isinstance(criteria.get('url'), list):
                    query = query.filter(
                        models.Url.url.in_(criteria['url']))
        # For the following section doesn't matter if filter/search because
        # it doesn't make sense to search in a boolean column :P
        if criteria.get('visited', None):
            if isinstance(criteria.get('visited'), list):
                criteria['visited'] = criteria['visited'][0]
            query = query.filter_by(
                visited=self.config.ConvertStrToBool(criteria['visited']))
        if criteria.get('scope', None):
            if isinstance(criteria.get('scope'), list):
                criteria['scope'] = criteria['scope'][0]
            query = query.filter_by(
                scope=self.config.ConvertStrToBool(criteria['scope']))
        if not for_stats:  # Query for stats can't have limit and offset
            try:
                if criteria.get('offset', None):
                    if isinstance(criteria.get('offset'), list):
                        criteria['offset'] = criteria['offset'][0]
                    query = query.offset(int(criteria['offset']))
                if criteria.get('limit', None):
                    if isinstance(criteria.get('limit'), list):
                        criteria['limit'] = criteria['limit'][0]
                    query = query.limit(int(criteria['limit']))
            except ValueError:
                raise InvalidParameterType("Invalid parameter type for transaction db")
        return query

    @target_required
    def GetAll(self, Criteria, target_id=None):
        query = self.GenerateQueryUsingSession(
            Criteria,
            target_id)
        results = query.all()
        return(self.DeriveUrlDicts(results))

    @target_required
    def SearchAll(self, Criteria, target_id=None):

        # Three things needed
        # + Total number of urls
        # + Filtered url
        # + Filtered number of url
        total = self.db.session.query(
            models.Url).filter_by(target_id=target_id).count()
        filtered_url_objs = self.GenerateQueryUsingSession(
            Criteria,
            target_id).all()
        filtered_number = self.GenerateQueryUsingSession(
            Criteria,
            target_id,
            for_stats=True).count()
        return({
            "records_total": total,
            "records_filtered": filtered_number,
            "data": self.DeriveUrlDicts(
                filtered_url_objs)
        })
