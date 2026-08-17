"""
owtf.managers.community_plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Database-level operations for community-uploaded plugins: upload,
validate, store, list, approve, reject, delete, and test-run. Approved
plugins run through the normal plugin runner; admin review of the
source is the trust boundary.
"""

import datetime
import logging
import os
import re
import unicodedata
import uuid

from owtf.models.user_plugin import (
    APPROVAL_APPROVED,
    APPROVAL_PENDING,
    APPROVAL_REJECTED,
    VALID_GROUPS,
    VALID_TYPES,
    UserPlugin,
)
from owtf.plugin.validator import PluginValidator
from owtf.settings import (
    COMMUNITY_PLUGIN_DEFAULT_TIMEOUT,
    COMMUNITY_PLUGIN_MEMORY_LIMIT,
    COMMUNITY_PLUGINS_DIR,
    PLUGIN_ALLOWED_EXTENSIONS,
    PLUGIN_UPLOAD_MAX_SIZE,
)

logger = logging.getLogger(__name__)

_SAFE_FILENAME_RE = re.compile(r"[^\w\-. ]")
_MAX_FILENAME_LENGTH = 100


def _sanitise_filename(raw):
    try:
        normalised = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")
    except Exception:
        normalised = raw
    safe = _SAFE_FILENAME_RE.sub("_", normalised).strip(". ")
    return (safe or "plugin")[:_MAX_FILENAME_LENGTH]


def _unique_plugin_path(name):
    """Return <COMMUNITY_PLUGINS_DIR>/<sanitised>_<uuid8>.py."""
    os.makedirs(COMMUNITY_PLUGINS_DIR, exist_ok=True)
    filename = "{}_{}.py".format(_sanitise_filename(name), uuid.uuid4().hex[:8])
    return os.path.join(COMMUNITY_PLUGINS_DIR, filename)


def _validate_metadata(name, description, group, plugin_type, author):
    """Return a list of metadata errors. Empty list means OK."""
    errors = []
    stripped_name = (name or "").strip()
    if not stripped_name:
        errors.append("'name' is required")
    elif len(stripped_name) < 3:
        errors.append("'name' must be at least 3 characters")
    elif len(stripped_name) > 128:
        errors.append("'name' must not exceed 128 characters")

    if not (description or "").strip():
        errors.append("'description' is required")

    if group not in VALID_GROUPS:
        errors.append("'group' must be one of: {}".format(", ".join(sorted(VALID_GROUPS))))

    if plugin_type not in VALID_TYPES:
        errors.append("'type' must be one of: {}".format(", ".join(sorted(VALID_TYPES))))

    stripped_author = (author or "").strip()
    if not stripped_author:
        errors.append("'author' is required")
    elif len(stripped_author) > 128:
        errors.append("'author' must not exceed 128 characters")

    return errors


