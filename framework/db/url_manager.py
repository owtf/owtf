#!/usr/bin/env python
'''
owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the copyright owner nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The DB stores HTTP transactions, unique URLs and more.
'''
from framework.lib.general import *
from framework.db.target_manager import target_required
from framework.db import models
import re
import logging


class URLManager:
    def __init__(self, Core):
        self.Core = Core
        # Compile regular expressions once at the beginning for speed purposes:
        self.IsFileRegexp = re.compile(
            Core.Config.FrameworkConfigGet('REGEXP_FILE_URL'),
            re.IGNORECASE)
        self.IsSmallFileRegexp = re.compile(
            Core.Config.FrameworkConfigGet('REGEXP_SMALL_FILE_URL'),
            re.IGNORECASE)
        self.IsImageRegexp = re.compile(
            Core.Config.FrameworkConfigGet('REGEXP_IMAGE_URL'),
            re.IGNORECASE)
        self.IsURLRegexp = re.compile(
            Core.Config.FrameworkConfigGet('REGEXP_VALID_URL'),
            re.IGNORECASE)
        self.IsSSIRegexp = re.compile(
            Core.Config.FrameworkConfigGet('REGEXP_SSI_URL'),
            re.IGNORECASE)

    def IsRegexpURL(self, URL, Regexp):
        if len(Regexp.findall(URL)) > 0:
                return True
        return False

    def IsSmallFileURL(self, URL):
        return self.IsRegexpURL(URL, self.IsSmallFileRegexp)

    def IsFileURL(self, URL):
        return self.IsRegexpURL(URL, self.IsFileRegexp)

    def IsImageURL(self, URL):
        return self.IsRegexpURL(URL, self.IsImageRegexp)

    def IsSSIURL(self, URL):
        return self.IsRegexpURL(URL, self.IsSSIRegexp)

    def GetURLsToVisit(self, target_id=None):
        if target_id is None:
            target_id = self.Core.DB.Target.GetTargetID()
        urls = self.Core.DB.session.query(models.Url.url).filter_by(
            target_id=target_id,
            visited=False).all()
        urls = [i[0] for i in urls]
        return(urls)

    def IsURL(self, URL):
        return self.IsRegexpURL(URL, self.IsURLRegexp)

    @target_required
    def AddURLToDB(self, url, visited, found=None, target_id=None):
        if self.IsURL(url):  # New URL
            # Make sure URL is clean prior to saving in DB, nasty bugs
            # can happen without this
            url = url.strip()
            scope = self.Core.DB.Target.IsInScopeURL(url)

            self.Core.DB.session.merge(models.Url(
                target_id=target_id,
                url=url,
                visited=visited,
                scope=scope))
            self.Core.DB.session.commit()

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
            self.Core.DB.session.merge(models.Url(
                target_id=target_id,
                url=url,
                visited=visited,
                scope=scope))
        self.Core.DB.session.commit()

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
                self.Core.DB.session.merge(models.Url(url=url, target_id=target_id))
        self.Core.DB.session.commit()
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
        query = self.Core.DB.session.query(models.Url).filter_by(target_id=target_id)
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
                visited=self.Core.Config.ConvertStrToBool(criteria['visited']))
        if criteria.get('scope', None):
            if isinstance(criteria.get('scope'), list):
                criteria['scope'] = criteria['scope'][0]
            query = query.filter_by(
                scope=self.Core.Config.ConvertStrToBool(criteria['scope']))
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
                raise InvalidParameterType(
                    "Invalid parameter type for transaction db")
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
        total = self.Core.DB.session.query(
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
