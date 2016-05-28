#!/usr/bin/env python
'''
Description:
OWTF imap agent daemon, to periodically check email and launch actions
'''

import imaplib
import time

from general import Config, Storage, Plugin


def RunDaemon(config, storage):
    print "Starting Daemon.."
    try:
        while True:
            print "Checking Email.."
            connection = imaplib.IMAP4_SSL(config.Get('IMAP_HOST'))
            connection.login(config.Get('IMAP_USER'), config.Get('IMAP_PASS'))
            connection.select()
            typ, data = connection.search(None, 'ALL')
            for ID in data[0].split():
                StoredID = 0
                if storage.Get():
                    StoredID = int(storage.Get())
                if int(ID) > StoredID:
                    print "Processing Message Number=%s" % ID
                    typ, data = connection.fetch(ID, '(RFC822)')
                    # Run the Plugin specified in the config file (i.e. link_clicker, whatever) to process the message:
                    Plugin().Run(config.Get('PROCESS_PLUGIN'), 'payloads', {
                        'Message': data,
                        'Log': config.Get('LOG_FILE'),
                        'ErrorLog': config.Get('ERROR_LOG_FILE')})
                    storage.Set(ID)  # Store last processed ID in the counter
            connection.close()
            connection.logout()
            storage.Save()
            print "Sleeping %s seconds..(Control+C to stop agent)" % config.Get('WAIT_SECS')
            time.sleep(int(config.Get('WAIT_SECS')))
    except KeyboardInterrupt:
        print "Stopping daemon.."
        storage.Save()

config = Config('config.cfg')
storage = Storage(config.Get('TRACK_FILE'))
RunDaemon(config, storage)
