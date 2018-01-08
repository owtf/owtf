"""
owtf.db.command_register
~~~~~~~~~~~~~~~~~~~~~~~~

Component to handle data storage and search of all commands run
"""

from owtf.db import models
from owtf.managers.poutput import plugin_output_exists
from owtf.managers.target import target_required, get_target_url_for_id


def add_command(session, command):
    """Adds a command to the DB

    :param command: Command to add
    :type command: `dict`
    :return: None
    :rtype: None
    """
    session.merge(models.Command(
        start_time=command['Start'],
        end_time=command['End'],
        success=command['Success'],
        target_id=command['Target'],
        plugin_key=command['PluginKey'],
        modified_command=command['ModifiedCommand'].strip(),
        original_command=command['OriginalCommand'].strip()
    ))
    session.commit()

def delete_command(session, command):
    """Delete the command from the DB

    :param command: Command to delete
    :type command: `dict`
    :return: None
    :rtype: None
    """
    command_obj = session.query(models.Command).get(command)
    session.delete(command_obj)
    session.commit()


@target_required
def command_already_registered(session, original_command, target_id=None):
    """Checks if the command has already been registered

    :param original_command: Original command to check
    :type original_command: `dict`
    :param target_id: Target ID
    :type target_id: `int`
    :return: None
    :rtype: None
    """
    register_entry = session.query(models.Command).get(original_command)
    if register_entry:
        # If the command was completed and the plugin output to which it
        # is referring exists
        if register_entry.success:
            if plugin_output_exists(session, register_entry.plugin_key, register_entry.target_id):
                return get_target_url_for_id(session, register_entry.target_id)
            else:
                delete_command(session, original_command)
                return None
        else:  # Command failed
            delete_command(session, original_command)
            return get_target_url_for_id(session, register_entry.target_id)
    return None
