#!/usr/bin/env python
'''
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
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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