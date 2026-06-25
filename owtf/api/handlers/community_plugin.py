"""
owtf.api.handlers.community_plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tornado request handlers for the Community Plugin Ecosystem.

Endpoints
---------
POST   /api/v1/community-plugins/upload         — upload a .py plugin
GET    /api/v1/community-plugins/                — list (filters: status, group, type, q ...)
GET    /api/v1/community-plugins/<id>/           — plugin details (incl. source code)
POST   /api/v1/community-plugins/<id>/test-run/  — admin-only smoke test (rate-limited)
POST   /api/v1/community-plugins/<id>/approve/   — admin
POST   /api/v1/community-plugins/<id>/reject/    — admin, body: {"reason": "..."}
GET    /api/v1/community-plugins/<id>/audit/log/ — admin, lifecycle events
GET    /api/v1/community-plugins/me/             — current user profile (id, name, is_admin)
DELETE /api/v1/community-plugins/<id>/           — admin, delete plugin record + file
"""

import json
import logging
import time
from collections import defaultdict, deque

from owtf.api.handlers.base import APIRequestHandler
from owtf.api.handlers.jwtauth import admin_required, jwtauth, user_is_admin
from owtf.lib.exceptions import APIError
from owtf.managers.community_plugin import (
    approve_community_plugin,
    delete_community_plugin,
    get_community_plugin,
    get_plugin_audit_log,
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
    "CommunityPluginTestRunHandler",
    "CommunityPluginApproveHandler",
    "CommunityPluginRejectHandler",
    "CommunityPluginAuditLogHandler",
    "CommunityPluginMeHandler",
]

# ---------------------------------------------------------------------------
# Rate limiter (in-memory, per-process). Good enough for single-worker MVP.
# ---------------------------------------------------------------------------

TEST_RUN_LIMIT = 3  # calls
TEST_RUN_WINDOW_SECONDS = 60
_test_run_calls: "defaultdict[object, deque]" = defaultdict(deque)


def _check_test_run_rate_limit(user_id) -> bool:
    """Return True if the caller is within budget, False if rate-limited."""
    key = user_id if user_id is not None else "anonymous"
    now = time.monotonic()
    bucket = _test_run_calls[key]
    while bucket and now - bucket[0] > TEST_RUN_WINDOW_SECONDS:
        bucket.popleft()
    if len(bucket) >= TEST_RUN_LIMIT:
        return False
    bucket.append(now)
    return True


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------


@jwtauth
class CommunityPluginUploadHandler(APIRequestHandler):
    """Accept a multipart plugin upload, validate it, and store it."""

    SUPPORTED_METHODS = ["POST", "OPTIONS"]

    def post(self):
        """Upload a community plugin.

        **Response** (success):
          ``{"status": "success", "data": {"plugin": {...}, "warnings": [...]}}``

        **Response** (validation error):
          HTTP 422 — ``{"status": "fail", "data": {"errors": [...], "violations": [...]}}``
        """
        try:

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

            files = self.request.files.get("plugin_file")
            if not files:
                raise APIError(400, "No plugin_file provided in the upload")

            file_info = files[0]
            file_body = file_info["body"]
            original_filename = file_info.get("filename", "plugin.py")

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
                user_id=self.get_current_user_id(),
            )

            if not result["success"]:
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
            self.success(
                {
                    "plugin": result["plugin"],
                    "warnings": result["warnings"],
                    "message": "Plugin uploaded successfully and is pending admin review.",
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
        # Include source code so the admin "View Code" button works without
        # a second round-trip.
        try:
            with open(data["file_path"], "r", encoding="utf-8") as fh:
                data["source_code"] = fh.read()
        except OSError:
            data["source_code"] = None
        self.success(data)

    def delete(self, plugin_id):
        plugin_id = int(plugin_id)
        ok = delete_community_plugin(self.session, plugin_id)
        if not ok:
            raise APIError(404, "Plugin not found")
        self.success(None)


# ---------------------------------------------------------------------------
# Test-Run (admin-only, rate-limited smoke test)
# ---------------------------------------------------------------------------


@admin_required
class CommunityPluginTestRunHandler(APIRequestHandler):
    """Smoke-test a community plugin against a URL.

    Loads the plugin via the standard module loader and runs it once
    against the given URL, returning the result inline. Skips OWTF's
    normal scan path (no target manager, no worklist, no saving) and is
    rate-limited per user.
    """

    SUPPORTED_METHODS = ["POST", "OPTIONS"]

    def post(self, plugin_id):
        user_id = self.get_current_user_id()
        if not _check_test_run_rate_limit(user_id):
            self.set_status(429)
            self.finish(
                {
                    "status": "fail",
                    "data": {
                        "error": "Too many test-run requests. Limit is {} per {}s.".format(
                            TEST_RUN_LIMIT, TEST_RUN_WINDOW_SECONDS
                        )
                    },
                }
            )
            return

        plugin_id = int(plugin_id)

        try:
            body = json.loads(self.request.body)
        except json.JSONDecodeError:
            raise APIError(400, "Request body must be valid JSON")

        target_url = body.get("target_url", "").strip()
        if not target_url:
            raise APIError(400, "'target_url' is required")
        if not (target_url.startswith("http://") or target_url.startswith("https://")):
            raise APIError(400, "'target_url' must start with http:// or https://")

        result = test_run_community_plugin(self.session, plugin_id, target_url)

        if not result.get("success"):
            self.set_status(422)
            self.finish({"status": "fail", "data": result})
            return

        self.success(result)


# Alias kept so the original /run/ path still resolves until the UI
# fully switches to /test-run/.
CommunityPluginRunHandler = CommunityPluginTestRunHandler


# ---------------------------------------------------------------------------
# Approve / Reject (admin)
# ---------------------------------------------------------------------------


@admin_required
class CommunityPluginApproveHandler(APIRequestHandler):
    """Approve a pending community plugin."""

    SUPPORTED_METHODS = ["POST", "OPTIONS"]

    def post(self, plugin_id):
        plugin_id = int(plugin_id)
        data = approve_community_plugin(self.session, plugin_id, reviewer_id=self.get_current_user_id())
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
        data = reject_community_plugin(self.session, plugin_id, reason, reviewer_id=self.get_current_user_id())
        if data is None:
            raise APIError(404, "Plugin not found")
        self.success(data)


# ---------------------------------------------------------------------------
# Audit Log (admin)
# ---------------------------------------------------------------------------


@admin_required
class CommunityPluginAuditLogHandler(APIRequestHandler):
    """Return the chronological lifecycle events for a plugin."""

    SUPPORTED_METHODS = ["GET", "OPTIONS"]

    def get(self, plugin_id):
        plugin_id = int(plugin_id)
        events = get_plugin_audit_log(self.session, plugin_id)
        if events is None:
            raise APIError(404, "Plugin not found")
        self.success({"plugin_id": plugin_id, "events": events})


# ---------------------------------------------------------------------------
# Me (current-user profile — used by the UI to decide admin tab visibility)
# ---------------------------------------------------------------------------


@jwtauth
class CommunityPluginMeHandler(APIRequestHandler):
    """Expose the logged-in user's profile (id, name, email, is_admin)."""

    SUPPORTED_METHODS = ["GET", "OPTIONS"]

    def get(self):
        user = self.get_current_user_obj()
        if user is None:
            raise APIError(401, "Not authenticated")
        self.success(
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "is_admin": user_is_admin(user),
            }
        )
