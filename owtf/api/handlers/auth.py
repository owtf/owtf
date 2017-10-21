import collections
from time import gmtime, strftime
from collections import defaultdict

import tornado.gen
import tornado.web
import tornado.httpclient

from owtf.lib import exceptions
from owtf.constants import RANKS
from owtf.lib.general import cprint
from owtf.lib.exceptions import InvalidTargetReference

