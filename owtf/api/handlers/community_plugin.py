"""
owtf.api.handlers.community_plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tornado request handlers for the Community Plugin Ecosystem.

Trust boundaries
----------------
Any authenticated user can list approved plugins, see their public
metadata, upload a new plugin, and see their own uploads. Everything
else (source viewing, deletion, approve/reject, test-run, review
history, admin-scoped listings) needs an admin token.

Endpoints
---------
POST   /api/v1/community-plugins/upload                 auth,  upload a .py plugin
GET    /api/v1/community-plugins/                       auth,  list approved (public metadata only)
GET    /api/v1/community-plugins/<id>/                  auth,  plugin metadata (no source, no file_path)
GET    /api/v1/community-plugins/<id>/source/           admin, plugin source code for review
DELETE /api/v1/community-plugins/<id>/delete/           admin, delete plugin record + file
POST   /api/v1/community-plugins/<id>/test-run/         admin, rate-limited smoke test
POST   /api/v1/community-plugins/<id>/approve/          admin
POST   /api/v1/community-plugins/<id>/reject/           admin, body: {"reason": "..."}
GET    /api/v1/community-plugins/<id>/review-history/   admin, upload + review timeline
GET    /api/v1/community-plugins/me/                    auth,  current user profile (id, name, is_admin)
GET    /api/v1/community-plugins/mine/                  auth,  current user's uploads (owner view)
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
    get_community_plugin_source,
    get_plugin_review_history,
    list_community_plugins,
    list_owner_plugins,
    reject_community_plugin,
    test_run_community_plugin,
    upload_community_plugin,
)
from owtf.models.user_plugin import APPROVAL_APPROVED
from owtf.settings import (
    COMMUNITY_PLUGIN_DEFAULT_TIMEOUT,
    COMMUNITY_PLUGIN_MAX_MEMORY,
    COMMUNITY_PLUGIN_MAX_TIMEOUT,
    COMMUNITY_PLUGIN_MEMORY_LIMIT,
    COMMUNITY_PLUGIN_MIN_MEMORY,
    COMMUNITY_PLUGIN_MIN_TIMEOUT,
)

logger = logging.getLogger(__name__)

__all__ = [
    "CommunityPluginUploadHandler",
    "CommunityPluginListHandler",
    "CommunityPluginDetailHandler",
    "CommunityPluginSourceHandler",
    "CommunityPluginDeleteHandler",
    "CommunityPluginRunHandler",
    "CommunityPluginTestRunHandler",
    "CommunityPluginApproveHandler",
    "CommunityPluginRejectHandler",
    "CommunityPluginReviewHistoryHandler",
    "CommunityPluginMeHandler",
    "CommunityPluginMineHandler",
]

# Statuses a non-admin caller is allowed to filter on.
_PUBLIC_STATUSES = {APPROVAL_APPROVED}

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


def _parse_bounded_int(field_name, raw_value, default, low, high, unit):
    """Turn an uploader-supplied string into an int inside [low, high].

    An empty string means the uploader did not send the field, so we
    fall back to ``default``. A non-integer or out-of-range value is
    surfaced as a 400 so the uploader knows their value was rejected
    instead of silently replaced.
    """
    if raw_value == "":
        return default
    try:
        value = int(raw_value)
    except ValueError:
        raise APIError(
            400,
            "{} must be an integer number of {}".format(field_name, unit),
        )
    if not (low <= value <= high):
        raise APIError(
            400,
            "{} must be between {} and {} {}".format(field_name, low, high, unit),
        )
    return value


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

            # execution_timeout and memory_limit come from the uploader so
            # they are treated as untrusted. We accept them only if they
            # parse as an int and sit inside the configured bounds. A bad
            # value returns 400 instead of silently falling back, so the
            # uploader knows their number was rejected.
            execution_timeout = _parse_bounded_int(
                "execution_timeout",
                _field("execution_timeout", ""),
                COMMUNITY_PLUGIN_DEFAULT_TIMEOUT,
                COMMUNITY_PLUGIN_MIN_TIMEOUT,
                COMMUNITY_PLUGIN_MAX_TIMEOUT,
                "seconds",
            )
            memory_limit = _parse_bounded_int(
                "memory_limit",
                _field("memory_limit", ""),
                COMMUNITY_PLUGIN_MEMORY_LIMIT,
                COMMUNITY_PLUGIN_MIN_MEMORY,
                COMMUNITY_PLUGIN_MAX_MEMORY,
                "bytes",
            )

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
    """List and search community plugins.

    Non-admin callers can only see approved plugins. Any other status
    filter (pending, rejected, or a bogus value) returns 403. Admins
    can request any status and get the admin serializer.
    """

    SUPPORTED_METHODS = ["GET", "OPTIONS"]

    def get(self):
        def _qparam(name, default=None):
            vals = self.request.arguments.get(name)
            if vals:
                return vals[0] if isinstance(vals[0], str) else vals[0].decode("utf-8")
            return default

        requested_status = _qparam("status", APPROVAL_APPROVED)
        is_admin = user_is_admin(self.get_current_user_obj())

        # Non-admins are locked to approved-only. Anything else returns
        # 403 so nobody can probe pending or rejected queues by guessing
        # a status value.
        if not is_admin and requested_status not in _PUBLIC_STATUSES:
            raise APIError(
                403,
                "Only admins can filter by '{}'. Use /community-plugins/mine/ for your own uploads.".format(
                    requested_status
                ),
            )

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
            status=requested_status,
            category=category or None,
            group=group or None,
            plugin_type=plugin_type or None,
            min_rating=min_rating if min_rating > 0 else None,
            query=q or None,
            limit=limit,
            offset=offset,
            as_admin=is_admin,
        )
        self.success(data)


# ---------------------------------------------------------------------------
# Detail (public metadata) / Source (admin) / Delete (admin)
# ---------------------------------------------------------------------------


@jwtauth
class CommunityPluginDetailHandler(APIRequestHandler):
    """Return metadata for a single community plugin.

    Non-admins get the safe public dict (no file_path, no source_code,
    no reviewer trail). Admins get the admin dict so review UIs can show
    rejection reasons and reviewer info in one call. Source code is
    served only by CommunityPluginSourceHandler.
    """

    SUPPORTED_METHODS = ["GET", "OPTIONS"]

    def get(self, plugin_id):
        plugin_id = int(plugin_id)
        is_admin = user_is_admin(self.get_current_user_obj())
        data = get_community_plugin(self.session, plugin_id, as_admin=is_admin)
        if data is None:
            raise APIError(404, "Plugin not found")
        self.success(data)


@admin_required
class CommunityPluginSourceHandler(APIRequestHandler):
    """Return the source code of a plugin. Admin only.

    Reads the file server-side and returns its contents so the review UI
    can show the code without knowing the file's path on disk.
    """

    SUPPORTED_METHODS = ["GET", "OPTIONS"]

    def get(self, plugin_id):
        plugin_id = int(plugin_id)
        data = get_community_plugin_source(self.session, plugin_id)
        if data is None:
            raise APIError(404, "Plugin not found")
        self.success(data)


@admin_required
class CommunityPluginDeleteHandler(APIRequestHandler):
    """Delete a community plugin record and its file. Admin only.

    Uses the DELETE method but sits on its own URL, separate from the
    detail GET. Tornado routes by URL first, so keeping them on separate
    URLs lets us apply admin_required at the class level.
    """

    SUPPORTED_METHODS = ["DELETE", "OPTIONS"]

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
# Review History (admin)
# ---------------------------------------------------------------------------


@admin_required
class CommunityPluginReviewHistoryHandler(APIRequestHandler):
    """Return the upload and review timeline for a plugin.

    Called it a review history rather than an audit log because the
    events are derived from the plugin row's own timestamps, not from
    an append-only audit table. An audit log implies stronger integrity
    guarantees than that.
    """

    SUPPORTED_METHODS = ["GET", "OPTIONS"]

    def get(self, plugin_id):
        plugin_id = int(plugin_id)
        events = get_plugin_review_history(self.session, plugin_id)
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


# ---------------------------------------------------------------------------
# Mine (uploader's own plugins across all statuses)
# ---------------------------------------------------------------------------


@jwtauth
class CommunityPluginMineHandler(APIRequestHandler):
    """List the plugins uploaded by the current user.

    Returns owner-view dicts so the uploader sees rejection_reason for
    any of their own rejected plugins. The filter uses the user id from
    the JWT, so nobody can see another user's uploads through this
    endpoint.
    """

    SUPPORTED_METHODS = ["GET", "OPTIONS"]

    def get(self):
        user_id = self.get_current_user_id()
        if user_id is None:
            raise APIError(401, "Not authenticated")
        self.success(list_owner_plugins(self.session, user_id))
