"""
owtf.managers.worklist
~~~~~~~~~~~~~~~~~~~~~~
The DB stores worklist
"""
import logging

from sqlalchemy.sql import not_

from owtf.db.session import get_count
from owtf.lib import exceptions
from owtf.managers.plugin import get_all_plugin_dicts
from owtf.managers.poutput import delete_all_poutput, plugin_already_run
from owtf.managers.target import get_target_config_dict, get_target_config_dicts
from owtf.models.plugin import Plugin
from owtf.models.target import Target
from owtf.models.work import Work


def load_works(session, target_urls, options):
    """Select the proper plugins to run against the target URL.

    .. note::

        If plugin group is not specified and several targets are fed, OWTF
        will run the WEB plugins for targets that are URLs and the NET
        plugins for the ones that are IP addresses.

    :param str target_url: the target URL
    :param dict options: the options from the CLI.
    """
    for target_url in target_urls:
        if target_url:
            target = get_target_config_dicts(
                session=session, filter_data={"target_url": target_url}
            )
            group = options["plugin_group"]
            if options["only_plugins"] is None:
                # If the plugin group option is the default one (not specified by the user).
                if group is None:
                    group = "web"  # Default to web plugins.
                    # Run net plugins if target does not start with http (see #375).
                    if not target_url.startswith(("http://", "https://")):
                        group = "network"
                filter_data = {"type": options["plugin_type"], "group": group}
            else:
                filter_data = {
                    "code": options.get("only_plugins"),
                    "type": options.get("plugin_type"),
                }
            plugins = get_all_plugin_dicts(session=session, criteria=filter_data)
            if not plugins:
                logging.error(
                    "No plugin found matching type '%s' and group '%s' for target %s!",
                    options["plugin_type"],
                    group,
                    target[0]["target_url"],
                )
            add_work(
                session=session,
                target_list=target,
                plugin_list=plugins,
                force_overwrite=options["force_overwrite"],
            )


def worklist_generate_query(session, criteria=None, for_stats=False):
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
    query = session.query(Work).join(Target).join(Plugin).order_by(Work.id)
    if criteria.get("search", None):
        if criteria.get("target_url", None):
            if isinstance(criteria.get("target_url"), list):
                criteria["target_url"] = criteria["target_url"][0]
            query = query.filter(
                Target.target_url.like("%%{!s}%%".format(criteria["target_url"]))
            )
        if criteria.get("type", None):
            if isinstance(criteria.get("type"), list):
                criteria["type"] = criteria["type"][0]
            query = query.filter(Plugin.type.like("%%{!s}%%".format(criteria["type"])))
        if criteria.get("group", None):
            if isinstance(criteria.get("group"), list):
                criteria["group"] = criteria["group"][0]
            query = query.filter(
                Plugin.group.like("%%{!s}%%".format(criteria["group"]))
            )
        if criteria.get("name", None):
            if isinstance(criteria.get("name"), list):
                criteria["name"] = criteria["name"][0]
            query = query.filter(Plugin.name.ilike("%%{!s}%%".format(criteria["name"])))
    try:
        if criteria.get("id", None):
            if isinstance(criteria.get("id"), list):
                query = query.filter(Work.target_id.in_(criteria.get("id")))
            if isinstance(criteria.get("id"), str):
                query = query.filter_by(target_id=int(criteria.get("id")))
        if not for_stats:
            if criteria.get("offset", None):
                if isinstance(criteria.get("offset"), list):
                    criteria["offset"] = criteria["offset"][0]
                query = query.offset(int(criteria["offset"]))
            if criteria.get("limit", None):
                if isinstance(criteria.get("limit"), list):
                    criteria["limit"] = criteria["limit"][0]
                query = query.limit(int(criteria["limit"]))
    except ValueError:
        raise exceptions.InvalidParameterType(
            "Invalid parameter type for transaction db"
        )
    return query


def _derive_work_dict(work_model):
    """Fetch work dict based on work model

    :param work_model: Model
    :type work_model:
    :return: Work dict
    :rtype: `dict`
    """
    if work_model is not None:
        wdict = {}
        wdict["target"] = get_target_config_dict(work_model.target)
        wdict["plugin"] = work_model.plugin.to_dict()
        wdict["id"] = work_model.id
        wdict["active"] = work_model.active
        return wdict


def _derive_work_dicts(work_models):
    """Fetch list of work dicts based on list of work models

    :param work_models: List of work models
    :type work_models: `list`
    :return: List of work dicts
    :rtype: `dict`
    """
    results = []
    for work_model in work_models:
        if work_model is not None:
            results.append(_derive_work_dict(work_model))
    return results


def get_work_for_target(session, in_use_target_list):
    """Get work for target list in use

    :param in_use_target_list: Target list in use
    :type in_use_target_list: `list`
    :return: A tuple of target, plugin work
    :rtype: `tuple`
    """
    query = session.query(Work).filter_by(active=True).order_by(Work.id)
    if len(in_use_target_list) > 0:
        query = query.filter(not_(Work.target_id.in_(in_use_target_list)))
    work_obj = query.first()
    if work_obj:
        # First get the worker dict and then delete
        work_dict = _derive_work_dict(work_obj)
        session.delete(work_obj)
        session.commit()
        return (work_dict["target"], work_dict["plugin"])


