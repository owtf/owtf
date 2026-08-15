"""
owtf.api.handlers.community_plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tornado handlers for the community plugin marketplace. Any
authenticated user can list approved plugins, upload, and see their
own uploads. Source viewing, delete, approve/reject, test-run, and
review history require an admin token.
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
    get_community_plugin_source,
    get_plugin_review_history,
    list_community_plugins,
    list_owner_plugins,
    reject_community_plugin,
    test_run_community_plugin,
    upload_community_plugin,
)
from owtf.models.user_plugin import APPROVAL_APPROVED, UserPlugin
from owtf.settings import (
    COMMUNITY_PLUGIN_DEFAULT_TIMEOUT,
    COMMUNITY_PLUGIN_MAX_MEMORY,
    COMMUNITY_PLUGIN_MAX_TIMEOUT,
    COMMUNITY_PLUGIN_MEMORY_LIMIT,
    COMMUNITY_PLUGIN_MIN_MEMORY,
    COMMUNITY_PLUGIN_MIN_TIMEOUT,
)

logger = logging.getLogger(__name__)

TEST_RUN_LIMIT = 3
TEST_RUN_WINDOW_SECONDS = 60
_test_run_calls = defaultdict(deque)


def _first_arg(handler, name, default=""):
    """First value of a Tornado request argument, decoded to str."""
    vals = handler.request.arguments.get(name)
    if not vals:
        return default
    return vals[0] if isinstance(vals[0], str) else vals[0].decode("utf-8")


def _check_test_run_rate_limit(user_id):
    """True if the caller is under the per-user budget, False otherwise."""
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
    """Parse uploader-supplied int in [low, high]. Empty means default. 400 otherwise."""
    if raw_value == "":
        return default
    try:
        value = int(raw_value)
    except ValueError:
        raise APIError(400, "{} must be an integer number of {}".format(field_name, unit))
    if not (low <= value <= high):
        raise APIError(400, "{} must be between {} and {} {}".format(field_name, low, high, unit))
    return value


@jwtauth
class CommunityPluginUploadHandler(APIRequestHandler):
    """Multipart plugin upload. 201 on success, 422 on validation failure."""

    SUPPORTED_METHODS = ["POST", "OPTIONS"]

    def post(self):
        try:
            execution_timeout = _parse_bounded_int(
                "execution_timeout",
                _first_arg(self, "execution_timeout", ""),
                COMMUNITY_PLUGIN_DEFAULT_TIMEOUT,
                COMMUNITY_PLUGIN_MIN_TIMEOUT,
                COMMUNITY_PLUGIN_MAX_TIMEOUT,
                "seconds",
            )
            memory_limit = _parse_bounded_int(
                "memory_limit",
                _first_arg(self, "memory_limit", ""),
                COMMUNITY_PLUGIN_MEMORY_LIMIT,
                COMMUNITY_PLUGIN_MIN_MEMORY,
                COMMUNITY_PLUGIN_MAX_MEMORY,
                "bytes",
            )

            files = self.request.files.get("plugin_file")
            if not files:
                raise APIError(400, "No plugin_file provided in the upload")

            file_info = files[0]
            result = upload_community_plugin(
                session=self.session,
                name=_first_arg(self, "name"),
                description=_first_arg(self, "description"),
                group=_first_arg(self, "group", "web"),
                plugin_type=_first_arg(self, "type", "passive"),
                author=_first_arg(self, "author"),
                file_body=file_info["body"],
                original_filename=file_info.get("filename", "plugin.py"),
                category=_first_arg(self, "category") or None,
                version=_first_arg(self, "version", "1.0.0"),
                tags=_first_arg(self, "tags") or None,
                execution_timeout=execution_timeout,
                memory_limit=memory_limit,
                is_public=_first_arg(self, "is_public", "true").lower() not in ("false", "0", "no"),
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


@jwtauth
class CommunityPluginListHandler(APIRequestHandler):
    """Non-admins see approved plugins only; admins can filter by any status."""

    SUPPORTED_METHODS = ["GET", "OPTIONS"]

    def get(self):
        requested_status = _first_arg(self, "status", APPROVAL_APPROVED)
        is_admin = user_is_admin(self.get_current_user_obj())

        # Non-admins locked to approved-only, so nobody can probe the
        # pending or rejected queues by guessing a status value.
        if not is_admin and requested_status != APPROVAL_APPROVED:
            raise APIError(
                403,
                "Only admins can filter by '{}'. Use /community-plugins/mine/ for your own uploads.".format(
                    requested_status
                ),
            )

        try:
            min_rating = float(_first_arg(self, "min_rating", "0") or 0)
        except ValueError:
            min_rating = 0.0
        try:
            limit = min(int(_first_arg(self, "limit", "50") or 50), 200)
        except ValueError:
            limit = 50
        try:
            offset = max(int(_first_arg(self, "offset", "0") or 0), 0)
        except ValueError:
            offset = 0

        self.success(
            list_community_plugins(
                session=self.session,
                status=requested_status,
                category=_first_arg(self, "category") or None,
                group=_first_arg(self, "group") or None,
                plugin_type=_first_arg(self, "type") or None,
                min_rating=min_rating if min_rating > 0 else None,
                query=_first_arg(self, "q") or None,
                limit=limit,
                offset=offset,
                as_admin=is_admin,
            )
        )


@jwtauth
class CommunityPluginDetailHandler(APIRequestHandler):
    """Plugin metadata. Non-admin, non-owner on pending/rejected returns 404.

    404 rather than 403 so plugin ids cannot be scraped to build a
    directory of other users' unpublished uploads.
    """

    SUPPORTED_METHODS = ["GET", "OPTIONS"]

    def get(self, plugin_id):
        plugin_id = int(plugin_id)
        current_user = self.get_current_user_obj()
        is_admin = user_is_admin(current_user)

        plugin = self.session.query(UserPlugin).get(plugin_id)
        if plugin is None:
            raise APIError(404, "Plugin not found")

        current_user_id = getattr(current_user, "id", None) if current_user is not None else None
        is_owner = current_user_id is not None and plugin.user_id == current_user_id
        is_approved = plugin.approval_status == APPROVAL_APPROVED

        if not is_admin and not is_owner and not is_approved:
            raise APIError(404, "Plugin not found")

        if is_admin:
            self.success(plugin.to_admin_dict())
        elif is_owner:
            self.success(plugin.to_owner_dict())
        else:
            self.success(plugin.to_dict())


@admin_required
class CommunityPluginSourceHandler(APIRequestHandler):
    """Return plugin source. File is read server-side; file_path never leaves."""

    SUPPORTED_METHODS = ["GET", "OPTIONS"]

    def get(self, plugin_id):
        data = get_community_plugin_source(self.session, int(plugin_id))
        if data is None:
            raise APIError(404, "Plugin not found")
        self.success(data)


@admin_required
class CommunityPluginDeleteHandler(APIRequestHandler):
    """Delete a plugin record and its on-disk file. Own URL so
    admin_required attaches to the class."""

    SUPPORTED_METHODS = ["DELETE", "OPTIONS"]

    def delete(self, plugin_id):
        if not delete_community_plugin(self.session, int(plugin_id)):
            raise APIError(404, "Plugin not found")
        self.success(None)


@admin_required
class CommunityPluginTestRunHandler(APIRequestHandler):
    """Run an approved plugin once against a URL. Rate-limited per user, not saved."""

    SUPPORTED_METHODS = ["POST", "OPTIONS"]

    def post(self, plugin_id):
        if not _check_test_run_rate_limit(self.get_current_user_id()):
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

        try:
            body = json.loads(self.request.body)
        except json.JSONDecodeError:
            raise APIError(400, "Request body must be valid JSON")

        target_url = body.get("target_url", "").strip()
        if not target_url:
            raise APIError(400, "'target_url' is required")
        if not (target_url.startswith("http://") or target_url.startswith("https://")):
            raise APIError(400, "'target_url' must start with http:// or https://")

        result = test_run_community_plugin(self.session, int(plugin_id), target_url)
        if not result.get("success"):
            self.set_status(422)
            self.finish({"status": "fail", "data": result})
            return
        self.success(result)


@admin_required
class CommunityPluginApproveHandler(APIRequestHandler):
    SUPPORTED_METHODS = ["POST", "OPTIONS"]

    def post(self, plugin_id):
        data = approve_community_plugin(self.session, int(plugin_id), reviewer_id=self.get_current_user_id())
        if data is None:
            raise APIError(404, "Plugin not found")
        self.success(data)


@admin_required
class CommunityPluginRejectHandler(APIRequestHandler):
    SUPPORTED_METHODS = ["POST", "OPTIONS"]

    def post(self, plugin_id):
        try:
            body = json.loads(self.request.body) if self.request.body else {}
        except json.JSONDecodeError:
            body = {}
        data = reject_community_plugin(
            self.session,
            int(plugin_id),
            body.get("reason", ""),
            reviewer_id=self.get_current_user_id(),
        )
        if data is None:
            raise APIError(404, "Plugin not found")
        self.success(data)


@admin_required
class CommunityPluginReviewHistoryHandler(APIRequestHandler):
    """Timeline of upload + review events. Called review history rather
    than audit log because there is no append-only audit table."""

    SUPPORTED_METHODS = ["GET", "OPTIONS"]

    def get(self, plugin_id):
        plugin_id = int(plugin_id)
        events = get_plugin_review_history(self.session, plugin_id)
        if events is None:
            raise APIError(404, "Plugin not found")
        self.success({"plugin_id": plugin_id, "events": events})


@jwtauth
class CommunityPluginMeHandler(APIRequestHandler):
    """Current user profile. The UI uses is_admin to decide tab visibility."""

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


@jwtauth
class CommunityPluginMineHandler(APIRequestHandler):
    """Uploads by the current user (owner view, so rejection reasons show)."""

    SUPPORTED_METHODS = ["GET", "OPTIONS"]

    def get(self):
        user_id = self.get_current_user_id()
        if user_id is None:
            raise APIError(401, "Not authenticated")
        self.success(list_owner_plugins(self.session, user_id))
