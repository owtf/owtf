#!/usr/bin/env python
'''
Description: OWTF imap agent daemon, to periodically check email and launch actions
'''

import imaplib
import time
import sys
import os

from general import *


def run_daemon(config, storage):
    print "Starting daemon.."
    try:
        while True:
            print "Checking email.."
            connection = imaplib.IMAP4_SSL(Config.Get('IMAP_HOST'))
            connection.login(config.Get('IMAP_USER'), config.Get('IMAP_PASS'))
            connection.select()
            typ, data = connection.search(None, 'ALL')
            for id in data[0].split():
                stored_id = 0
                if storage.get():
                    stored_id = int(storage.get())
                if int(id) > stored_id:
                    print "Processing message number=%s" % id
                    typ, data = connection.fetch(id, '(RFC822)')
                    # Run the Plugin specified in the config file (i.e. link_clicker, whatever) to process the message
                    log_config = { 
                        'message' : data,
                        'log' : config.get('LOG_FILE'),
                        'error_log' : config.get('ERROR_LOG_FILE')
                    }
                    Plugin().run(config.Get('PROCESS_PLUGIN'), 'payloads', log_config)
                    storage.set(id) # Store last processed ID in the counter
            connection.close()
            connection.logout()
            storage.save()
            print "Sleeping %s seconds..(Control+C to stop agent)" % config.Get('WAIT_SECS')
            time.sleep(int(config.Get('WAIT_SECS')))
    except KeyboardInterrupt:
        print "Stopping daemon.."
        storage.save()

imapd_config = Config('config.cfg')
storage = Storage(config.Get('TRACK_FILE'))
run_daemon(imapd_config, storage)
