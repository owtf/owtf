"""
owtf.managers.community_plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All database-level operations for community-uploaded plugins.

This module owns the "write" path (upload → validate → store) and the
"read" path (list, get, search, approve/reject).  The sandbox execution
lives in owtf.plugin.sandbox so this manager stays thin and testable.
"""

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
from owtf.plugin.sandbox import SandboxResult, SandboxRunner
from owtf.plugin.validator import PluginValidator, ValidationResult
from owtf.settings import (
    COMMUNITY_PLUGIN_DEFAULT_TIMEOUT,
    COMMUNITY_PLUGIN_MEMORY_LIMIT,
    COMMUNITY_PLUGINS_DIR,
    PLUGIN_ALLOWED_EXTENSIONS,
    PLUGIN_UPLOAD_MAX_SIZE,
)

logger = logging.getLogger(__name__)

DRY_RUN_TARGET = "https://www.google.com"
DRY_RUN_TIMEOUT = 30  # seconds — short, just checking the plugin loads and runs

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
        "sandbox": None,
        "auto_approved": False,
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

    # --- Sandbox dry run ---
    sandbox_result: SandboxResult = SandboxRunner.run(
        plugin_path=file_path,
        target_url=DRY_RUN_TARGET,
        timeout=DRY_RUN_TIMEOUT,
        memory_limit=memory_limit,
    )
    result["sandbox"] = sandbox_result.to_dict()

    approval_status = APPROVAL_PENDING
    result["auto_approved"] = False

    if sandbox_result.success:
        logger.info("Sandbox dry run passed; plugin saved as pending review: %s", name)
    else:
        result["warnings"].append("Sandbox dry run failed; plugin saved as pending: {}".format(sandbox_result.error))
        logger.warning("Sandbox dry run failed for plugin '%s': %s", name, sandbox_result.error)

    # --- Persist metadata to DB ---
    try:
        plugin = UserPlugin(
            name=name.strip(),
            description=description.strip(),
            category=(category or "").strip() or None,
            group=group,
            type=plugin_type,
            author=author.strip(),
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
        result["plugin"] = plugin.to_dict()
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
) -> Dict:
    """Return a paginated list of community plugins matching the filters."""
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
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "plugins": [p.to_dict() for p in plugins],
    }


def get_community_plugin(session, plugin_id: int) -> Optional[Dict]:
    """Return a single plugin dict by id, or None if not found."""
    plugin = session.query(UserPlugin).get(plugin_id)
    if plugin is None:
        return None
    return plugin.to_dict()


def test_run_community_plugin(session, plugin_id: int, target_url: str) -> Dict:
    """Quick test run of a community plugin against a URL.

    This is just a smoke test so the uploader/reviewer can see the plugin
    actually executes. It skips the normal scan pipeline on purpose
    (no target manager, no worklist, no output saved). For a real scan,
    use the plugin runner like the built-in plugins do.

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

    result: SandboxResult = SandboxRunner.run(
        plugin_path=plugin.file_path,
        target_url=target_url,
        timeout=plugin.execution_timeout,
        memory_limit=plugin.memory_limit,
    )
    payload = result.to_dict()
    payload["non_persistent"] = True
    payload["is_test_run"] = True
    return payload


# Old name kept as an alias so existing callers still work for now.
run_community_plugin = test_run_community_plugin


def approve_community_plugin(session, plugin_id: int) -> Optional[Dict]:
    """Set approval_status to 'approved'.  Returns updated dict or None."""
    plugin = session.query(UserPlugin).get(plugin_id)
    if plugin is None:
        return None
    plugin.approval_status = APPROVAL_APPROVED
    plugin.rejection_reason = None
    session.commit()
    return plugin.to_dict()


def reject_community_plugin(session, plugin_id: int, reason: str = "") -> Optional[Dict]:
    """Set approval_status to 'rejected' with a reason.  Returns updated dict or None."""
    plugin = session.query(UserPlugin).get(plugin_id)
    if plugin is None:
        return None
    plugin.approval_status = APPROVAL_REJECTED
    plugin.rejection_reason = reason.strip() or "No reason provided"
    session.commit()
    return plugin.to_dict()


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
