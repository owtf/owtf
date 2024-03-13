"""
owtf.api.routes
~~~~~~~~~~~~~~~

"""
import tornado.web

from owtf.api.handlers.config import ConfigurationHandler
from owtf.api.handlers.health import HealthCheckHandler
from owtf.api.handlers.index import IndexHandler
from owtf.api.handlers.misc import ErrorDataHandler, DashboardPanelHandler, ProgressBarHandler
from owtf.api.handlers.plugin import PluginDataHandler, PluginNameOutput, PluginOutputHandler
from owtf.api.handlers.base import FileRedirectHandler
from owtf.api.handlers.report import ReportExportHandler
from owtf.api.handlers.session import OWTFSessionHandler
from owtf.api.handlers.targets import TargetConfigHandler, TargetConfigSearchHandler, TargetSeverityChartHandler
from owtf.utils.file import get_dir_worker_logs
from owtf.api.handlers.transactions import (
    TransactionDataHandler,
    TransactionHrtHandler,
    TransactionSearchHandler,
    URLDataHandler,
    URLSearchHandler,
)
from owtf.api.handlers.work import WorkerHandler, WorklistHandler, WorklistSearchHandler
from owtf.api.handlers.auth import (
    LogInHandler,
    LogOutHandler,
    RegisterHandler,
    AccountActivationGenerateHandler,
    AccountActivationValidateHandler,
    OtpGenerateHandler,
    OtpVerifyHandler,
    PasswordChangeHandler,
)
from owtf.api.handlers.api_token import ApiTokenGenerateHandler
from owtf.db.session import get_scoped_session
from owtf.models.plugin import Plugin
from owtf.settings import STATIC_ROOT

__all__ = ["API_v1_HANDLERS", "UI_HANDLERS"]

session = get_scoped_session()
plugin_group_re = "(%s)?" % "|".join(Plugin.get_all_plugin_groups(session))
plugin_type_re = "(%s)?" % "|".join(Plugin.get_all_plugin_types(session))
plugin_code_re = "([0-9A-Z\-]+)?"

API_v1_HANDLERS = [
    tornado.web.url(r"/api/v1/errors/?([0-9]+)?/?$", ErrorDataHandler, name="errors_api_url"),
    tornado.web.url(
        r"/api/v1/sessions/?([0-9]+)?/?(activate|add|remove)?/?$", OWTFSessionHandler, name="owtf_sessions_api_url"
    ),
    tornado.web.url(
        r"/api/v1/plugins/?" + plugin_group_re + "/?" + plugin_type_re + "/?" + plugin_code_re + "/?$",
        PluginDataHandler,
        name="plugins_api_url",
    ),
    tornado.web.url(r"/api/v1/plugins/progress/?$", ProgressBarHandler, name="poutput_count"),
    tornado.web.url(r"/api/v1/targets/severitychart/?$", TargetSeverityChartHandler, name="targets_severity"),
    tornado.web.url(r"/api/v1/targets/search/?$", TargetConfigSearchHandler, name="targets_search_api_url"),
    tornado.web.url(r"/api/v1/targets/?([0-9]+)?/?$", TargetConfigHandler, name="targets_api_url"),
    tornado.web.url(r"/api/v1/targets/([0-9]+)/urls/?$", URLDataHandler, name="urls_api_url"),
    tornado.web.url(r"/api/v1/targets/([0-9]+)/urls/search/?$", URLSearchHandler, name="urls_search_api_url"),
    tornado.web.url(
        r"/api/v1/targets/([0-9]+)/transactions/?([0-9]+)?/?$", TransactionDataHandler, name="transactions_api_url"
    ),
    tornado.web.url(
        r"/api/v1/targets/([0-9]+)/transactions/search/?$", TransactionSearchHandler, name="transactions_search_api_url"
    ),
    tornado.web.url(
        r"/api/v1/targets/([0-9]+)/transactions/hrt/?([0-9]+)?/?$",
        TransactionHrtHandler,
        name="transactions_hrt_api_url",
    ),
    tornado.web.url(
        r"/api/v1/targets/([0-9]+)/poutput/?" + plugin_group_re + "/?" + plugin_type_re + "/?" + plugin_code_re + "/?$",
        PluginOutputHandler,
        name="poutput_api_url",
    ),
    tornado.web.url(r"/api/v1/targets/([0-9]+)/poutput/names/?$", PluginNameOutput, name="plugin_name_api_url"),
    tornado.web.url(r"/api/v1/targets/([0-9]+)/export/?$", ReportExportHandler, name="report_export_api_url"),
    # The following one url is dummy and actually processed in file server
    tornado.web.url(r"/api/v1/workers/?([0-9]+)?/?(abort|pause|resume)?/?$", WorkerHandler, name="workers_api_url"),
    tornado.web.url(
        r"/api/v1/worklist/?([0-9]+)?/?(pause|resume|delete)?/?$", WorklistHandler, name="worklist_api_url"
    ),
    tornado.web.url(r"/api/v1/worklist/search/?$", WorklistSearchHandler, name="worklist_search_api_url"),
    tornado.web.url(r"/api/v1/configuration/?$", ConfigurationHandler, name="configuration_api_url"),
    tornado.web.url(r"/api/v1/dashboard/severitypanel/?$", DashboardPanelHandler),
    tornado.web.url(r"/api/v1/register/?$", RegisterHandler, name="regisration_api_url"),
    tornado.web.url(r"/api/v1/login/?$", LogInHandler, name="login_api_url"),
    tornado.web.url(r"/api/v1/logout/?$", LogOutHandler, name="logout_api_url"),
    tornado.web.url(r"/api/v1/generate/api_token/?$", ApiTokenGenerateHandler, name="apitokengenerator_api_url"),
    tornado.web.url(
        r"/api/v1/generate/confirm_email/?$", AccountActivationGenerateHandler, name="confirmpasswordgenerator_api_url"
    ),
    tornado.web.url(
        r"/api/v1/verify/confirm_email/([^/]+)?$",
        AccountActivationValidateHandler,
        name="confirmpasswordverify_api_url",
    ),
    tornado.web.url(r"/api/v1/generate/otp/?$", OtpGenerateHandler, name="otp_generate_api_url"),
    tornado.web.url(r"/api/v1/verify/otp/?$", OtpVerifyHandler, name="otp_verify_api_url"),
    tornado.web.url(r"/api/v1/new-password/?$", PasswordChangeHandler, name="password_change_api_url"),
]

UI_HANDLERS = [
    tornado.web.url(r"/static/(.*)", tornado.web.StaticFileHandler, {"path": STATIC_ROOT}),
    tornado.web.url(r"/debug/health/?$", HealthCheckHandler),
    tornado.web.url(
        r"/logs/(.*)", tornado.web.StaticFileHandler, {"path": get_dir_worker_logs()}, name="logs_files_url"
    ),
    tornado.web.url(r"/output_files/(.*)", FileRedirectHandler, name="file_redirect_url"),
    tornado.web.url(r"^/(?!api|debug|static|output_files|logs)(.*)$", IndexHandler),
]
