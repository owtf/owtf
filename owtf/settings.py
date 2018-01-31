import os

import yaml


HOME_DIR = os.path.expanduser("~")
OWTF_CONF = os.path.join(HOME_DIR, ".owtf")
ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_DIR = os.path.join(ROOT_DIR, 'data', 'conf')

DEBUG = True
CLI = False
# Used by tools like dirbuster to launch gui or cli versions
INTERACTIVE = True

### Database Server
if os.environ.get("DOCKER", None):
    DATABASE_NAME = os.environ["POSTGRES_DB"]
    DATABASE_PASS = os.environ["POSTGRES_PASSWORD"]
    DATABASE_USER = os.environ["POSTGRES_USER"]
    DATABASE_IP = "db"
    DATABASE_PORT = 5342
else:
    with open(os.path.join(OWTF_CONF, "db.yaml"), "r") as f:
        conf = yaml.load(f)
        DATABASE_PASS = conf["password"]
        DATABASE_NAME = conf['database_name']
        DATABASE_USER = conf['username']
        DATABASE_IP = conf['database_ip']
        DATABASE_PORT = int(conf['database_port'])


### Interface Server
SERVER_ADDR = '0.0.0.0'
UI_SERVER_PORT = 8009
FILE_SERVER_PORT = 8010

# ERROR reporting
USE_SENTRY = True
SENTRY_API_KEY = ''

# IMP PATHS
WEB_TEST_GROUPS = os.path.join(OWTF_CONF, 'conf', 'profiles', 'plugin_web', 'groups.cfg')
NET_TEST_GROUPS = os.path.join(OWTF_CONF, 'conf', 'profiles', 'plugin_net', 'groups.cfg')
AUX_TEST_GROUPS = os.path.join(OWTF_CONF, 'conf', 'profiles', 'plugin_aux', 'groups.cfg')
PLUGINS_DIR = os.path.join(ROOT_DIR, 'plugins')

### Output Settings
OUTPUT_PATH = 'owtf_review'
AUX_OUTPUT_PATH = 'owtf_review/auxiliary'

# The name of the directories relative to output path
TARGETS_DIR = 'targets'
WORKER_LOG_DIR = 'logs'

### Default profile settings
DEFAULT_GENERAL_PROFILE = os.path.join(OWTF_CONF, 'conf', 'general.cfg')
DEFAULT_RESOURCES_PROFILE = os.path.join(OWTF_CONF, 'conf', 'resources.cfg')
DEFAULT_MAPPING_PROFILE = os.path.join(OWTF_CONF, 'conf', 'mappings.cfg')
DEFAULT_FRAMEWORK_CONFIG = os.path.join(OWTF_CONF, 'conf', 'framework.cfg')
DEFAULT_WEB_PLUGIN_ORDER_PROFILE = os.path.join(OWTF_CONF, 'conf', 'profiles', 'plugin_web', 'order.cfg')
DEFAULT_NET_PLUGIN_ORDER_PROFILE = os.path.join(OWTF_CONF, 'conf', 'profiles', 'plugin_net', 'order.cfg')

# logs_dir can be both relative or absolute path ;)
LOGS_DIR = 'logs'
# Used for logging in OWTF
OWTF_LOG_FILE = '/tmp/owtf.log'


### Interface static folders
TEMPLATES = os.path.join(ROOT_DIR, 'templates')
POUTPUT_TEMPLATES_DIR = os.path.join(ROOT_DIR, 'templates')
STATIC_ROOT = os.path.join(ROOT_DIR, 'webapp', 'build')

### SMTP
EMAIL_FROM = 'you@your_server.com'
SMTP_LOGIN = 'login@your_server.com'
SMTP_PASS = 'your_password'
SMTP_HOST = 'your_mail_server.com'
SMTP_PORT = 25

########## CELERY
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

### OUTBOUND PROXY
USE_OUTBOUND_PROXY = False
OUTBOUND_PROXY_IP = ''
OUTBOUND_PROXY_PORT = ''
OUTBOUND_PROXY_AUTH = None

