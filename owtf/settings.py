"""
owtf.settings
~~~~~~~~~~~~~

It contains all the owtf global configs.
"""
import os
import re

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

import yaml

HOME_DIR = os.path.expanduser("~")
OWTF_CONF = os.path.join(HOME_DIR, ".owtf")
ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_DIR = os.path.join(ROOT_DIR, "data", "conf")

DEBUG = True
# Used by tools like dirbuster to launch gui or cli versions
INTERACTIVE = True

# Database config when used in docker
if os.environ.get("DOCKER", None):
    DATABASE_NAME = os.environ["POSTGRES_DB"]
    DATABASE_PASS = os.environ["POSTGRES_PASSWORD"]
    DATABASE_USER = os.environ["POSTGRES_USER"]
    DATABASE_IP = "db"
    DATABASE_PORT = 5432
else:
    # Change this if you deploy OWTF to a public facing server
    DATABASE_PASS = "jgZKW33Q+HZk8rqylZxaPg1lbuNGHJhgzsq3gBKV32g="
    DATABASE_NAME = "owtf_db"
    DATABASE_USER = "owtf_db_user"
    DATABASE_IP = os.environ.get("POSTGRES_HOST", "127.0.0.1")
    DATABASE_PORT = 5432

# API and UI Server
SERVER_ADDR = "0.0.0.0"
SERVER_PORT = 8009
FILE_SERVER_PORT = 8010
FRONTEND_SERVER_PORT = 8019

# Default API version
DEFAULT_API_VERSION = "v1"

# Application secret
# Change this
APP_SECRET = "changeme"

SESSION_COOKIE_NAME = "owtf-session"

# CORS settings. Fine grained, do not override if possible.
SIMPLE_HEADERS = ["accept", "accept-language", "content-language", "authorization"]
ALLOWED_ORIGINS = ["http://localhost:8010", "http://localhost:8019"]
ALLOWED_METHODS = ["GET", "POST", "DELETE"]
SEND_CREDENTIALS = False

# ERROR reporting
USE_SENTRY = False
SENTRY_API_KEY = ""

# IMP PATHS
WEB_TEST_GROUPS = os.path.join(OWTF_CONF, "conf", "profiles", "plugin_web", "groups.cfg")
NET_TEST_GROUPS = os.path.join(OWTF_CONF, "conf", "profiles", "plugin_net", "groups.cfg")
AUX_TEST_GROUPS = os.path.join(OWTF_CONF, "conf", "profiles", "plugin_aux", "groups.cfg")
PLUGINS_DIR = os.path.join(ROOT_DIR, "plugins")

# Output Settings
OUTPUT_PATH = "owtf_review"
AUX_OUTPUT_PATH = "owtf_review/auxiliary"
NET_SCANS_PATH = "owtf_review/scans"

# The name of the directories relative to output path
TARGETS_DIR = "targets"
WORKER_LOG_DIR = "logs"

# Default profile settings
DEFAULT_GENERAL_PROFILE = os.path.join(OWTF_CONF, "conf", "general.yaml")
DEFAULT_FRAMEWORK_CONFIG = os.path.join(OWTF_CONF, "conf", "framework.yaml")
DEFAULT_RESOURCES_PROFILE = os.path.join(OWTF_CONF, "conf", "resources.cfg")
DEFAULT_WEB_PLUGIN_ORDER_PROFILE = os.path.join(OWTF_CONF, "conf", "profiles", "plugin_web", "order.cfg")
DEFAULT_NET_PLUGIN_ORDER_PROFILE = os.path.join(OWTF_CONF, "conf", "profiles", "plugin_net", "order.cfg")

# logs_dir can be both relative or absolute path ;)
LOGS_DIR = "logs"
# Used for logging in OWTF
OWTF_LOG_FILE = "/tmp/owtf.log"

# Interface static folders
TEMPLATES = os.path.join(OWTF_CONF, "build")
STATIC_ROOT = os.path.join(OWTF_CONF, "build")

# SMTP (Make changes here to setup SMTP server of your choice)
EMAIL_FROM = None  # Your SMTP From Mail
SMTP_LOGIN = None  # Your SMTP Login
SMTP_PASS = None  # Your Password
SMTP_HOST = None  # Your Mail Server
SMTP_PORT = None  # Your SMTP Port

# OUTBOUND PROXY
USE_OUTBOUND_PROXY = False
OUTBOUND_PROXY_IP = ""
OUTBOUND_PROXY_PORT = ""
OUTBOUND_PROXY_AUTH = None

# Inbound Proxy Configuration
INBOUND_PROXY_IP = "127.0.0.1"
INBOUND_PROXY_PORT = 8008
INBOUND_PROXY_PROCESSES = 0
INBOUND_PROXY_CACHE_DIR = "/tmp/owtf/proxy-cache"
CA_CERT = os.path.join(OWTF_CONF, "proxy", "certs", "ca.crt")
CA_KEY = os.path.join(OWTF_CONF, "proxy", "certs", "ca.key")
CA_PASS_FILE = os.path.join(OWTF_CONF, "proxy", "certs", "ca_pass.txt")
CERTS_FOLDER = os.path.join(OWTF_CONF, "proxy", "certs")

