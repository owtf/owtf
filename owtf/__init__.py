from __future__ import absolute_import, unicode_literals

import re
from typing import Any, NamedTuple

try:
    from owtf.utils.logger import OWTFLogger

    OWTFLogger().enable_logging()
except ImportError as e:
    print(e)

__version__ = "2.6.0"
__homepage__ = "https://github.com/owtf/owtf"
__docformat__ = "markdown"


version_info_t = NamedTuple("version_info_t", [("major", int), ("minor", int), ("patch", int)])

# bumpversion can only search for {current_version}
# so we have to parse the version here.
_temp = re.match(r"(\d+)\.(\d+).(\d+)(\.(.+))?", __version__).groups()
VERSION = version_info = version_info_t(int(_temp[0]), int(_temp[1]), int(_temp[2]))
del _temp
__all__ = []
