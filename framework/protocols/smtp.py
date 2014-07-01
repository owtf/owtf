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

Description:
This is the OWTF SMTP handler, to simplify sending emails.

"""

import os
import base64
import smtplib

from email import MIMEMultipart, MIMEBase, MIMEText, Encoders

from framework.lib.general import *


class SMTP(object):
    def __init__(self, Core):
        self.Core = Core
        self.MsgPrefix = 'OWTF SMTP Client - '

    def Print(self, Message):
        cprint(self.MsgPrefix + Message)

    def create_connection_with_mail_server(self, Options):
        return smtplib.SMTP(Options['SMTP_HOST'], int(Options['SMTP_PORT']))

    def Connect(self, Options):
        MailServer = self.create_connection_with_mail_server(Options)
        MailServer.ehlo()
        try:
            MailServer.starttls() # Give start TLS a shot
        except Exception, e:
            self.Print(
                str(e) +
                " - Assuming TLS unsupported and trying to continue..")
        try:
            MailServer.login(Options['SMTP_LOGIN'], Options['SMTP_PASS'])
        except Exception, e:
            self.Print(
                'ERROR: ' + str(e) +
                " - Assuming open-relay and trying to continue..")
        return MailServer

    def is_file(self, target):
        return os.path.isfile(target)

    def get_file_content_as_list(self, Options):
        return GetFileAsList(Options['EMAIL_TARGET'])

    def BuildTargetList(self, Options):
        """Build a list of targets for simplification purposes."""
        if self.is_file(Options['EMAIL_TARGET']):
            TargetList = self.get_file_content_as_list(Options)
        else:
            TargetList = [ Options['EMAIL_TARGET'] ]
        return TargetList

    def Send(self, Options):
        NumErrors = 0
        for Target in self.BuildTargetList(Options):
            Target = Target.strip()
            if not Target:
                continue  # Skip blank lines!
            self.Print("Sending email for target: " + Target)
            try:
                Message = self.BuildMessage(Options, Target)
                MailServer = self.Connect(Options)
                MailServer.sendmail(
                    Options['SMTP_LOGIN'],
                    Target,
                    Message.as_string())
                self.Print("Email relay successful!")
            except Exception, e:
                self.Core.Error.Add("Error delivering email: " + str(e))
                NumErrors += 1
        return (NumErrors == 0)

    def BuildMessage(self, Options, Target):
        Message = MIMEMultipart.MIMEMultipart()
        for Name, Value in Options.items():
            if Name == 'EMAIL_BODY':
                self.AddBody(Message, Value)
            elif Name == 'EMAIL_ATTACHMENT':
                self.AddAttachment(Message, Value)
            else:  # From, To, Subject, etc.
                self.SetOption(Message, Name, Value, Target)
        return Message

    def SetOption(self, Message, Option, Value, Target):
        if Option == 'EMAIL_FROM':
            Message['From'] = Value
        elif Option == 'EMAIL_TARGET':
            Message['To'] = Target
        elif Option == 'EMAIL_PRIORITY':
            if Value == 'yes':
                Message['X-Priority'] = " 1 (Highest)"
                Message['X-MSMail-Priority'] = " High"
        elif Option == 'EMAIL_SUBJECT':
            Message['Subject'] = Value

    def AddBody(self, Message, Text):
        # If a file has been specified as Body, then set Body to file contents.
        if os.path.isfile(Text):
            Body = self.Core.open(Text).read().strip()
        else:
            Body = Text
        Message.attach(MIMEText.MIMEText(Body, Message))

    def AddAttachment(self, Message, Attachment):
        if not Attachment:
            return False
        BinaryBlob = MIMEBase.MIMEBase('application', 'octet-stream')
        BinaryBlob.set_payload(self.Core.open(Attachment, 'rb').read())
        Encoders.encode_base64(BinaryBlob)  # base64 encode the Binary Blob.
        # Binary Blob headers.
        BinaryBlob.add_header(
            'Content-Disposition',
            'attachment; filename="%s"' % os.path.basename(Attachment))
        Message.attach(BinaryBlob)
        return True
