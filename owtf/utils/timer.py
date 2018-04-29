"""
owtf.utils.timer
~~~~~~~~~~~~~~~~

The time module allows the rest of the framework to time how long it takes for
certain actions to execute and present this information in both seconds and
human-readable form.
"""
import datetime
import math

from owtf.settings import DATE_TIME_FORMAT

__all__ = ["Timer", "timer"]


class Timer(object):
    # Dictionary of timers, Several timers can be set at any given point in time.
    timers = {}

    def __init__(self, datetime_format="%d/%m/%Y-%H:%M"):
        self.date_time_format = datetime_format

    def start_timer(self, offset="0"):
        """ Adds a start time to the timer

        :param offset: Timer index
        :type offset: `str`
        :return: The start time for the timer
        :rtype: `datetime`
        """
        self.timers[offset] = {}
        self.timers[offset]["start"] = self.get_current_date_time()
        return self.timers[offset]["start"]

    def get_current_date_time_as_str(self):
        """Returns a datetime object as a string in a particular format

        :return: Datetime object in string form
        :rtype: `str`
        """
        return self.get_current_date_time().strftime(self.date_time_format)

    @staticmethod
    def get_current_date_time():
        """ Current timestamp

        :return: The current time as a timestamp
        :rtype: `datetime`
        """
        return datetime.datetime.now()

    def get_elapsed_time(self, offset="0"):
        """Gets the time elapsed between now and start of the timer in Unix epoch

        :param offset: Timer index
        :type offset: `str`
        :return: Time difference
        :rtype: `datetime`
        """
        return datetime.datetime.now() - self.timers[offset]["start"]

    def get_time_as_str(self, timedelta):
        """Get the time difference as a human readable string

        :param timedelta: Time difference
        :type timedelta: `datetime.timedelta`
        :return: Human readable form for the timedelta
        :rtype: `str`
        """
        microseconds, seconds = math.modf(timedelta.total_seconds())
        seconds = int(seconds)
        milliseconds = int(microseconds * 1000)
        hours = seconds / 3600
        seconds -= 3600 * hours
        minutes = seconds / 60
        seconds -= 60 * minutes
        timer_str = ""
        if hours > 0:
            timer_str += "%2dh, " % hours
        if minutes > 0:
            timer_str += "%2dm, " % minutes
        timer_str += "%2ds, %3dms" % (seconds, milliseconds)
        # Strip necessary to get rid of leading spaces sometimes.
        return timer_str.strip()

    def get_time_human(self, seconds_str):
        """Generates the human readable string for the timestamp

        :param seconds_str: Unix style timestamp
        :type seconds_str: `str`
        :return: Timestamp in a human readable string
        :rtype: `str`
        """
        seconds, milliseconds = str(seconds_str).split(".")
        seconds = int(seconds)
        milliseconds = int(milliseconds[0:3])
        hours = seconds / 3600
        seconds -= 3600 * hours
        minutes = seconds / 60
        seconds -= 60 * minutes
        timer_str = ""
        if hours > 0:
            timer_str += "%2dh, " % hours
        if minutes > 0:
            timer_str += "%2dm, " % minutes
        timer_str += "%2ds, %3dms" % (seconds, milliseconds)
        # Strip necessary to get rid of leading spaces sometimes.
        return timer_str.strip()

    def end_timer(self, offset="0"):
        """Sets the end of the timer

        :param offset: Timer index
        :type offset: `str`
        :return:
        :rtype: None
        """
        self.timers[offset]["end"] = self.get_current_date_time()

    def get_elapsed_time_as_str(self, offset="0"):
        """Returns the time elapsed a nice readable string

        :param offset: Timer index
        :type offset: `str`
        :return: Time elapsed as a string
        :rtype: `str`
        """
        elapsed = self.get_elapsed_time(offset)
        self.end_timer(offset)
        return self.get_time_as_str(elapsed)

    def get_start_date_time(self, offset="0"):
        """Get the start time for the timer

        :param offset: Timer index
        :type offset: `str`
        :return: Start time for the timer as a timestamp
        :rtype: `datetime`
        """
        return self.timers[offset]["start"]

    def get_end_date_time(self, offset="0"):
        """Get the end time for the timer

        :param offset: Timer index
        :type offset: `str`
        :return: End time for the timer as a timestamp
        :rtype: `datetime`
        """
        if "end" not in self.timers[offset].keys():
            self.end_timer(offset)
        return self.timers[offset]["end"]

    def get_start_date_time_as_str(self, offset="0"):
        """Get the start time for the timer as a string

        :param offset: Timer index
        :type offset: `str`
        :return: Start time for the timer as a string
        :rtype: `str`
        """
        return self.get_start_date_time(offset).strftime(self.date_time_format)

    def get_end_date_time_as_str(self, offset="0"):
        """Get the end time for the timer as a string

        :param offset: Timer index
        :type offset: `str`
        :return: End time for the timer as a string
        :rtype: `str`
        """
        return self.get_end_date_time(offset).strftime(self.date_time_format)


timer = Timer(datetime_format=DATE_TIME_FORMAT)
