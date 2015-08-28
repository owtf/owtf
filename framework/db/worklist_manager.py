#!/usr/bin/env python
'''
The DB stores worklist
'''
from framework.db import models
from framework.dependency_management.dependency_resolver import BaseComponent
from framework.lib import exceptions
from sqlalchemy import exc
from sqlalchemy.sql import not_
import logging


class WorklistManager(BaseComponent):
    
    COMPONENT_NAME = "worklist_manager"
    
    def __init__(self):
        self.register_in_service_locator()
        self.db = self.get_component("db")
        self.plugin_output = None
        self.target = None
        self.db_plugin = None

    def init(self):
        self.target = self.get_component("target")
        self.plugin_output = self.get_component("plugin_output")
        self.db_plugin = self.get_component("db_plugin")

    def _generate_query(self, criteria=None, for_stats=False):
        if criteria is None:
            criteria = {}
        query = self.db.session.query(models.Work).join(
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
            wdict["target"] = self.target.DeriveTargetConfig(
                work_model.target)
            wdict["plugin"] = self.db_plugin.DerivePluginDict(
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

    def get_work(self, in_use_target_list):
        query = self.db.session.query(models.Work).filter_by(
            active=True).order_by(models.Work.id)
        if len(in_use_target_list) > 0:
            query = query.filter(
                not_(models.Work.target_id.in_(in_use_target_list)))
        work_obj = query.first()
        if work_obj:
            # First get the worker dict and then delete
            work_dict = self._derive_work_dict(work_obj)
            self.db.session.delete(work_obj)
            self.db.session.commit()
            return((work_dict["target"], work_dict["plugin"]))

    def get_all(self, criteria=None):
        query = self._generate_query(criteria)
        works = query.all()
        return(self._derive_work_dicts(works))

    def get(self, work_id):
        work = self.db.session.query(models.Work).get(work_id)
        if work is None:
            raise exceptions.InvalidWorkReference(
                "No work with id " + str(work_id))
        return(self._derive_work_dict(work))

    def add_work(self, target_list, plugin_list, force_overwrite=False):
        for target in target_list:
            for plugin in plugin_list:
                # Check if it already in worklist
                if self.db.session.query(models.Work).filter_by(
                        target_id=target["id"],
                        plugin_key=plugin["key"]).count() == 0:
                    # Check if it is already run ;) before adding
                    if ((force_overwrite is True) or
                        (force_overwrite is False and
                            self.plugin_output.PluginAlreadyRun(
                                plugin, target_id=target["id"]) is False)):
                        # If force overwrite is true then plugin output has
                        # to be deleted first
                        if force_overwrite is True:
                            self.plugin_output.DeleteAll({
                                "target_id": target["id"],
                                "plugin_key": plugin["key"]
                            })
                        work_model = models.Work(
                            target_id=target["id"],
                            plugin_key=plugin["key"])
                        self.db.session.add(
                            work_model)
        self.db.session.commit()

    def remove_work(self, work_id):
        work_obj = self.db.session.query(models.Work).get(work_id)
        if work_obj is None:
            raise exceptions.InvalidWorkReference(
                "No work with id " + str(work_id))
        self.db.session.delete(work_obj)
        self.db.session.commit()

    def patch_work(self, work_id, active=True):
        work_obj = self.db.session.query(models.Work).get(work_id)
        if work_obj is None:
            raise exceptions.InvalidWorkReference(
                "No work with id " + str(work_id))
        if active != work_obj.active:
            work_obj.active = active
            self.db.session.merge(work_obj)
            self.db.session.commit()

    def pause_all(self):
        query = self.db.session.query(models.Work)
        query.update({"active": False})
        self.db.session.commit()

    def resume_all(self):
        query = self.db.session.query(models.Work)
        query.update({"active": True})
        self.db.session.commit()

    def stop_plugins(self, plugin_list):
        query = self.db.session.query(models.Work)
        for plugin in plugin_list:
            query.filter_by(plugin_key=plugin["key"]).update(
                {"active": False})
        self.db.session.commit()

    def stop_targets(self, target_list):
        query = self.db.session.query(models.Work)
        for target in target_list:
            query.filter_by(target_id=target["id"]).update(
                {"active": False})
        self.db.session.commit()

    def search_all(self, criteria):
        # Three things needed
        # + Total number of work
        # + Filtered work dicts
        # + Filtered number of works
        total = self.db.session.query(
            models.Work).count()
        filtered_work_objs = self._generate_query(criteria).all()
        filtered_number = self._generate_query(criteria, for_stats=True).count()
        return({
            "records_total": total,
            "records_filtered": filtered_number,
            "data": self._derive_work_dicts(filtered_work_objs)
        })
