"""
owtf.managers.community_plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All database-level operations for community-uploaded plugins.

This module owns the "write" path (upload → validate → store) and the
"read" path (list, get, search, approve/reject).  Approved plugins run
through the normal plugin runner alongside built-in plugins; admin
review of the source is the trust boundary.
"""

import datetime
import logging
import os
import re
import unicodedata
import uuid
from typing import Dict, List, Optional

from owtf.models.user_plugin import (
    APPROVAL_APPROVED,
    APPROVAL_PENDING,
    APPROVAL_REJECTED,
    VALID_GROUPS,
    VALID_TYPES,
    UserPlugin,
)
from owtf.plugin.validator import PluginValidator, ValidationResult
from owtf.settings import (
    COMMUNITY_PLUGIN_DEFAULT_TIMEOUT,
    COMMUNITY_PLUGIN_MEMORY_LIMIT,
    COMMUNITY_PLUGINS_DIR,
    PLUGIN_ALLOWED_EXTENSIONS,
    PLUGIN_UPLOAD_MAX_SIZE,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Filename sanitisation
# ---------------------------------------------------------------------------

_SAFE_FILENAME_RE = re.compile(r"[^\w\-. ]")
_MAX_FILENAME_LENGTH = 100


def _sanitise_filename(raw: str) -> str:
    """Return a filesystem-safe filename derived from *raw*.

    Steps:
      1. Normalise unicode to ASCII equivalents where possible.
      2. Replace anything that is not alphanumeric / dash / dot / space
         with an underscore.
      3. Strip leading dots (hidden files) and whitespace.
      4. Truncate to _MAX_FILENAME_LENGTH characters.
    """
    try:
        normalised = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")
    except Exception:
        normalised = raw
    safe = _SAFE_FILENAME_RE.sub("_", normalised)
    safe = safe.strip(". ")
    if not safe:
        safe = "plugin"
    return safe[:_MAX_FILENAME_LENGTH]


def _unique_plugin_path(name: str) -> str:
    """Return a unique, collision-free absolute path for storing a plugin.

    Format: <COMMUNITY_PLUGINS_DIR>/<sanitised_name>_<uuid4_hex[:8]>.py
    """
    os.makedirs(COMMUNITY_PLUGINS_DIR, exist_ok=True)
    stem = _sanitise_filename(name)
    uid = uuid.uuid4().hex[:8]
    filename = "{}_{}{}".format(stem, uid, ".py")
    return os.path.join(COMMUNITY_PLUGINS_DIR, filename)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _validate_metadata(name: str, description: str, group: str, plugin_type: str, author: str) -> List[str]:
    """Return a list of metadata validation errors (empty list = OK)."""
    errors = []
    if not name or not name.strip():
        errors.append("'name' is required")
    elif len(name.strip()) < 3:
        errors.append("'name' must be at least 3 characters")
    elif len(name.strip()) > 128:
        errors.append("'name' must not exceed 128 characters")

    if not description or not description.strip():
        errors.append("'description' is required")

    if group not in VALID_GROUPS:
        errors.append("'group' must be one of: {}".format(", ".join(sorted(VALID_GROUPS))))

    if plugin_type not in VALID_TYPES:
        errors.append("'type' must be one of: {}".format(", ".join(sorted(VALID_TYPES))))

    if not author or not author.strip():
        errors.append("'author' is required")
    elif len(author.strip()) > 128:
        errors.append("'author' must not exceed 128 characters")

    return errors


# ---------------------------------------------------------------------------
# Public manager functions
# ---------------------------------------------------------------------------


def upload_community_plugin(
    session,
    name: str,
    description: str,
    group: str,
    plugin_type: str,
    author: str,
    file_body: bytes,
    original_filename: str,
    category: Optional[str] = None,
    version: str = "1.0.0",
    tags: Optional[str] = None,
    execution_timeout: int = COMMUNITY_PLUGIN_DEFAULT_TIMEOUT,
    memory_limit: int = COMMUNITY_PLUGIN_MEMORY_LIMIT,
    is_public: bool = True,
    user_id: Optional[int] = None,
) -> Dict:
    """Validate and persist a new community plugin.

    Returns a dict with keys:
      - success (bool)
      - errors  (list[str])  — metadata / file errors
      - violations (list[str]) — AST security violations
      - warnings (list[str])  — non-fatal AST warnings
      - plugin (dict | None) — serialised UserPlugin on success
    """
    result = {
        "success": False,
        "errors": [],
        "violations": [],
        "warnings": [],
        "plugin": None,
    }

    # --- File extension check ---
    _, ext = os.path.splitext(original_filename)
    if ext.lower() not in PLUGIN_ALLOWED_EXTENSIONS:
        result["errors"].append("Invalid file type '{}'. Only .py files are accepted.".format(ext))
        return result

    # --- File size check ---
    if len(file_body) > PLUGIN_UPLOAD_MAX_SIZE:
        result["errors"].append("Plugin file exceeds maximum size of {} KB.".format(PLUGIN_UPLOAD_MAX_SIZE // 1024))
        return result

    # --- Metadata validation ---
    metadata_errors = _validate_metadata(name, description, group, plugin_type, author)
    if metadata_errors:
        result["errors"].extend(metadata_errors)
        return result

    # --- Duplicate name check ---
    if UserPlugin.get_by_name(session, name.strip()):
        result["errors"].append("A plugin named '{}' already exists. Choose a unique name.".format(name.strip()))
        return result

    # --- AST security validation ---
    validation: ValidationResult = PluginValidator.validate_bytes(file_body, filename=original_filename)
    result["violations"] = validation.violations
    result["warnings"] = validation.warnings

    if not validation.passed:
        logger.warning(
            "Plugin upload rejected (AST violations) — name=%s violations=%s",
            name,
            validation.violations,
        )
        return result

    # --- Save file to disk ---
    file_path = _unique_plugin_path(name.strip())
    try:
        with open(file_path, "wb") as fh:
            fh.write(file_body)
    except OSError as exc:
        result["errors"].append("Failed to save plugin file: {}".format(exc))
        return result

    approval_status = APPROVAL_PENDING
    logger.info("Plugin passed AST validation; saved as pending review: %s", name)

    # --- Persist metadata to DB ---
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
            approval_status=approval_status,
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
        # Uploader is the owner, so return the owner shape.
        # rejection_reason is empty on a fresh upload but filled in later
        # if an admin rejects.
        result["plugin"] = plugin.to_owner_dict()
        logger.info("Community plugin uploaded: id=%d name=%s", plugin.id, plugin.name)
    except Exception as exc:
        session.rollback()
        # Clean up the file if DB insert fails so we don't orphan files
        try:
            os.remove(file_path)
        except OSError:
            pass
        result["errors"].append("Database error: {}".format(str(exc)))
        logger.exception("Failed to persist community plugin to DB")

    return result


def list_community_plugins(
    session,
    status: Optional[str] = APPROVAL_APPROVED,
    category: Optional[str] = None,
    group: Optional[str] = None,
    plugin_type: Optional[str] = None,
    min_rating: Optional[float] = None,
    query: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    as_admin: bool = False,
) -> Dict:
    """Return a paginated list of community plugins matching the filters.

    Pass as_admin=True to use the richer serializer (reviewer trail,
    resource limits, rejection reason). Public callers should leave it False.
    """
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
    serializer = (lambda p: p.to_admin_dict()) if as_admin else (lambda p: p.to_dict())
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "plugins": [serializer(p) for p in plugins],
    }


def list_owner_plugins(session, user_id: int) -> Dict:
    """Return plugins uploaded by user_id, using the owner serializer so
    rejection reasons are visible to the uploader."""
    plugins = UserPlugin.get_for_user(session, user_id)
    return {
        "total": len(plugins),
        "plugins": [p.to_owner_dict() for p in plugins],
    }


def get_community_plugin(session, plugin_id: int, as_admin: bool = False) -> Optional[Dict]:
    """Return a single plugin dict by id, or None if not found.

    Default is the safe public view. Pass as_admin=True to also see
    reviewer metadata. Source code is served by
    get_community_plugin_source() behind an admin-only route.
    """
    plugin = session.query(UserPlugin).get(plugin_id)
    if plugin is None:
        return None
    return plugin.to_admin_dict() if as_admin else plugin.to_dict()


def get_community_plugin_source(session, plugin_id: int) -> Optional[Dict]:
    """Return {"plugin_id", "name", "source_code"} for admin review.

    Returns None if the plugin does not exist. source_code is None if
    the file cannot be read (missing, permission error, etc). file_path
    is intentionally left out so the server's filesystem layout is not
    exposed to any client.
    """
    plugin = session.query(UserPlugin).get(plugin_id)
    if plugin is None:
        return None
    try:
        with open(plugin.file_path, "r", encoding="utf-8") as fh:
            source = fh.read()
    except OSError:
        source = None
    return {"plugin_id": plugin.id, "name": plugin.name, "source_code": source}


def test_run_community_plugin(session, plugin_id: int, target_url: str) -> Dict:
    """Smoke-test an approved community plugin against a single URL.

    Loads and invokes the plugin via the standard module loader so the
    uploader / reviewer can see it execute. Output is not persisted
    through the scan pipeline; for a real scan, queue it like a built-in
    plugin.

    Plugin must be approved.
    """
    plugin = session.query(UserPlugin).get(plugin_id)
    if plugin is None:
        return {"success": False, "error": "Plugin not found", "non_persistent": True, "is_test_run": True}
    if plugin.approval_status != APPROVAL_APPROVED:
        return {
            "success": False,
            "error": "Plugin is not approved (status: {})".format(plugin.approval_status),
            "non_persistent": True,
            "is_test_run": True,
        }
    if not os.path.isfile(plugin.file_path):
        return {"success": False, "error": "Plugin file missing from disk", "non_persistent": True, "is_test_run": True}

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
        output = plugin_runner.run_plugin(None, plugin_dict)
        return {
            "success": True,
            "output": output,
            "non_persistent": True,
            "is_test_run": True,
        }
    except Exception as exc:
        logger.exception("Community plugin test-run failed: id=%d", plugin_id)
        return {
            "success": False,
            "error": str(exc),
            "non_persistent": True,
            "is_test_run": True,
        }


def approve_community_plugin(session, plugin_id: int, reviewer_id: Optional[int] = None) -> Optional[Dict]:
    """Set approval_status to 'approved'.  Returns updated dict or None."""
    plugin = session.query(UserPlugin).get(plugin_id)
    if plugin is None:
        return None
    plugin.approval_status = APPROVAL_APPROVED
    plugin.rejection_reason = None
    plugin.reviewed_by_user_id = reviewer_id
    plugin.reviewed_at = datetime.datetime.utcnow()
    session.commit()
    session.refresh(plugin)
    return plugin.to_admin_dict()


def reject_community_plugin(
    session, plugin_id: int, reason: str = "", reviewer_id: Optional[int] = None
) -> Optional[Dict]:
    """Set approval_status to 'rejected' with a reason.  Returns updated dict or None."""
    plugin = session.query(UserPlugin).get(plugin_id)
    if plugin is None:
        return None
    plugin.approval_status = APPROVAL_REJECTED
    plugin.rejection_reason = reason.strip() or "No reason provided"
    plugin.reviewed_by_user_id = reviewer_id
    plugin.reviewed_at = datetime.datetime.utcnow()
    session.commit()
    session.refresh(plugin)
    return plugin.to_admin_dict()


def get_plugin_review_history(session, plugin_id: int) -> Optional[List[Dict]]:
    """Return the review timeline for a plugin.

    The events are derived from the plugin's own upload and review
    timestamps. There is no separate append-only audit table yet, so
    this is a review history view, not an audit log in the strict
    sense. Returns ``None`` when the plugin does not exist.
    """
    plugin = session.query(UserPlugin).get(plugin_id)
    if plugin is None:
        return None
    events: List[Dict] = [
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


def delete_community_plugin(session, plugin_id: int) -> bool:
    """Delete plugin record and its file from disk.  Returns True on success."""
    plugin = session.query(UserPlugin).get(plugin_id)
    if plugin is None:
        return False
    file_path = plugin.file_path
    session.delete(plugin)
    session.commit()
    try:
        if file_path and os.path.isfile(file_path):
            os.remove(file_path)
    except OSError as exc:
        logger.warning("Could not remove plugin file %s: %s", file_path, exc)
    return True
