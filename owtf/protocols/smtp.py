"""
owtf.protocols.smtp
~~~~~~~~~~~~~~~~~~~

Description:
This is the OWTF SMTP handler, to simplify sending emails.
"""
from email.mime import base, multipart, text as mimetext
from email import encoders
import logging
import os
import smtplib

from owtf.utils.file import FileOperations, get_file_as_list

__all__ = ["smtp"]


class SMTP(object):

    def __init__(self):
        self.msg_prefix = "OWTF SMTP Client - "

    def pprint(self, message):
        logging.info(self.msg_prefix + message)

    def create_connection_with_mail_server(self, options):
        return smtplib.SMTP(options["SMTP_HOST"], int(options["SMTP_PORT"]))

    def connect(self, options):
        try:
            mail_server = self.create_connection_with_mail_server(options)
            mail_server.ehlo()
        except Exception:
            self.pprint("Error connecting to {!s} on port {!s}".format(options["SMTP_HOST"], options["SMTP_PORT"]))
            return None
        try:
            mail_server.starttls()  # Give start TLS a shot
        except Exception as e:
            self.pprint("{} - Assuming TLS unsupported and trying to continue..".format(str(e)))
        try:
            mail_server.login(options["SMTP_LOGIN"], options["SMTP_PASS"])
        except Exception as e:
            self.pprint("ERROR: {} - Assuming open-relay and trying to continue..".format(str(e)))
        return mail_server

    def is_file(self, target):
        return os.path.isfile(target)

    def get_file_content_as_list(self, options):
        return get_file_as_list(options["EMAIL_TARGET"])

    def build_target_list(self, options):
        """Build a list of targets for simplification purposes."""
        if self.is_file(options["EMAIL_TARGET"]):
            target_list = self.get_file_content_as_list(options)
        else:
            target_list = [options["EMAIL_TARGET"]]
        return target_list

    def send(self, options):
        num_errors = 0
        for target in self.build_target_list(options):
            target = target.strip()
            if not target:
                continue  # Skip blank lines!
            self.pprint("Sending email for target: {!s}".format(target))
            try:
                message = self.build_message(options, target)
                mail_server = self.connect(options)
                if mail_server is None:
                    raise Exception("Error connecting to {}".format(str(target)))
                mail_server.sendmail(options["SMTP_LOGIN"], target, message.as_string())
                self.pprint("Email relay successful!")
            except Exception as e:
                logging.error("Error delivering email: %s", str(e))
                num_errors += 1
        return num_errors == 0

    def build_message(self, options, target):
        message = multipart.MIMEMultipart()
        for name, value in list(options.items()):
            if name == "EMAIL_BODY":
                self.add_body(message, value)
            elif name == "EMAIL_ATTACHMENT":
                self.add_attachment(message, value)
            else:  # From, To, Subject, etc.
                self.set_option(message, name, value, target)
        return message

    def set_option(self, message, option, value, target):
        if option == "EMAIL_FROM":
            message["From"] = value
        elif option == "EMAIL_TARGET":
            message["To"] = target
        elif option == "EMAIL_PRIORITY":
            if value == "yes":
                message["X-Priority"] = " 1 (Highest)"
                message["X-MSMail-Priority"] = " High"
        elif option == "EMAIL_SUBJECT":
            message["Subject"] = value

    def add_body(self, message, text):
        # If a file has been specified as Body, then set Body to file contents.
        if os.path.isfile(text):
            body = FileOperations.open(text).read().strip()
        else:
            body = text
        message.attach(mimetext.MIMEText(body, message))

    def add_attachment(self, message, attachment):
        if not attachment:
            return False
        binary_blob = base.MIMEBase("application", "octet-stream")
        binary_blob.set_payload(FileOperations.open(attachment, "rb").read())
        encoders.encode_base64(binary_blob)  # base64 encode the Binary Blob.
        # Binary Blob headers.
        binary_blob.add_header("Content-Disposition", 'attachment; filename="{}"'.format(os.path.basename(attachment)))
        message.attach(binary_blob)
        return True


smtp = SMTP()
