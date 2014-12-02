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

The DB stores worklist
'''
from framework.db import models
from framework.lib import exceptions
from sqlalchemy import exc
from sqlalchemy.sql import not_
import logging


class WorklistManager(object):
    def __init__(self, Core):
        self.Core = Core

    def _generate_query(self, criteria=None, for_stats=False):
        if criteria is None:
            criteria = {}
        query = self.Core.DB.session.query(models.Work).join(
            models.Target).join(models.Plugin).order_by(models.Work.id)
        if criteria.get('search', None):
            if criteria.get('target_url', None):
                if isinstance(criteria.get('target_url'), list):
                    criteria['target_url'] = criteria['target_url'][0]
                query = query.filter(models.Target.target_url.like(
                    '%'+criteria['target_url']+'%'))
            if criteria.get('type', None):
                if isinstance(criteria.get('type'), list):
                    criteria['type'] = criteria['type'][0]
                query = query.filter(models.Plugin.type.like(
                    '%'+criteria['type']+'%'))
            if criteria.get('group', None):
                if isinstance(criteria.get('group'), list):
                    criteria['group'] = criteria['group'][0]
                query = query.filter(models.Plugin.group.like(
                    '%'+criteria['group']+'%'))
            if criteria.get('name', None):
                if isinstance(criteria.get('name'), list):
                    criteria['name'] = criteria['name'][0]
                query = query.filter(models.Plugin.name.ilike(
                    '%'+criteria['name']+'%'))
        try:
            if criteria.get('id', None):
                if isinstance(criteria.get('id'), list):
                    query = query.filter(
                        models.Work.target_id.in_(criteria.get('id')))
                if isinstance(criteria.get('id'), (str, unicode)):
                    query = query.filter_by(
                        target_id == int(criteria.get('id')))
            if not for_stats:
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
        return(query)

    def _derive_work_dict(self, work_model):
        if work_model is not None:
            wdict = {}
            wdict["target"] = self.Core.DB.Target.DeriveTargetConfig(
                work_model.target)
            wdict["plugin"] = self.Core.DB.Plugin.DerivePluginDict(
                work_model.plugin)
            wdict["id"] = work_model.id
            wdict["active"] = work_model.active
            return wdict

    def _derive_work_dicts(self, work_models):
        results = []
        for work_model in work_models:
            if work_model is not None:
                results.append(
                    self._derive_work_dict(work_model))
        return results

    def get_total_work_count(self):
        return self.Core.DB.session.query(models.Work).filter_by(
            active=True).count()

    def get_work(self, in_use_target_list):
        query = self.Core.DB.session.query(models.Work).filter_by(
            active=True).order_by(models.Work.id)
        if len(in_use_target_list) > 0:
            query = query.filter(
                not_(models.Work.target_id.in_(in_use_target_list)))
        work_obj = query.first()
        if work_obj:
            # First get the worker dict and then delete
            work_dict = self._derive_work_dict(work_obj)
            self.Core.DB.session.delete(work_obj)
            self.Core.DB.session.commit()
            return((work_dict["target"], work_dict["plugin"]))

    def get_all(self, criteria=None):
        query = self._generate_query(criteria)
        works = query.all()
        return(self._derive_work_dicts(works))

    def get(self, work_id):
        work = self.Core.DB.session.query(models.Work).get(work_id)
        if work is None:
            raise exceptions.InvalidWorkReference(
                "No work with id " + str(work_id))
        return(self._derive_work_dict(work))

    def add_work(self, target_list, plugin_list, force_overwrite=False):
        for target in target_list:
            for plugin in plugin_list:
                # Check if it already in worklist
                if self.Core.DB.session.query(models.Work).filter_by(
                        target_id=target["id"],
                        plugin_key=plugin["key"]).count() == 0:
                    # Check if it is already run ;) before adding
                    if ((force_overwrite is True) or
                        (force_overwrite is False and
                            self.Core.DB.POutput.PluginAlreadyRun(
                                plugin, target_id=target["id"]) is False)):
                        # If force overwrite is true then plugin output has
                        # to be deleted first
                        if force_overwrite is True:
                            self.Core.DB.POutput.DeleteAll({
                                "target_id": target["id"],
                                "plugin_key": plugin["key"]
                            })
                        work_model = models.Work(
                            target_id=target["id"],
                            plugin_key=plugin["key"])
                        self.Core.DB.session.add(
                            work_model)
        self.Core.DB.session.commit()

    def remove_work(self, work_id):
        work_obj = self.Core.DB.session.query(models.Work).get(work_id)
        if work_obj is None:
            raise exceptions.InvalidWorkReference(
                "No work with id " + str(work_id))
        self.Core.DB.session.delete(work_obj)
        self.Core.DB.session.commit()

    def patch_work(self, work_id, active=True):
        work_obj = self.Core.DB.session.query(models.Work).get(work_id)
        if work_obj is None:
            raise exceptions.InvalidWorkReference(
                "No work with id " + str(work_id))
        if active != work_obj.active:
            work_obj.active = active
            self.Core.DB.session.merge(work_obj)
            self.Core.DB.session.commit()

    def pause_all(self):
        query = self.Core.DB.session.query(models.Work)
        query.update({"active": False})
        self.Core.DB.session.commit()

    def resume_all(self):
        query = self.Core.DB.session.query(models.Work)
        query.update({"active": True})
        self.Core.DB.session.commit()

    def stop_plugins(self, plugin_list):
        query = self.Core.DB.session.query(models.Work)
        for plugin in plugin_list:
            query.filter_by(plugin_key=plugin["key"]).update(
                {"active": False})
        self.Core.DB.session.commit()

    def stop_targets(self, target_list):
        query = self.Core.DB.session.query(models.Work)
        for target in target_list:
            query.filter_by(target_id=target["id"]).update(
                {"active": False})
        self.Core.DB.session.commit()

    def search_all(self, criteria):
        # Three things needed
        # + Total number of work
        # + Filtered work dicts
        # + Filtered number of works
        total = self.Core.DB.session.query(
            models.Work).count()
        filtered_work_objs = self._generate_query(criteria).all()
        filtered_number = self._generate_query(criteria, for_stats=True).count()
        return({
            "records_total": total,
            "records_filtered": filtered_number,
            "data": self._derive_work_dicts(filtered_work_objs)
        })
