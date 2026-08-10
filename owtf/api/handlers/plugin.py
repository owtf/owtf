"""
owtf.api.handlers.plugin
~~~~~~~~~~~~~~~~~~~~~~~~

"""

import collections
import logging
import os
import re
import unicodedata
import uuid

from owtf.api.handlers.base import APIRequestHandler
from owtf.api.handlers.jwtauth import jwtauth
from owtf.constants import MAPPINGS
from owtf.lib import exceptions
from owtf.lib.exceptions import APIError
from owtf.managers.plugin import get_all_plugin_dicts, get_types_for_plugin_group
from owtf.managers.poutput import delete_all_poutput, get_all_poutputs, update_poutput
from owtf.models.test_group import TestGroup
from owtf.models.user_plugin import (
    APPROVAL_PENDING,
    VALID_GROUPS,
    VALID_TYPES,
    UserPlugin,
)
from owtf.plugin.validator import PluginValidator
from owtf.settings import (
    COMMUNITY_PLUGINS_DIR,
    PLUGIN_ALLOWED_EXTENSIONS,
    PLUGIN_UPLOAD_MAX_SIZE,
)

logger = logging.getLogger(__name__)

__all__ = ["PluginNameOutput", "PluginDataHandler", "PluginOutputHandler", "PluginUploadHandler"]

_SAFE_STEM_RE = re.compile(r"[^\w\-. ]")
_MAX_STEM = 80


def _make_upload_path(name: str) -> str:
    """Return a unique, collision-free absolute path for a plugin upload."""
    try:
        normalised = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    except Exception:
        normalised = name
    stem = _SAFE_STEM_RE.sub("_", normalised).strip(". ")[:_MAX_STEM] or "plugin"
    os.makedirs(COMMUNITY_PLUGINS_DIR, exist_ok=True)
    return os.path.join(COMMUNITY_PLUGINS_DIR, "{}_{}{}".format(stem, uuid.uuid4().hex[:8], ".py"))


@jwtauth
class PluginDataHandler(APIRequestHandler):
    """Get completed plugin output data from the DB."""

    SUPPORTED_METHODS = ["GET"]

    # TODO: Creation of user plugins
    def get(self, plugin_group=None, plugin_type=None, plugin_code=None):
        """Get plugin data based on user filter data.

        **Example request**:

        .. sourcecode:: http

            GET /api/v1/plugins/?group=web&group=network HTTP/1.1
            Accept: application/json, text/javascript, */*
            X-Requested-With: XMLHttpRequest

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Encoding: gzip
            Vary: Accept-Encoding
            Content-Type: application/json

            {
                "status": "success",
                "data": [
                    {
                        "file": "Old_Backup_and_Unreferenced_Files@OWTF-CM-006.py",
                        "code": "OWTF-CM-006",
                        "group": "web",
                        "attr": null,
                        "title": "Old Backup And Unreferenced Files",
                        "key": "external@OWTF-CM-006",
                        "descrip": "Plugin to assist manual testing",
                        "min_time": null,
                        "type": "external",
                        "name": "Old_Backup_and_Unreferenced_Files"
                    },
                    {
                        "file": "Old_Backup_and_Unreferenced_Files@OWTF-CM-006.py",
                        "code": "OWTF-CM-006",
                        "group": "web",
                        "attr": null,
                        "title": "Old Backup And Unreferenced Files",
                        "key": "passive@OWTF-CM-006",
                        "descrip": "Google Hacking for juicy files",
                        "min_time": null,
                        "type": "passive",
                        "name": "Old_Backup_and_Unreferenced_Files"
                    }
                ]
            }
        """
        # for_api=True strips server-side fields (file_path, source,
        # execution_timeout, memory_limit) from community plugin entries
        # before they are handed back to the client. The trust model
        # guarantees file_path never leaves the server; this endpoint is
        # the only path that merges community plugins into a client-facing
        # response, so the stripping has to happen here.
        try:
            filter_data = dict(self.request.arguments)
            if not plugin_group:  # Check if plugin_group is present in url
                self.success(get_all_plugin_dicts(self.session, filter_data, for_api=True))
            if plugin_group and (not plugin_type) and (not plugin_code):
                filter_data.update({"group": plugin_group})
                self.success(get_all_plugin_dicts(self.session, filter_data, for_api=True))
            if plugin_group and plugin_type and (not plugin_code):
                if plugin_type not in get_types_for_plugin_group(self.session, plugin_group):
                    raise APIError(422, "Plugin type not found in selected plugin group")
                filter_data.update({"type": plugin_type, "group": plugin_group})
                self.success(get_all_plugin_dicts(self.session, filter_data, for_api=True))
            if plugin_group and plugin_type and plugin_code:
                if plugin_type not in get_types_for_plugin_group(self.session, plugin_group):
                    raise APIError(422, "Plugin type not found in selected plugin group")
                filter_data.update({"type": plugin_type, "group": plugin_group, "code": plugin_code})
                # This combination will be unique, so have to return a dict
                results = get_all_plugin_dicts(self.session, filter_data, for_api=True)
                if results:
                    self.success(results[0])
                else:
                    raise APIError(500, "Cannot get any plugin dict")
        except exceptions.InvalidTargetReference:
            raise APIError(400, "Invalid target provided.")


