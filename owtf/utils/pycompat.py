"""
owtf.utils.pycompat
~~~~~~~~~~~~~~~~~~~

Helpers for compatibility between Python 2.x and 3.x.

"""
import sys

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3


if not PY2:
    strtypes = (str, )

    def u(s):
        return s
else:
    strtypes = (str, unicode)

    def u(s):
        return unicode(s)


def get_dict_iter_items(dictionary):
    if not PY2:
        return dictionary.items()
    else:
        return dictionary.iteritems()


if PY3:
    def iter_keys(d, **kw):
        return iter(d.keys(**kw))

    def iter_values(d, **kw):
        return iter(d.values(**kw))

    def iter_items(d, **kw):
        return iter(d.items(**kw))

    def iter_lists(d, **kw):
        return iter(d.lists(**kw))

else:
    def iter_keys(d, **kw):
        return d.iterkeys(**kw)

    def iter_values(d, **kw):
        return d.itervalues(**kw)

    def iter_items(d, **kw):
        return d.iteritems(**kw)

    def iter_lists(d, **kw):
        return d.iterlists(**kw)
