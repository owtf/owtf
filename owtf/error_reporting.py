"""
owtf.error_reporting
~~~~~~~~~~~~~~~~~~~~

This module set up sentry error reporting and logging.
"""
import logging
import signal
import sys

# setup sentry logging
try:
    from raven.contrib.tornado import AsyncSentryClient
    raven_installed = True
except ImportError:
    raven_installed = False


__all__ = ['SentryProxy', 'get_sentry_client', 'log_and_exit_handler', 'setup_signal_handlers']


signame_by_signum = {v: k for k, v in signal.__dict__.items() if k.startswith('SIG') and not
        k.startswith('SIG_')}


class SentryProxy(object):
    """Simple proxy for sentry client that logs to stderr even if no sentry client exists."""
    def __init__(self, sentry_client):
        self.sentry_client = sentry_client

    def captureException(self, exc_info=None, **kwargs):
        if self.sentry_client:
            self.sentry_client.captureException(exc_info=exc_info, **kwargs)

        logging.exception("exception occurred")


def get_sentry_client(sentry_key):
    if sentry_key and raven_installed:
        logging.info("[+] Sentry client setup key={}".format(sentry_key))
        sentry_client = SentryProxy(sentry_client=AsyncSentryClient(sentry_key))
    else:
        if not sentry_key:
            logging.info("[-] No Sentry key specified")

        if not raven_installed:
            logging.info("[-] Raven (sentry client) not installed")

        sentry_client = SentryProxy(sentry_client=None)

    return sentry_client


def log_and_exit_handler(signum, frame):
    logging.warning("caught signal {}, exiting".format(signame_by_signum[signum]))
    sys.exit(1)


def setup_signal_handlers():
    """Setup the handlers"""
    for signum in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(signum, log_and_exit_handler)