@jwtauth
class PluginNameOutput(APIRequestHandler):
    """Get the scan results for a target."""

    SUPPORTED_METHODS = ["GET"]

    def get(self, target_id=None):
        """Retrieve scan results for a target.

        **Example request**:

        .. sourcecode:: http

            GET /api/v1/targets/2/poutput/names/ HTTP/1.1
            Accept: */*
            Accept-Encoding: gzip, deflate
            X-Requested-With: XMLHttpRequest

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Encoding: gzip
            Content-Type: application/json; charset=UTF-8

            {
                "status": "success",
                "data": {
                    "OWTF-AT-004": {
                        "data": [
                            {
                                "status": "Successful",
                                "owtf_rank": -1,
                                "plugin_group": "web",
                                "start_time": "01/04/2018-14:05",
                                "target_id": 2,
                                "run_time": "0s,   1ms",
                                "user_rank": -1,
                                "plugin_key": "external@OWTF-AT-004",
                                "id": 5,
                                "plugin_code": "OWTF-AT-004",
                                "user_notes": null,
                                "output_path": null,
                                "end_time": "01/04/2018-14:05",
                                "error": null,
                                "plugin_type": "external"
                            }
                        ],
                        "details": {
                            "priority": 99,
                            "code": "OWTF-AT-004",
                            "group": "web",
                            "mappings": {
                                "OWASP_V3": [
                                    "OWASP-AT-004",
                                    "Brute Force Testing"
                                ],
                                "OWASP_V4": [
                                    "OTG-AUTHN-003",
                                    "Testing for Weak lock out mechanism"
                                ],
                                "CWE": [
                                    "CWE-16",
                                    "Configuration - Brute force"
                                ],
                                "NIST": [
                                    "IA-6",
                                    "Authenticator Feedback - Brute force"
                                ],
                                "OWASP_TOP_10": [
                                    "A5",
                                    "Security Misconfiguration - Brute force"
                                ]
                            },
                            "hint": "Brute Force",
                            "url": "https://www.owasp.org/index.php/Testing_for_Brute_Force_(OWASP-AT-004)",
                            "descrip": "Testing for Brute Force"
                        }
                    },
                }
            }
        """
        try:
            filter_data = dict(self.request.arguments)
            results = get_all_poutputs(self.session, filter_data, target_id=int(target_id), inc_output=False)

            # Get test groups as well, for names and info links
            groups = {}
            for group in TestGroup.get_all(self.session):
                group["mappings"] = MAPPINGS.get(group["code"], {})
                groups[group["code"]] = group

            dict_to_return = {}
            for item in results:
                if item["plugin_code"] in dict_to_return:
                    dict_to_return[item["plugin_code"]]["data"].append(item)
                else:
                    ini_list = []
                    ini_list.append(item)
                    dict_to_return[item["plugin_code"]] = {}
                    dict_to_return[item["plugin_code"]]["data"] = ini_list
                    dict_to_return[item["plugin_code"]]["details"] = groups[item["plugin_code"]]
            dict_to_return = collections.OrderedDict(sorted(dict_to_return.items()))
            if results:
                self.success(dict_to_return)
            else:
                raise APIError(500, "Cannot fetch plugin outputs")

        except exceptions.InvalidTargetReference:
            raise APIError(400, "Invalid target provided")
        except exceptions.InvalidParameterType:
            raise APIError(400, "Invalid parameter type provided")