### Inbound Proxy Configuration
INBOUND_PROXY_IP = '127.0.0.1'
INBOUND_PROXY_PORT = 8008
INBOUND_PROXY_PROCESSES = 0
INBOUND_PROXY_CACHE_DIR = '/tmp/owtf/proxy-cache'
CA_CERT = os.path.join(OWTF_CONF, "proxy", "certs", "ca.crt")
CA_KEY = os.path.join(OWTF_CONF, "proxy", "certs", "ca.key")
CA_PASS_FILE = os.path.join(OWTF_CONF, 'proxy', "certs", "ca_pass.txt")
CERTS_FOLDER = os.path.join(OWTF_CONF, 'proxy', 'certs')

BLACKLIST_COOKIES = ['_ga', '__utma', '__utmb', '__utmc', '__utmz', '__utmv']
WHITELIST_COOKIES = ""
PROXY_RESTRICTED_RESPONSE_HEADERS = [
    "Content-Length",
    "Content-Encoding",
    "Etag",
    "Transfer-Encoding",
    "Connection",
    "Vary",
    "Accept-Ranges",
    "Pragma"
]

PROXY_RESTRICTED_REQUEST_HEADERS = [
    "Connection",
    "Pragma",
    "Cache-Control",
    "If-Modified-Since"
]

PROXY_LOG = '/tmp/owtf/proxy.log'

### UI
UI_SERVER_LOG = '/tmp/owtf/ui_server.log'
FILE_SERVER_LOG = '/tmp/owtf/file_server.log'

### HTTP_AUTH
HTTP_AUTH_HOST = None
HTTP_AUTH_USERNAME = None
HTTP_AUTH_PASSWORD = None
HTTP_AUTH_MODE = 'basic'


### Memory
RESOURCE_MONITOR_PROFILER = 0
PROCESS_PER_CORE = 1
MIN_RAM_NEEDED = 20

# misc
DATE_TIME_FORMAT = '%d/%m/%Y-%H:%M'
REPLACEMENT_DELIMITER = "@@@"
REPLACEMENT_DELIMITER_LENGTH = len(REPLACEMENT_DELIMITER)
CONFIG_TYPES = ['string', 'other']

FORCE_OVERWRITE = True
USER_AGENT = 'Mozilla/5.0 (X11; Linux i686; rv:6.0) Gecko/20100101 Firefox/15.0'
PROXY_CHECK_URL = 'http://www.google.ie'


### Fallback
FALLBACK_FRAMEWORK_CONFIG = os.path.join(ROOT_DIR, 'data', 'conf', 'framework.cfg')
FALLBACK_WEB_TEST_GROUPS = os.path.join(ROOT_DIR, 'data', 'conf', 'profiles', 'plugin_web', 'groups.cfg')
FALLBACK_NET_TEST_GROUPS = os.path.join(ROOT_DIR, 'data', 'conf', 'profiles', 'plugin_net', 'groups.cfg')
FALLBACK_AUX_TEST_GROUPS = os.path.join(ROOT_DIR, 'data', 'conf', 'profiles', 'plugin_aux', 'groups.cfg')
FALLBACK_PLUGINS_DIR = os.path.join(ROOT_DIR, 'data', 'plugins')
FALLBACK_GENERAL_PROFILE = os.path.join(ROOT_DIR, 'data', 'conf', 'general.cfg')
FALLBACK_RESOURCES_PROFILE = os.path.join(ROOT_DIR, 'data', 'conf', 'resources.cfg')
FALLBACK_MAPPING_PROFILE = os.path.join(ROOT_DIR, 'data' + 'conf', 'mappings.cfg')
FALLBACK_WEB_PLUGIN_ORDER_PROFILE = os.path.join(ROOT_DIR, 'data', 'conf', 'profiles', 'plugin_web', 'order.cfg')
FALLBACK_NET_PLUGIN_ORDER_PROFILE = os.path.join(ROOT_DIR, 'data', 'conf', 'profiles', 'plugin_net', 'order.cfg')