def upload_community_plugin(
    session,
    name,
    description,
    group,
    plugin_type,
    author,
    file_body,
    original_filename,
    category=None,
    version="1.0.0",
    tags=None,
    execution_timeout=COMMUNITY_PLUGIN_DEFAULT_TIMEOUT,
    memory_limit=COMMUNITY_PLUGIN_MEMORY_LIMIT,
    is_public=True,
    user_id=None,
):
    """Validate and persist a community plugin upload.

    Returns {"success", "errors", "violations", "warnings", "plugin"}.
    On success, "plugin" is the owner-view dict. On any failure "success"
    is False and one of "errors" (metadata/file) or "violations" (AST) is
    populated.
    """
    result = {"success": False, "errors": [], "violations": [], "warnings": [], "plugin": None}

    ext = os.path.splitext(original_filename)[1].lower()
    if ext not in PLUGIN_ALLOWED_EXTENSIONS:
        result["errors"].append("Invalid file type '{}'. Only .py files are accepted.".format(ext))
        return result

    if len(file_body) > PLUGIN_UPLOAD_MAX_SIZE:
        result["errors"].append("Plugin file exceeds maximum size of {} KB.".format(PLUGIN_UPLOAD_MAX_SIZE // 1024))
        return result

    metadata_errors = _validate_metadata(name, description, group, plugin_type, author)
    if metadata_errors:
        result["errors"].extend(metadata_errors)
        return result

    if UserPlugin.get_by_name(session, name.strip()):
        result["errors"].append("A plugin named '{}' already exists. Choose a unique name.".format(name.strip()))
        return result

    validation = PluginValidator.validate_bytes(file_body, filename=original_filename)
    result["violations"] = validation.violations
    result["warnings"] = validation.warnings
    if not validation.passed:
        logger.warning("Plugin upload rejected by AST validator: name=%s violations=%s", name, validation.violations)
        return result

    file_path = _unique_plugin_path(name.strip())
    try:
        with open(file_path, "wb") as fh:
            fh.write(file_body)
    except OSError as exc:
        result["errors"].append("Failed to save plugin file: {}".format(exc))
        return result

    try:
        plugin = UserPlugin(
            name=name.strip(),
            description=description.strip(),
            category=(category or "").strip() or None,
            group=group,
            type=plugin_type,
            author=author.strip(),
            user_id=user_id,
            file_path=file_path,
            approval_status=APPROVAL_PENDING,
            version=version.strip() or "1.0.0",
            tags=tags.strip() if tags else None,
            execution_timeout=execution_timeout,
            memory_limit=memory_limit,
            is_public=is_public,
        )
        session.add(plugin)
        session.commit()
        session.refresh(plugin)
        result["success"] = True
        result["plugin"] = plugin.to_owner_dict()
        logger.info("Community plugin uploaded: id=%d name=%s (pending review)", plugin.id, plugin.name)
    except Exception as exc:
        session.rollback()
        try:
            os.remove(file_path)
        except OSError:
            pass
        result["errors"].append("Database error: {}".format(str(exc)))
        logger.exception("Failed to persist community plugin")

    return result


def list_community_plugins(
    session,
    status=APPROVAL_APPROVED,
    category=None,
    group=None,
    plugin_type=None,
    min_rating=None,
    query=None,
    limit=50,
    offset=0,
    as_admin=False,
):
    """Paginated list of community plugins. as_admin=True picks the richer serializer."""
    plugins, total = UserPlugin.search(
        session,
        status=status,
        category=category,
        group=group,
        plugin_type=plugin_type,
        min_rating=min_rating,
        query=query,
        limit=limit,
        offset=offset,
    )
    serializer = UserPlugin.to_admin_dict if as_admin else UserPlugin.to_dict
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "plugins": [serializer(p) for p in plugins],
    }


def list_owner_plugins(session, user_id):
    """Plugins uploaded by user_id, owner view (so rejection reasons are visible)."""
    plugins = UserPlugin.get_for_user(session, user_id)
    return {"total": len(plugins), "plugins": [p.to_owner_dict() for p in plugins]}


def get_community_plugin(session, plugin_id, as_admin=False):
    """Return a plugin dict, or None if not found. Public view by default."""
    plugin = session.query(UserPlugin).get(plugin_id)
    if plugin is None:
        return None
    return plugin.to_admin_dict() if as_admin else plugin.to_dict()


def get_community_plugin_source(session, plugin_id):
    """{"plugin_id", "name", "source_code"} for admin review. file_path is not returned."""
    plugin = session.query(UserPlugin).get(plugin_id)
    if plugin is None:
        return None
    try:
        with open(plugin.file_path, "r", encoding="utf-8") as fh:
            source = fh.read()
    except OSError:
        source = None
    return {"plugin_id": plugin.id, "name": plugin.name, "source_code": source}


def test_run_community_plugin(session, plugin_id, target_url):
    """Run an approved plugin once against a URL. Result is not persisted."""
    plugin = session.query(UserPlugin).get(plugin_id)
    if plugin is None:
        return {"success": False, "error": "Plugin not found"}
    if plugin.approval_status != APPROVAL_APPROVED:
        return {"success": False, "error": "Plugin is not approved (status: {})".format(plugin.approval_status)}
    if not os.path.isfile(plugin.file_path):
        return {"success": False, "error": "Plugin file missing from disk"}

    from owtf.plugin.runner import runner as plugin_runner

    plugin_dict = {
        "source": "community",
        "name": plugin.name,
        "file_path": plugin.file_path,
        "type": plugin.type,
        "group": plugin.group,
        "execution_timeout": plugin.execution_timeout,
        "target_url": target_url,
    }
    try:
        return {"success": True, "output": plugin_runner.run_plugin(None, plugin_dict)}
    except Exception as exc:
        logger.exception("Community plugin test-run failed: id=%d", plugin_id)
        return {"success": False, "error": str(exc)}


def _plugin_key(up):
    """Deterministic key used to mirror a community plugin into the plugins table."""
    return "{}@community_{}".format(up.type, up.id)


def _sync_to_plugins_table(session, up):
    """Insert or refresh the plugins-table mirror for an approved community plugin.

    Approved community plugins live alongside built-in plugins in the
    plugins table so the standard worklist FK, worker lookup, and runner
    dispatch work without special cases.
    """
    from owtf.models.plugin import Plugin

    key = _plugin_key(up)
    row = session.query(Plugin).filter_by(key=key).first()
    if row is None:
        row = Plugin(key=key)
        session.add(row)
    row.title = up.name.replace("_", " ").title()
    row.name = up.name
    row.code = None  # no test_groups link; plugin_gen_query uses an outer join
    row.group = up.group
    row.type = up.type
    row.descrip = up.description
    row.file = os.path.basename(up.file_path)
    row.attr = None
    row.source = "community"
    row.file_path = up.file_path


def _unsync_from_plugins_table(session, up):
    from owtf.models.plugin import Plugin

    row = session.query(Plugin).filter_by(key=_plugin_key(up)).first()
    if row is not None:
        session.delete(row)


def approve_community_plugin(session, plugin_id, reviewer_id=None):
    plugin = session.query(UserPlugin).get(plugin_id)
    if plugin is None:
        return None
    plugin.approval_status = APPROVAL_APPROVED
    plugin.rejection_reason = None
    plugin.reviewed_by_user_id = reviewer_id
    plugin.reviewed_at = datetime.datetime.utcnow()
    _sync_to_plugins_table(session, plugin)
    session.commit()
    session.refresh(plugin)
    return plugin.to_admin_dict()


def reject_community_plugin(session, plugin_id, reason="", reviewer_id=None):
    plugin = session.query(UserPlugin).get(plugin_id)
    if plugin is None:
        return None
    was_approved = plugin.approval_status == APPROVAL_APPROVED
    plugin.approval_status = APPROVAL_REJECTED
    plugin.rejection_reason = reason.strip() or "No reason provided"
    plugin.reviewed_by_user_id = reviewer_id
    plugin.reviewed_at = datetime.datetime.utcnow()
    if was_approved:
        _unsync_from_plugins_table(session, plugin)
    session.commit()
    session.refresh(plugin)
    return plugin.to_admin_dict()


def get_plugin_review_history(session, plugin_id):
    """Timeline derived from the plugin's own upload/review timestamps."""
    plugin = session.query(UserPlugin).get(plugin_id)
    if plugin is None:
        return None
    events = [
        {
            "event": "uploaded",
            "timestamp": plugin.created_at.isoformat() if plugin.created_at else None,
            "user_id": plugin.user_id,
            "details": {"name": plugin.name, "version": plugin.version},
        }
    ]
    if plugin.reviewed_at:
        events.append(
            {
                "event": plugin.approval_status,
                "timestamp": plugin.reviewed_at.isoformat(),
                "user_id": plugin.reviewed_by_user_id,
                "details": {"rejection_reason": plugin.rejection_reason} if plugin.rejection_reason else {},
            }
        )
    return events


def delete_community_plugin(session, plugin_id):
    """Delete the DB row and the on-disk file. Returns True if the row existed."""
    plugin = session.query(UserPlugin).get(plugin_id)
    if plugin is None:
        return False
    file_path = plugin.file_path
    _unsync_from_plugins_table(session, plugin)
    session.delete(plugin)
    session.commit()
    try:
        if file_path and os.path.isfile(file_path):
            os.remove(file_path)
    except OSError as exc:
        logger.warning("Could not remove plugin file %s: %s", file_path, exc)
    return True