@jwtauth
class PluginOutputHandler(APIRequestHandler):
    """Filter plugin output data."""

    SUPPORTED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]

    def get(self, target_id=None, plugin_group=None, plugin_type=None, plugin_code=None):
        """Get the plugin output based on query filter params.

        **Example request**:

        .. sourcecode:: http

            GET /api/v1/targets/2/poutput/?plugin_code=OWTF-AJ-001 HTTP/1.1
            X-Requested-With: XMLHttpRequest

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "success",
                "data": [
                    {
                        "status": "Successful",
                        "owtf_rank": -1,
                        "plugin_group": "web",
                        "start_time": "01/04/2018-14:06",
                        "target_id": 2,
                        "run_time": "0s,   1ms",
                        "user_rank": -1,
                        "plugin_key": "external@OWTF-AJ-001",
                        "id": 27,
                        "plugin_code": "OWTF-AJ-001",
                        "user_notes": null,
                        "output_path": null,
                        "end_time": "01/04/2018-14:06",
                        "error": null,
                        "output": "Intended to show helpful info in the future",
                        "plugin_type": "external"
                    }
                ]
            }
        """
        try:
            filter_data = dict(self.request.arguments)
            if plugin_group and (not plugin_type):
                filter_data.update({"plugin_group": plugin_group})
            if plugin_type and plugin_group and (not plugin_code):
                if plugin_type not in get_types_for_plugin_group(self.session, plugin_group):
                    raise APIError(422, "Plugin type not found in selected plugin group")
                filter_data.update({"plugin_type": plugin_type, "plugin_group": plugin_group})
            if plugin_type and plugin_group and plugin_code:
                if plugin_type not in get_types_for_plugin_group(self.session, plugin_group):
                    raise APIError(422, "Plugin type not found in selected plugin group")
                filter_data.update(
                    {"plugin_type": plugin_type, "plugin_group": plugin_group, "plugin_code": plugin_code}
                )
            results = get_all_poutputs(self.session, filter_data, target_id=int(target_id), inc_output=True)
            if results:
                self.success(results)
            else:
                raise APIError(500, "Cannot fetch plugin outputs")

        except exceptions.InvalidTargetReference:
            raise APIError(400, "Invalid target reference provided")
        except exceptions.InvalidParameterType:
            raise APIError(400, "Invalid parameter type provided")

    def post(self, target_url):
        raise APIError(405)

    def put(self):
        raise APIError(405)

    def patch(self, target_id=None, plugin_group=None, plugin_type=None, plugin_code=None):
        """Modify plugin output data like ranking, severity, notes, etc.

        **Example request**:

        .. sourcecode:: http

            PATCH /api/v1/targets/2/poutput/web/external/OWTF-CM-008 HTTP/1.1
            Content-Type: application/x-www-form-urlencoded; charset=UTF-8
            X-Requested-With: XMLHttpRequest


            user_rank=0

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Length: 0
            Content-Type: application/json

            {
                "status": "success",
                "data": null
            }
        """
        try:
            if (not target_id) or (not plugin_group) or (not plugin_type) or (not plugin_code):
                raise APIError(400, "Missing requirement arguments")
            else:
                patch_data = dict(self.request.arguments)
                update_poutput(self.session, plugin_group, plugin_type, plugin_code, patch_data, target_id=target_id)
                self.success(None)
        except exceptions.InvalidTargetReference:
            raise APIError(400, "Invalid target reference provided")
        except exceptions.InvalidParameterType:
            raise APIError(400, "Invalid parameter type provided")

    def delete(self, target_id=None, plugin_group=None, plugin_type=None, plugin_code=None):
        """Delete a plugin output.

        **Example request**:

        .. sourcecode:: http

            DELETE /api/v1/targets/2/poutput/web/external/OWTF-AJ-001 HTTP/1.1
            X-Requested-With: XMLHttpRequest

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json
            {
                "status": "success",
                "data": null
            }
        """
        try:
            filter_data = dict(self.request.arguments)
            if not plugin_group:  # First check if plugin_group is present in url
                delete_all_poutput(self.session, filter_data, target_id=int(target_id))
            if plugin_group and (not plugin_type):
                filter_data.update({"plugin_group": plugin_group})
                delete_all_poutput(self.session, filter_data, target_id=int(target_id))
            if plugin_type and plugin_group and (not plugin_code):
                if plugin_type not in get_types_for_plugin_group(self.session, plugin_group):
                    raise APIError(422, "Plugin type not found in the selected plugin group")
                filter_data.update({"plugin_type": plugin_type, "plugin_group": plugin_group})
                delete_all_poutput(self.session, filter_data, target_id=int(target_id))
            if plugin_type and plugin_group and plugin_code:
                if plugin_type not in get_types_for_plugin_group(self.session, plugin_group):
                    raise APIError(422, "Plugin type not found in the selected plugin group")
                filter_data.update(
                    {"plugin_type": plugin_type, "plugin_group": plugin_group, "plugin_code": plugin_code}
                )
                delete_all_poutput(self.session, filter_data, target_id=int(target_id))
                self.success(None)
        except exceptions.InvalidTargetReference:
            raise APIError(400, "Invalid target reference provided")
        except exceptions.InvalidParameterType:
            raise APIError(400, "Invalid parameter type provided")


