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
from framework.db import models
import logging
import re

class URLManager:
        NumURLsBefore = 0

        def __init__(self, Core):
                self.Core = Core
                # Compile regular expressions once at the beginning for speed purposes:
                self.IsFileRegexp = re.compile(Core.Config.FrameworkConfigGet('REGEXP_FILE_URL'), re.IGNORECASE)
                self.IsSmallFileRegexp = re.compile(Core.Config.FrameworkConfigGet('REGEXP_SMALL_FILE_URL'), re.IGNORECASE)
                self.IsImageRegexp = re.compile(Core.Config.FrameworkConfigGet('REGEXP_IMAGE_URL'), re.IGNORECASE)
                self.IsURLRegexp = re.compile(Core.Config.FrameworkConfigGet('REGEXP_VALID_URL'), re.IGNORECASE)
                self.IsSSIRegexp = re.compile(Core.Config.FrameworkConfigGet('REGEXP_SSI_URL'), re.IGNORECASE)

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

        def GetURLsToVisit(self, target = None):
            Session = self.Core.DB.Target.GetUrlDBSession(target)
            session = Session()
            urls = session.query(models.Url.url).filter_by(visited = False).all()
            session.close()
            urls = [i[0] for i in urls]
            return(urls)

        def IsURL(self, URL):
                return self.IsRegexpURL(URL, self.IsURLRegexp)

        def GetNumURLs(self):
            #return self.Core.DB.GetLength(DBPrefix+'ALL_URLS_DB')
            Session = self.Core.DB.Target.GetUrlDBSession()
            session = Session()
            count = session.query(models.Url).count()
            session.close()
            return(count)

        def AddURLToDB(self, url, visited, found = None, target = None):
            Message = ''
            if self.IsURL(url): # New URL
                url = url.strip() # Make sure URL is clean prior to saving in DB, nasty bugs can happen without this
                scope =  self.Core.DB.Target.IsInScopeURL(url)
                Session = self.Core.DB.Target.GetUrlDBSession()
                session = Session()
                session.merge(models.Url(url = url, visited = visited, scope = scope))
                session.commit()
                session.close()
            return Message

        def AddURL(self, url, found = None, target = None): # Adds a URL to the relevant DBs if not already added
                visited = False
                if found != None: # Visited URL -> Found in [ True, False ]
                    visited = True
                return self.AddURLToDB(url, visited, found = found, target = target)

        def AddURLsStart(self):
                self.NumURLsBefore = self.GetNumURLs()

        def AddURLsEnd(self):
                NumURLsAfter = self.GetNumURLs()
                Message = str(NumURLsAfter-self.NumURLsBefore)+" URLs have been added and classified"
                log(Message)
                return(NumURLsAfter - self.NumURLsBefore) #Message

        def ImportProcessedURLs(self, urls_list, target_id = None):
            Session = self.Core.DB.Target.GetUrlDBSession(target_id)
            session = Session()
            for url, visited, scope in urls_list:
                session.merge(models.Url(url = url, visited = visited, scope = scope))
                log("Added " + url + " to URLs DB")
            session.commit()
            session.close()

        def ImportURLs(self, url_list, target = None): # Extracts and classifies all URLs passed. Expects a newline separated URL list
            imported_urls = []
            self.AddURLsStart()
            Session = self.Core.DB.Target.GetUrlDBSession(target)
            session = Session()
            for url in url_list:
                if self.IsURL(url):
                    imported_urls.append(url)
                    session.merge(models.Url(url = url))
            session.commit()
            session.close()
            count = self.AddURLsEnd()
            Message = str(count)+" URLs have been added and classified"
            return(imported_urls)  # Return imported urls

#-------------------------------------------------- API Methods --------------------------------------------------
        def DeriveUrlDict(self, url_obj):
            udict = dict(url_obj.__dict__)
            udict.pop("_sa_instance_state")
            return udict

        def DeriveUrlDicts(self, url_obj_list):
            dict_list = []
            for url_obj in url_obj_list:
                dict_list.append(self.DeriveUrlDict(url_obj))
            return dict_list

        def GenerateQueryUsingSession(self, session, Criteria):
            query = session.query(models.Url)
            if Criteria.get('url', None):
                if isinstance(Criteria.get('url'), (str, unicode)):
                    query = query.filter_by(url = Criteria['url'])
                if isinstance(Criteria.get('url'), list):
                    query = query.filter(models.Url.url.in_(Criteria['url']))
            if Criteria.get('visited', None):
                if isinstance(Criteria.get('visited'), list):
                    Criteria['visited'] = Criteria['visited'][0]
                query = query.filter_by(visited = self.Core.Config.ConvertStrToBool(Criteria['url']))
            if Criteria.get('scope', None):
                if isinstance(Criteria.get('scope'), list):
                    Criteria['scope'] = Criteria['scope'][0]
                query = query.filter_by(scope = self.Core.Config.ConvertStrToBool(Criteria['scope']))
            return query

        def GetAll(self, Criteria, target_id = None):
            Session = self.Core.DB.Target.GetUrlDBSession(target_id)
            session = Session()
            query = self.GenerateQueryUsingSession(session, Criteria)
            results = query.all()
            return(self.DeriveUrlDicts(results))