BLACKLIST_COOKIES = ["_ga", "__utma", "__utmb", "__utmc", "__utmz", "__utmv"]
WHITELIST_COOKIES = ""
PROXY_RESTRICTED_RESPONSE_HEADERS = [
    "Content-Length",
    "Content-Encoding",
    "Etag",
    "Transfer-Encoding",
    "Connection",
    "Vary",
    "Accept-Ranges",
    "Pragma",
]

PROXY_RESTRICTED_REQUEST_HEADERS = [
    "Connection",
    "Pragma",
    "Cache-Control",
    "If-Modified-Since",
]
PROXY_LOG = "/tmp/owtf/proxy.log"

# Define regex patterns
REGEXP_FILE_URL = (
    "^[^\?]+\.(xml|exe|pdf|cs|log|inc|dat|bak|conf|cnf|old|zip|7z|rar|tar|gz|bz2|txt|xls|xlsx|doc|docx|ppt|pptx)$"
)
# Potentially small files will be retrieved for analysis
REGEXP_SMALL_FILE_URL = "^[^\?]+\.(xml|cs|inc|dat|bak|conf|cnf|old|txt)$"
REGEXP_IMAGE_URL = "^[^\?]+\.(jpg|jpeg|png|gif|bmp)$"
REGEXP_VALID_URL = "^[^\?]+\.(shtml|shtm|stm)$"
REGEXP_SSI_URL = "^(http|ftp)[^ ]+$"
REGEXP_PASSWORD = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,20}$"
REGEXP_EMAIL = "^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[-]?\w+[.]\w{2,3}$"

# Compile regular expressions once at the beginning for speed purposes:
is_file_regex = re.compile(REGEXP_FILE_URL, re.IGNORECASE)
is_small_file_regex = re.compile(REGEXP_SMALL_FILE_URL, re.IGNORECASE)
is_image_regex = re.compile(REGEXP_IMAGE_URL, re.IGNORECASE)
is_url_regex = re.compile(REGEXP_VALID_URL, re.IGNORECASE)
is_ssi_regex = re.compile(REGEXP_SSI_URL, re.IGNORECASE)
is_password_valid_regex = re.compile(REGEXP_PASSWORD)
is_email_valid_regex = re.compile(REGEXP_EMAIL, re.IGNORECASE)

# UI
SERVER_LOG = "/tmp/owtf/ui_server.log"
FILE_SERVER_LOG = "/tmp/owtf/file_server.log"

# HTTP_AUTH
HTTP_AUTH_HOST = None
HTTP_AUTH_USERNAME = None
HTTP_AUTH_PASSWORD = None
HTTP_AUTH_MODE = "basic"

# Memory
RESOURCE_MONITOR_PROFILER = 0
PROCESS_PER_CORE = 1
MIN_RAM_NEEDED = 20

# misc
DATE_TIME_FORMAT = "%d/%m/%Y-%H:%M"
REPLACEMENT_DELIMITER = "@@@"
REPLACEMENT_DELIMITER_LENGTH = len(REPLACEMENT_DELIMITER)
CONFIG_TYPES = ["string", "other"]

USER_AGENT = "Mozilla/5.0 (X11; Linux i686; rv:6.0) Gecko/20100101 Firefox/15.0"
PROXY_CHECK_URL = "http://www.google.ie"

# Fallback
FALLBACK_WEB_TEST_GROUPS = os.path.join(ROOT_DIR, "data", "conf", "profiles", "plugin_web", "groups.cfg")
FALLBACK_NET_TEST_GROUPS = os.path.join(ROOT_DIR, "data", "conf", "profiles", "plugin_net", "groups.cfg")
FALLBACK_AUX_TEST_GROUPS = os.path.join(ROOT_DIR, "data", "conf", "profiles", "plugin_aux", "groups.cfg")
FALLBACK_PLUGINS_DIR = os.path.join(ROOT_DIR, "data", "plugins")
FALLBACK_GENERAL_PROFILE = os.path.join(ROOT_DIR, "data", "conf", "general.yaml")
FALLBACK_FRAMEWORK_CONFIG = os.path.join(ROOT_DIR, "data", "conf", "framework.yaml")
FALLBACK_RESOURCES_PROFILE = os.path.join(ROOT_DIR, "data", "conf", "resources.cfg")
FALLBACK_WEB_PLUGIN_ORDER_PROFILE = os.path.join(ROOT_DIR, "data", "conf", "profiles", "plugin_web", "order.cfg")
FALLBACK_NET_PLUGIN_ORDER_PROFILE = os.path.join(ROOT_DIR, "data", "conf", "profiles", "plugin_net", "order.cfg")

# Override the values
local_conf = os.path.join(OWTF_CONF, "settings.py")
try:
    with open(local_conf) as f:
        settings = compile(f.read(), local_conf, "exec")
        exec(settings, globals(), locals())
except FileNotFoundError:
    pass

# JWT
JWT_SECRET_KEY = "changeme"  # Add your JWT_SECRET_KEY here
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_SECONDS = 60 * 60 * 24
JWT_OPTIONS = {
    "verify_signature": True,
    "verify_exp": True,
    "verify_nbf": False,
    "verify_iat": True,
    "verify_aud": False,
}
