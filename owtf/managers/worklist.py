"""
owtf.db.worklist_manager
~~~~~~~~~~~~~~~~~~~~~~~~

The DB stores worklist
"""

from sqlalchemy.sql import not_

from owtf.db import models
from owtf.dependency_management.dependency_resolver import BaseComponent
from owtf.lib import exceptions


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
        """Generate query based on criteria

        :param criteria: Filter criteria
        :type criteria: `dict`
        :param for_stats: True/False
        :type for_stats: `bool`
        :return:
        :rtype:
        """
        if criteria is None:
            criteria = {}
        query = self.db.session.query(models.Work).join(models.Target).join(models.Plugin).order_by(models.Work.id)
        if criteria.get('search', None):
            if criteria.get('target_url', None):
                if isinstance(criteria.get('target_url'), list):
                    criteria['target_url'] = criteria['target_url'][0]
                query = query.filter(models.Target.target_url.like('%%%s%%' % criteria['target_url']))
            if criteria.get('type', None):
                if isinstance(criteria.get('type'), list):
                    criteria['type'] = criteria['type'][0]
                query = query.filter(models.Plugin.type.like('%%%s%%' % criteria['type']))
            if criteria.get('group', None):
                if isinstance(criteria.get('group'), list):
                    criteria['group'] = criteria['group'][0]
                query = query.filter(models.Plugin.group.like('%%%s%%' % criteria['group']))
            if criteria.get('name', None):
                if isinstance(criteria.get('name'), list):
                    criteria['name'] = criteria['name'][0]
                query = query.filter(models.Plugin.name.ilike('%%%s%%' % criteria['name']))
        try:
            if criteria.get('id', None):
                if isinstance(criteria.get('id'), list):
                    query = query.filter(models.Work.target_id.in_(criteria.get('id')))
                if isinstance(criteria.get('id'), str):
                    query = query.filter_by(target_id=int(criteria.get('id')))
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
            raise exceptions.InvalidParameterType("Invalid parameter type for transaction db")
        return query

    def _derive_work_dict(self, work_model):
        """Fetch work dict based on work model

        :param work_model: Model
        :type work_model:
        :return: Work dict
        :rtype: `dict`
        """
        if work_model is not None:
            wdict = dict()
            wdict["target"] = self.target.get_target_config_dict(work_model.target)
            wdict["plugin"] = self.db_plugin.derive_plugin_dict(work_model.plugin)
            wdict["id"] = work_model.id
            wdict["active"] = work_model.active
            return wdict

    def _derive_work_dicts(self, work_models):
        """Fetch list of work dicts based on list of work models

        :param work_models: List of work models
        :type work_models: `list`
        :return: List of work dicts
        :rtype: `dict`
        """
        results = []
        for work_model in work_models:
            if work_model is not None:
                results.append(self._derive_work_dict(work_model))
        return results

    def get_work(self, in_use_target_list):
        """Get work for target list in use

        :param in_use_target_list: Target list in use
        :type in_use_target_list: `list`
        :return: A tuple of target, plugin work
        :rtype: `tuple`
        """
        query = self.db.session.query(models.Work).filter_by(active=True).order_by(models.Work.id)
        if len(in_use_target_list) > 0:
            query = query.filter(not_(models.Work.target_id.in_(in_use_target_list)))
        work_obj = query.first()
        if work_obj:
            # First get the worker dict and then delete
            work_dict = self._derive_work_dict(work_obj)
            self.db.session.delete(work_obj)
            self.db.session.commit()
            return (work_dict["target"], work_dict["plugin"])

    def get_all(self, criteria=None):
        """Get all work dicts based on criteria

        :param criteria: Filter criteria
        :type criteria: `dict`
        :return: List of work dicts
        :rtype: `list`
        """
        query = self._generate_query(criteria)
        works = query.all()
        return self._derive_work_dicts(works)

    def get(self, work_id):
        """Get the work for work dict ID

        :param work_id: Work ID
        :type work_id: `int`
        :return: List of work dicts
        :rtype: `list`
        """
        work = self.db.session.query(models.Work).get(work_id)
        if work is None:
            raise exceptions.InvalidWorkReference("No work with id %s" % str(work_id))
        return self._derive_work_dict(work)

    def group_sort_order(self, plugin_list):
        """Sort work into a priority of plugin type

        .note::
            TODO: Fix for individual plugins
            # Right now only for plugin groups launched not individual plugins
            # Giving priority to plugin type based on type
            # Higher priority == run first!

        :param plugin_list: List of plugins to right
        :type plugin_list: `list`
        :return: Sorted list of plugin list
        :rtype: `list`
        """
        priority = {"grep": -1, "bruteforce": 0, "active": 1, "semi_passive": 2, "passive": 3, "external": 4}
        # reverse = True so that descending order is maintained
        sorted_plugin_list = sorted(plugin_list, key=lambda k: priority[k['type']], reverse=True)
        return sorted_plugin_list

    def add_work(self, target_list, plugin_list, force_overwrite=False):
        """Add work to the worklist

        :param target_list: target list
        :type target_list: `list`
        :param plugin_list: plugin list
        :type plugin_list: `list`
        :param force_overwrite: True/False, user choice
        :type force_overwrite: `bool`
        :return: None
        :rtype: None
        """
        if any(plugin['group'] == 'auxiliary' for plugin in plugin_list):
            # No sorting if aux plugins are run
            sorted_plugin_list = plugin_list
        else:
            sorted_plugin_list = self.group_sort_order(plugin_list)
        for target in target_list:
            for plugin in sorted_plugin_list:
                # Check if it already in worklist
                if self.db.session.query(models.Work).filter_by(target_id=target["id"],
                                                                plugin_key=plugin["key"]).count() == 0:
                    # Check if it is already run ;) before adding
                    is_run = self.plugin_output.plugin_already_run(plugin, target_id=target["id"])
                    if (force_overwrite is True) or (force_overwrite is False and is_run is False):
                        # If force overwrite is true then plugin output has
                        # to be deleted first
                        if force_overwrite is True:
                            self.plugin_output.delete_all({"plugin_key": plugin["key"]}, target_id=target["id"])
                        work_model = models.Work(target_id=target["id"], plugin_key=plugin["key"])
                        self.db.session.add(work_model)
        self.db.session.commit()

    def remove_work(self, work_id):
        """Remove work dict from worklist

        :param work_id: Work ID
        :type work_id: `int`
        :return: None
        :rtype: None
        """
        work_obj = self.db.session.query(models.Work).get(work_id)
        if work_obj is None:
            raise exceptions.InvalidWorkReference("No work with id %s" % str(work_id))
        self.db.session.delete(work_obj)
        self.db.session.commit()

    def delete_all(self):
        """Delete all work from the worklist

        :return: None
        :rtype: None
        """
        query = self.db.session.query(models.Work)
        for work_obj in query:
            self.db.session.delete(work_obj)
        self.db.session.commit()

    def patch_work(self, work_id, active=True):
        """Patch work dict in the worklist

        :param work_id: Work dict id
        :type work_id: `int`
        :param active: Is work active or not
        :type active: `bool`
        :return: None
        :rtype: None
        """
        work_obj = self.db.session.query(models.Work).get(work_id)
        if work_obj is None:
            raise exceptions.InvalidWorkReference("No work with id %s" % str(work_id))
        if active != work_obj.active:
            work_obj.active = active
            self.db.session.merge(work_obj)
            self.db.session.commit()

    def pause_all(self):
        """Pause all work in the worklist

        :return: None
        :rtype: None
        """
        query = self.db.session.query(models.Work)
        query.update({"active": False})
        self.db.session.commit()

    def resume_all(self):
        """Resume all work in the worklist

        :return: None
        :rtype: None
        """
        query = self.db.session.query(models.Work)
        query.update({"active": True})
        self.db.session.commit()

    def stop_plugins(self, plugin_list):
        """Stop list of plugins from the worklist

        :param plugin_list: List of plugins to stop
        :type plugin_list: `list`
        :return: None
        :rtype: None
        """
        query = self.db.session.query(models.Work)
        for plugin in plugin_list:
            query.filter_by(plugin_key=plugin["key"]).update({"active": False})
        self.db.session.commit()

    def stop_targets(self, target_list):
        """Stop work in the worklist for a list of targets

        :param target_list: List of targets
        :type target_list: `list`
        :return: None
        :rtype: None
        """
        query = self.db.session.query(models.Work)
        for target in target_list:
            query.filter_by(target_id=target["id"]).update({"active": False})
        self.db.session.commit()

    def search_all(self, criteria):
        """Search the worklist

        .note::
            Three things needed
                + Total number of work
                + Filtered work dicts
                + Filtered number of works

        :param criteria: Filter criteria
        :type criteria: `dict`
        :return: Results of the search query
        :rtype: `dict`
        """
        total = self.db.session.query(models.Work).count()
        filtered_work_objs = self._generate_query(criteria).all()
        filtered_number = self._generate_query(criteria, for_stats=True).count()
        results = {
            "records_total": total,
            "records_filtered": filtered_number,
            "data": self._derive_work_dicts(filtered_work_objs)
        }
        return results
