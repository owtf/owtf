"""
owtf.api.handlers.community_plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tornado request handlers for the Community Plugin Ecosystem.

Endpoints
---------
POST /api/v1/community-plugins/upload
    Upload a new .py plugin file with metadata.
    Expects multipart/form-data with fields:
      name, description, group, type, author
    And an optional file field:
      plugin_file (the .py content)
    Optional fields: category, version, tags, execution_timeout, memory_limit, is_public

GET  /api/v1/community-plugins/
    List community plugins.  Query params:
      status      (default: approved)
      category, group, type, min_rating, q (search), limit, offset

GET  /api/v1/community-plugins/<id>/
    Get full details of one plugin.

POST /api/v1/community-plugins/<id>/run
    Execute a plugin against a target.
    JSON body: {"target_url": "https://example.com"}

POST /api/v1/community-plugins/<id>/approve   (admin-only, no auth check for now)
POST /api/v1/community-plugins/<id>/reject
    JSON body for reject: {"reason": "..."}

DELETE /api/v1/community-plugins/<id>/
    Delete a plugin and its file.
"""

import json
import logging

from owtf.api.handlers.base import APIRequestHandler
from owtf.api.handlers.jwtauth import admin_required, jwtauth
from owtf.lib.exceptions import APIError
from owtf.managers.community_plugin import (
    approve_community_plugin,
    delete_community_plugin,
    get_community_plugin,
    list_community_plugins,
    reject_community_plugin,
    test_run_community_plugin,
    upload_community_plugin,
)
from owtf.models.user_plugin import APPROVAL_APPROVED

logger = logging.getLogger(__name__)

__all__ = [
    "CommunityPluginUploadHandler",
    "CommunityPluginListHandler",
    "CommunityPluginDetailHandler",
    "CommunityPluginRunHandler",
    "CommunityPluginApproveHandler",
    "CommunityPluginRejectHandler",
]


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------


@jwtauth
class CommunityPluginUploadHandler(APIRequestHandler):
    """Accept a multipart plugin upload, validate it, and store it."""

    SUPPORTED_METHODS = ["POST", "OPTIONS"]

    def post(self):
        """Upload a community plugin.

        **Request** (multipart/form-data):
          - name         (required, string)
          - description  (required, string)
          - group        (required: web | network | auxiliary)
          - type         (required: active | passive | semi_passive | external | grep)
          - author       (required, string)
          - plugin_file  (required, .py file)
          - category     (optional)
          - version      (optional, default "1.0.0")
          - tags         (optional, comma-separated)
          - execution_timeout (optional, int seconds)
          - memory_limit      (optional, int bytes)
          - is_public         (optional, bool)

        **Response** (success):
          {"status": "success", "data": {"plugin": {...}, "warnings": [...]}}

        **Response** (validation error):
          HTTP 422
          {"status": "fail", "data": {"errors": [...], "violations": [...]}}
        """
        try:
            # --- Extract text fields ---
            def _field(name, default=""):
                vals = self.request.arguments.get(name)
                if vals:
                    return vals[0] if isinstance(vals[0], str) else vals[0].decode("utf-8")
                return default

            name = _field("name")
            description = _field("description")
            group = _field("group", "web")
            plugin_type = _field("type", "passive")
            author = _field("author")
            category = _field("category") or None
            version = _field("version", "1.0.0")
            tags = _field("tags") or None
            is_public = _field("is_public", "true").lower() not in ("false", "0", "no")

            try:
                execution_timeout = int(_field("execution_timeout", "300"))
            except ValueError:
                execution_timeout = 300

            try:
                memory_limit = int(_field("memory_limit", str(256 * 1024 * 1024)))
            except ValueError:
                memory_limit = 256 * 1024 * 1024

            # --- Extract uploaded file ---
            files = self.request.files.get("plugin_file")
            if not files:
                raise APIError(400, "No plugin_file provided in the upload")

            file_info = files[0]
            file_body = file_info["body"]
            original_filename = file_info.get("filename", "plugin.py")

            # --- Delegate to manager ---
            result = upload_community_plugin(
                session=self.session,
                name=name,
                description=description,
                group=group,
                plugin_type=plugin_type,
                author=author,
                file_body=file_body,
                original_filename=original_filename,
                category=category,
                version=version,
                tags=tags,
                execution_timeout=execution_timeout,
                memory_limit=memory_limit,
                is_public=is_public,
            )

            if not result["success"]:
                # Return 422 Unprocessable Entity with details
                self.set_status(422)
                self.finish(
                    {
                        "status": "fail",
                        "data": {
                            "errors": result["errors"],
                            "violations": result["violations"],
                            "warnings": result["warnings"],
                        },
                    }
                )
                return

            self.set_status(201)
            if result["auto_approved"]:
                message = (
                    "Plugin uploaded and auto-approved after passing AST validation "
                    "and sandbox dry run. It is now live in the marketplace."
                )
            else:
                message = "Plugin uploaded successfully but sandbox dry run failed. It is pending manual review."
            self.success(
                {
                    "plugin": result["plugin"],
                    "warnings": result["warnings"],
                    "sandbox": result["sandbox"],
                    "auto_approved": result["auto_approved"],
                    "message": message,
                }
            )

        except APIError:
            raise
        except Exception as exc:
            logger.exception("Unhandled error in plugin upload")
            raise APIError(500, "Internal server error during plugin upload: {}".format(str(exc)))


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