@jwtauth
class PluginUploadHandler(APIRequestHandler):
    """Upload a community plugin via POST /api/v1/plugins/upload.

    Accepts a multipart/form-data request containing a .py file and metadata.
    The file is scanned with PluginValidator (AST-based static analysis) before
    it is saved to disk.  On passing all checks the metadata is written to the
    UserPlugin table with approval_status='pending' so an administrator must
    approve the plugin before it becomes visible to other users.

    **Request** (multipart/form-data):
      - name         (required, 3-128 chars)
      - description  (required)
      - group        (required: web | network | auxiliary, default web)
      - type         (required: active | passive | semi_passive | external | grep, default passive)
      - author       (required)
      - plugin_file  (required, .py file, max 512 KB)
      - category     (optional)
      - version      (optional, default "1.0.0")
      - tags         (optional, comma-separated)

    **Response** (success, HTTP 201):
      {"status": "success", "data": {"plugin": {...}, "warnings": [...]}}

    **Response** (validation failure, HTTP 422):
      {"status": "fail", "data": {"errors": [...], "violations": [...], "warnings": [...]}}
    """

    SUPPORTED_METHODS = ["POST", "OPTIONS"]

    def post(self):
        try:

            def _field(name, default=""):
                vals = self.request.arguments.get(name)
                if vals:
                    v = vals[0]
                    return v if isinstance(v, str) else v.decode("utf-8")
                return default

            name = _field("name").strip()
            description = _field("description").strip()
            group = _field("group", "web")
            plugin_type = _field("type", "passive")
            author = _field("author").strip()
            category = (_field("category") or "").strip() or None
            version = (_field("version", "1.0.0") or "1.0.0").strip()
            tags_raw = _field("tags") or None

            # ── 1. File presence ──────────────────────────────────────────
            files = self.request.files.get("plugin_file")
            if not files:
                raise APIError(400, "No plugin_file provided in the upload")

            file_info = files[0]
            file_body = file_info["body"]
            original_filename = file_info.get("filename", "plugin.py")

            # ── 2. Basic file checks ──────────────────────────────────────
            errors = []
            _, ext = os.path.splitext(original_filename)
            if ext.lower() not in PLUGIN_ALLOWED_EXTENSIONS:
                errors.append("Invalid file type '{}'. Only .py files are accepted.".format(ext))

            if len(file_body) > PLUGIN_UPLOAD_MAX_SIZE:
                errors.append("Plugin file exceeds the maximum size of {} KB.".format(PLUGIN_UPLOAD_MAX_SIZE // 1024))

            # ── 3. Metadata validation ────────────────────────────────────
            if not name or len(name) < 3:
                errors.append("'name' must be at least 3 characters")
            elif len(name) > 128:
                errors.append("'name' must not exceed 128 characters")

            if not description:
                errors.append("'description' is required")

            if group not in VALID_GROUPS:
                errors.append("'group' must be one of: {}".format(", ".join(sorted(VALID_GROUPS))))

            if plugin_type not in VALID_TYPES:
                errors.append("'type' must be one of: {}".format(", ".join(sorted(VALID_TYPES))))

            if not author:
                errors.append("'author' is required")
            elif len(author) > 128:
                errors.append("'author' must not exceed 128 characters")

            if errors:
                self.set_status(422)
                self.finish(
                    {
                        "status": "fail",
                        "data": {"errors": errors, "violations": [], "warnings": []},
                    }
                )
                return

            # ── 4. Duplicate name check ───────────────────────────────────
            if UserPlugin.get_by_name(self.session, name):
                self.set_status(422)
                self.finish(
                    {
                        "status": "fail",
                        "data": {
                            "errors": ["A plugin named '{}' already exists. Choose a unique name.".format(name)],
                            "violations": [],
                            "warnings": [],
                        },
                    }
                )
                return

            # ── 5. AST security scan ──────────────────────────────────────
            validation = PluginValidator.validate_bytes(file_body, filename=original_filename)
            if not validation.passed:
                logger.warning(
                    "Plugin upload rejected due to AST violations — name=%s violations=%s",
                    name,
                    validation.violations,
                )
                self.set_status(422)
                self.finish(
                    {
                        "status": "fail",
                        "data": {
                            "errors": [],
                            "violations": validation.violations,
                            "warnings": validation.warnings,
                        },
                    }
                )
                return

            # ── 6. Save file to disk ──────────────────────────────────────
            file_path = _make_upload_path(name)
            try:
                with open(file_path, "wb") as fh:
                    fh.write(file_body)
            except OSError as exc:
                raise APIError(500, "Failed to save plugin file: {}".format(exc))

            # ── 7. Persist metadata to DB with 'pending' status ───────────
            try:
                plugin = UserPlugin(
                    name=name,
                    description=description,
                    category=category,
                    group=group,
                    type=plugin_type,
                    author=author,
                    file_path=file_path,
                    approval_status=APPROVAL_PENDING,
                    version=version,
                    tags=tags_raw.strip() if tags_raw else None,
                )
                self.session.add(plugin)
                self.session.commit()
                self.session.refresh(plugin)
            except Exception as exc:
                self.session.rollback()
                # Clean up the orphaned file on DB failure
                try:
                    os.remove(file_path)
                except OSError:
                    pass
                raise APIError(500, "Database error while saving plugin: {}".format(str(exc)))

            logger.info(
                "Plugin uploaded and queued for review — id=%d name=%s author=%s",
                plugin.id,
                plugin.name,
                plugin.author,
            )

            self.set_status(201)
            self.success(
                {
                    "plugin": plugin.to_dict(),
                    "warnings": validation.warnings,
                    "message": (
                        "Plugin uploaded and stored as pending review. "
                        "It will become visible in the marketplace after administrator approval."
                    ),
                }
            )

        except APIError:
            raise
        except Exception as exc:
            logger.exception("Unhandled error in PluginUploadHandler.post")
            raise APIError(500, "Internal server error during plugin upload: {}".format(str(exc)))
