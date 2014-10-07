#!/usr/bin/env python
"""

owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the copyright owner nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The time module allows the rest of the framework to time how long it takes for
certain actions to execute and present this information in both seconds and
human-readable form.

"""

import time
from framework.dependency_management.dependency_resolver import BaseComponent
from framework.dependency_management.interfaces import TimerInterface
import math
import datetime


class Timer(BaseComponent, TimerInterface):

    COMPONENT_NAME = "timer"

    # Dictionary of Timers, Several timers can be set at any given point in
    # time.
    Time = {}

    def __init__(self, datetime_format="%d/%m/%Y-%H:%M"):
        self.register_in_service_locator()
        self.date_time_format = datetime_format

    def start_timer(self, offSet='0'):
        self.Time[offSet] = {}
        self.Time[offSet]['start'] = self.get_current_date_time()
        return self.Time[offSet]['start']

    def get_current_date_time_as_str(self):
        return self.get_current_date_time().strftime(self.date_time_format)

    @staticmethod
    def get_current_date_time():
        return datetime.datetime.now()

    def get_elapsed_time(self, offSet='0'):
        return datetime.datetime.now() - self.Time[offSet]['start']

    def get_time_as_str(self, timedelta):
        microseconds, seconds = math.modf(timedelta.total_seconds())
        seconds = int(seconds)
        miliseconds = int(microseconds*1000)
        hours = seconds / 3600
        seconds -= 3600*hours
        minutes = seconds / 60
        seconds -= 60*minutes
        TimeStr = ''
        if hours > 0:
            TimeStr += "%2dh, " % hours
        if minutes > 0:
            TimeStr += "%2dm, " % minutes
        TimeStr += "%2ds, %3dms" % (seconds, miliseconds)
        # Strip necessary to get rid of leading spaces sometimes.
        return TimeStr.strip()

    def get_time_human(self, seconds_str):
        seconds, miliseconds = str(seconds_str).split('.')
        seconds = int(seconds)
        miliseconds = int(miliseconds[0:3])
        hours = seconds / 3600
        seconds -= 3600*hours
        minutes = seconds / 60
        seconds -= 60*minutes
        TimeStr = ''
        if hours > 0:
            TimeStr += "%2dh, " % hours
        if minutes > 0:
            TimeStr += "%2dm, " % minutes
        TimeStr += "%2ds, %3dms" % (seconds, miliseconds)
        # Strip necessary to get rid of leading spaces sometimes.
        return TimeStr.strip()

    def end_timer(self, offset='0'):
        self.Time[offset]['end'] = self.get_current_date_time()

    def get_elapsed_time_as_str(self, offset='0'):
        elapsed = self.get_elapsed_time(offset)
        self.end_timer(offset)
        return(self.get_time_as_str(elapsed))

    def get_start_date_time(self, offset='0'):
        return self.Time[offset]['start']

    def get_end_date_time(self, offset='0'):
        if 'end' not in self.Time[offset].keys():
            self.end_timer(offset)
        return self.Time[offset]['end']

    def get_start_date_time_as_str(self, offset='0'):
        return self.get_start_date_time(offset).strftime(self.date_time_format)

    def get_end_date_time_as_str(self, offset='0'):
        return self.get_end_date_time(offset).strftime(self.date_time_format)