@jwtauth
class CommunityPluginListHandler(APIRequestHandler):
    """List and search community plugins."""

    SUPPORTED_METHODS = ["GET", "OPTIONS"]

    def get(self):
        """List community plugins with optional filtering.

        Query parameters:
          - status     (default: approved)
          - category
          - group      (web | network | auxiliary)
          - type       (active | passive | semi_passive | external | grep)
          - min_rating (float)
          - q          (free-text search on name/description/author)
          - limit      (int, default 50, max 200)
          - offset     (int, default 0)
        """

        def _qparam(name, default=None):
            vals = self.request.arguments.get(name)
            if vals:
                return vals[0] if isinstance(vals[0], str) else vals[0].decode("utf-8")
            return default

        status = _qparam("status", APPROVAL_APPROVED)
        category = _qparam("category")
        group = _qparam("group")
        plugin_type = _qparam("type")
        q = _qparam("q")

        try:
            min_rating = float(_qparam("min_rating", "0") or 0)
        except ValueError:
            min_rating = 0.0

        try:
            limit = min(int(_qparam("limit", "50") or 50), 200)
        except ValueError:
            limit = 50

        try:
            offset = max(int(_qparam("offset", "0") or 0), 0)
        except ValueError:
            offset = 0

        data = list_community_plugins(
            session=self.session,
            status=status,
            category=category or None,
            group=group or None,
            plugin_type=plugin_type or None,
            min_rating=min_rating if min_rating > 0 else None,
            query=q or None,
            limit=limit,
            offset=offset,
        )
        self.success(data)


# ---------------------------------------------------------------------------
# Detail / Delete
# ---------------------------------------------------------------------------


@jwtauth
class CommunityPluginDetailHandler(APIRequestHandler):
    """Get or delete a single community plugin."""

    SUPPORTED_METHODS = ["GET", "DELETE", "OPTIONS"]

    def get(self, plugin_id):
        plugin_id = int(plugin_id)
        data = get_community_plugin(self.session, plugin_id)
        if data is None:
            raise APIError(404, "Plugin not found")
        self.success(data)

    def delete(self, plugin_id):
        plugin_id = int(plugin_id)
        ok = delete_community_plugin(self.session, plugin_id)
        if not ok:
            raise APIError(404, "Plugin not found")
        self.success(None)


# ---------------------------------------------------------------------------
# Test Run (smoke test only, not a real OWTF scan)
# ---------------------------------------------------------------------------


@jwtauth
class CommunityPluginTestRunHandler(APIRequestHandler):
    """Quick test run for a community plugin.

    Runs the plugin once in the sandbox against the given URL and returns
    the result inline. It skips OWTF's normal scan path (no target manager,
    no worklist, no saving). For a real scan, schedule the plugin through
    the regular runner like the built-in plugins.
    """

    SUPPORTED_METHODS = ["POST", "OPTIONS"]

    def post(self, plugin_id):
        """Test-run a community plugin.

        Body: ``{"target_url": "https://example.com"}``

        Response (note the ``non_persistent`` / ``is_test_run`` flags):
          ``{"status": "success", "data": {"success": true, "output": {...},
          "non_persistent": true, "is_test_run": true}}``
        """
        plugin_id = int(plugin_id)

        try:
            body = json.loads(self.request.body)
        except json.JSONDecodeError:
            raise APIError(400, "Request body must be valid JSON")

        target_url = body.get("target_url", "").strip()
        if not target_url:
            raise APIError(400, "'target_url' is required")

        # Basic URL sanity — must start with http(s)://
        if not (target_url.startswith("http://") or target_url.startswith("https://")):
            raise APIError(400, "'target_url' must start with http:// or https://")

        result = test_run_community_plugin(self.session, plugin_id, target_url)

        if not result.get("success"):
            self.set_status(422)
            self.finish({"status": "fail", "data": result})
            return

        self.success(result)


# Old name kept so the current UI's /run/ call still works until we
# update it to /test-run/.
CommunityPluginRunHandler = CommunityPluginTestRunHandler


# ---------------------------------------------------------------------------
# Approve / Reject  (admin operations — no extra auth layer for MVP)
# ---------------------------------------------------------------------------


@admin_required
class CommunityPluginApproveHandler(APIRequestHandler):
    """Approve a pending community plugin."""

    SUPPORTED_METHODS = ["POST", "OPTIONS"]

    def post(self, plugin_id):
        plugin_id = int(plugin_id)
        data = approve_community_plugin(self.session, plugin_id)
        if data is None:
            raise APIError(404, "Plugin not found")
        self.success(data)


@admin_required
class CommunityPluginRejectHandler(APIRequestHandler):
    """Reject a community plugin with a reason."""

    SUPPORTED_METHODS = ["POST", "OPTIONS"]

    def post(self, plugin_id):
        plugin_id = int(plugin_id)
        try:
            body = json.loads(self.request.body) if self.request.body else {}
        except json.JSONDecodeError:
            body = {}
        reason = body.get("reason", "")
        data = reject_community_plugin(self.session, plugin_id, reason)
        if data is None:
            raise APIError(404, "Plugin not found")
        self.success(data)
