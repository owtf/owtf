"""
owtf.utils.pycompat
~~~~~~~~~~~~~~~~~~~

Helpers for compatibility between Python 2.x and 3.x.

"""
import sys

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if not PY2:
    strtypes = (str,)

    def u(s):
        return s


else:
    strtypes = (str, unicode)

    def u(s):
        return unicode(s)


if PY3:

    def iterkeys(d, **kw):
        return iter(d.keys(**kw))

    def itervalues(d, **kw):
        return iter(d.values(**kw))

    def iteritems(d, **kw):
        return iter(d.items(**kw))

    def iterlists(d, **kw):
        return iter(d.lists(**kw))


else:

    def iterkeys(d, **kw):
        return d.iterkeys(**kw)

    def itervalues(d, **kw):
        return d.itervalues(**kw)

    def iteritems(d, **kw):
        return d.iteritems(**kw)

    def iterlists(d, **kw):
        return d.iterlists(**kw)