def get_all_work(session, criteria=None):
    """Get all work dicts based on criteria

    :param criteria: Filter criteria
    :type criteria: `dict`
    :return: List of work dicts
    :rtype: `list`
    """
    query = worklist_generate_query(session, criteria)
    works = query.all()
    return _derive_work_dicts(works)


def get_work(session, work_id):
    """Get the work for work dict ID

    :param work_id: Work ID
    :type work_id: `int`
    :return: List of work dicts
    :rtype: `list`
    """
    work = session.query(Work).get(work_id)
    if work is None:
        raise exceptions.InvalidWorkReference(
            "No work with id {!s}".format(str(work_id))
        )
    return _derive_work_dict(work)


def group_sort_order(plugin_list):
    """Sort work into a priority of plugin type

    .. note::
        TODO: Fix for individual plugins
        # Right now only for plugin groups launched not individual plugins
        # Giving priority to plugin type based on type
        # Higher priority == run first!

    :param plugin_list: List of plugins to right
    :type plugin_list: `list`
    :return: Sorted list of plugin list
    :rtype: `list`
    """
    priority = {
        "grep": -1,
        "bruteforce": 0,
        "active": 1,
        "semi_passive": 2,
        "passive": 3,
        "external": 4,
    }
    # reverse = True so that descending order is maintained
    sorted_plugin_list = sorted(
        plugin_list, key=lambda k: priority[k["type"]], reverse=True
    )
    return sorted_plugin_list


def add_work(session, target_list, plugin_list, force_overwrite=False):
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
    if any(plugin["group"] == "auxiliary" for plugin in plugin_list):
        # No sorting if aux plugins are run
        sorted_plugin_list = plugin_list
    else:
        sorted_plugin_list = group_sort_order(plugin_list)
    for target in target_list:
        for plugin in sorted_plugin_list:
            # Check if it already in worklist
            if (
                get_count(
                    session.query(Work).filter_by(
                        target_id=target["id"], plugin_key=plugin["key"]
                    )
                )
                == 0
            ):
                # Check if it is already run ;) before adding
                is_run = plugin_already_run(
                    session=session, plugin_info=plugin, target_id=target["id"]
                )
                if (
                    (force_overwrite is True)
                    or (force_overwrite is False and is_run is False)
                ):
                    # If force overwrite is true then plugin output has
                    # to be deleted first
                    if force_overwrite is True:
                        delete_all_poutput(
                            session=session,
                            filter_data={"plugin_key": plugin["key"]},
                            target_id=target["id"],
                        )
                    work_model = Work(target_id=target["id"], plugin_key=plugin["key"])
                    session.add(work_model)
    session.commit()


def remove_work(session, work_id):
    """Remove work dict from worklist

    :param work_id: Work ID
    :type work_id: `int`
    :return: None
    :rtype: None
    """
    work_obj = session.query(Work).get(work_id)
    if work_obj is None:
        raise exceptions.InvalidWorkReference(
            "No work with id {!s}".format(str(work_id))
        )
    session.delete(work_obj)
    session.commit()


def delete_all_work(session):
    """Delete all work from the worklist

    :return: None
    :rtype: None
    """
    query = session.query(Work)
    for work_obj in query:
        session.delete(work_obj)
    session.commit()


def patch_work(session, work_id, active=True):
    """Patch work dict in the worklist

    :param work_id: Work dict id
    :type work_id: `int`
    :param active: Is work active or not
    :type active: `bool`
    :return: None
    :rtype: None
    """
    work_obj = session.query(Work).get(work_id)
    if work_obj is None:
        raise exceptions.InvalidWorkReference(
            "No work with id {!s}".format(str(work_id))
        )
    if active != work_obj.active:
        work_obj.active = active
        session.merge(work_obj)
        session.commit()


def pause_all_work(session):
    """Pause all work in the worklist

    :return: None
    :rtype: None
    """
    query = session.query(Work)
    query.update({"active": False})
    session.commit()


def resume_all_work(session):
    """Resume all work in the worklist

    :return: None
    :rtype: None
    """
    query = session.query(Work)
    query.update({"active": True})
    session.commit()


def stop_plugins(session, plugin_list):
    """Stop list of plugins from the worklist

    :param plugin_list: List of plugins to stop
    :type plugin_list: `list`
    :return: None
    :rtype: None
    """
    query = session.query(Work)
    for plugin in plugin_list:
        query.filter_by(plugin_key=plugin["key"]).update({"active": False})
    session.commit()


def stop_targets(session, target_list):
    """Stop work in the worklist for a list of targets

    :param target_list: List of targets
    :type target_list: `list`
    :return: None
    :rtype: None
    """
    query = session.query(Work)
    for target in target_list:
        query.filter_by(target_id=target["id"]).update({"active": False})
    session.commit()


def search_all_work(session, criteria):
    """Search the worklist

    .. note::
        Three things needed
            + Total number of work
            + Filtered work dicts
            + Filtered number of works

    :param criteria: Filter criteria
    :type criteria: `dict`
    :return: Results of the search query
    :rtype: `dict`
    """
    total = get_count(session.query(Work))
    filtered_work_objs = worklist_generate_query(session, criteria).all()
    filtered_number = worklist_generate_query(session, criteria, for_stats=True).count()
    results = {
        "records_total": total,
        "records_filtered": filtered_number,
        "data": _derive_work_dicts(filtered_work_objs),
    }
    return results
