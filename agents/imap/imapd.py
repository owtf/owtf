#!/usr/bin/env python
'''
Description:
OWTF imap agent daemon, to periodically check email and launch actions
'''
import imaplib, time, sys, os
from general import *

def RunDaemon(Config, Storage):
	print "Starting Daemon.."
	try:
		while True:
			print "Checking Email.."
			Connection = imaplib.IMAP4_SSL(Config.Get('IMAP_HOST'))
			Connection.login(Config.Get('IMAP_USER'), Config.Get('IMAP_PASS'))
			Connection.select()
			Typ, Data = Connection.search(None, 'ALL')
			for ID in Data[0].split():
				StoredID = 0
				if Storage.Get():
					StoredID = int(Storage.Get())
				if int(ID) > StoredID:
					print "Processing Message Number=" + ID
					Typ, Data = Connection.fetch(ID, '(RFC822)')
					# Run the Plugin specified in the config file (i.e. link_clicker, whatever) to process the message:
					Plugin().Run(Config.Get('PROCESS_PLUGIN'), 'payloads', { 
									'Message' : Data
									, 'Log' : Config.Get('LOG_FILE')
									, 'ErrorLog' : Config.Get('ERROR_LOG_FILE') })
					#print 'Message %s\n%s\n' % (Num, Data[0][1])
					Storage.Set(ID) # Store last processed ID in the counter
			Connection.close()
			Connection.logout()
			Storage.Save()
			print "Sleeping " + Config.Get('WAIT_SECS') + " seconds..(Control+C to stop agent)"
			time.sleep(int(Config.Get('WAIT_SECS')))
	except KeyboardInterrupt:
		print "Stopping daemon.."
		Storage.Save()

Config = Config('config.cfg')
Storage = Storage(Config.Get('TRACK_FILE'))
RunDaemon(Config, Storage)
