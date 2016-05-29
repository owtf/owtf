#!/usr/bin/env python
"""
Description:
This is the OWTF SMTP handler, to simplify sending emails.
"""

import os
import base64
import smtplib

from email import MIMEMultipart, MIMEBase, MIMEText, Encoders
from framework.dependency_management.dependency_resolver import BaseComponent

from framework.lib.general import *
from framework.utils import FileOperations


class SMTP(BaseComponent):

    COMPONENT_NAME = "smtp"

    def __init__(self):
        self.register_in_service_locator()
        self.error_handler = self.get_component("error_handler")
        self.MsgPrefix = 'OWTF SMTP Client - '

    def Print(self, message):
        cprint(self.MsgPrefix + message)

    def create_connection_with_mail_server(self, options):
        return smtplib.SMTP(options['SMTP_HOST'], int(options['SMTP_PORT']))

    def Connect(self, options):
        mail_server = self.create_connection_with_mail_server(options)
        mail_server.ehlo()
        try:
            mail_server.starttls() # Give start TLS a shot
        except Exception, e:
            self.Print(
                str(e) +
                " - Assuming TLS unsupported and trying to continue..")
        try:
            mail_server.login(options['SMTP_LOGIN'], options['SMTP_PASS'])
        except Exception, e:
            self.Print(
                'ERROR: ' + str(e) +
                " - Assuming open-relay and trying to continue..")
        return mail_server

    def is_file(self, target):
        return os.path.isfile(target)

    def get_file_content_as_list(self, options):
        return GetFileAsList(options['EMAIL_TARGET'])

    def BuildTargetList(self, options):
        """Build a list of targets for simplification purposes."""
        if self.is_file(options['EMAIL_TARGET']):
            target_list = self.get_file_content_as_list(options)
        else:
            target_list = [options['EMAIL_TARGET']]
        return target_list

    def Send(self, options):
        num_errors = 0
        for target in self.BuildTargetList(options):
            target = target.strip()
            if not target:
                continue  # Skip blank lines!
            self.Print("Sending email for target: " + target)
            try:
                message = self.BuildMessage(options, target)
                mail_server = self.Connect(options)
                mail_server.sendmail(
                    options['SMTP_LOGIN'],
                    target,
                    message.as_string())
                self.Print("Email relay successful!")
            except Exception, e:
                self.error_handler.Add("Error delivering email: " + str(e))
                num_errors += 1
        return (num_errors == 0)

    def BuildMessage(self, options, target):
        message = MIMEMultipart.MIMEMultipart()
        for name, value in options.items():
            if name == 'EMAIL_BODY':
                self.AddBody(message, value)
            elif name == 'EMAIL_ATTACHMENT':
                self.AddAttachment(message, value)
            else:  # From, To, Subject, etc.
                self.SetOption(message, name, value, target)
        return message

    def SetOption(self, message, option, value, target):
        if option == 'EMAIL_FROM':
            message['From'] = value
        elif option == 'EMAIL_TARGET':
            message['To'] = target
        elif option == 'EMAIL_PRIORITY':
            if value == 'yes':
                message['X-Priority'] = " 1 (Highest)"
                message['X-MSMail-Priority'] = " High"
        elif option == 'EMAIL_SUBJECT':
            message['Subject'] = value

    def AddBody(self, message, text):
        # If a file has been specified as Body, then set Body to file contents.
        if os.path.isfile(text):
            body = FileOperations.open(text).read().strip()
        else:
            body = text
        message.attach(MIMEText.MIMEText(body, message))

    def AddAttachment(self, message, attachment):
        if not attachment:
            return False
        binary_blob = MIMEBase.MIMEBase('application', 'octet-stream')
        binary_blob.set_payload(FileOperations.open(attachment, 'rb').read())
        Encoders.encode_base64(binary_blob)  # base64 encode the Binary Blob.
        # Binary Blob headers.
        binary_blob.add_header(
            'Content-Disposition',
            'attachment; filename="%s"' % os.path.basename(attachment))
        message.attach(binary_blob)
        return True
