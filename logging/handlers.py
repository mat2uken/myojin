# encoding: utf-8

import logging, logging.handlers
from flask.globals import current_app

from .. import mailutils

class MailHandler(logging.handlers.SMTPHandler):
    """
    Logging to mail handler.
 
    support AWS SES or SMTP.
    """

    def __init__(self, fromaddr, toaddrs, subject):
        """
        Initialize the handler.
        """
        logging.Handler.__init__(self)

        self.fromaddr = fromaddr
        if isinstance(toaddrs, basestring):
            toaddrs = [toaddrs]
        self.toaddrs = toaddrs
        self.subject = subject

    def emit(self, record):
        """
        Emit a record.

        Format the record and send it to the specified addressees by myojin mail sender.
        """
        try:
            from email.utils import formatdate
            msg = self.format(record)
            msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\nDate: %s\r\n\r\n%s" % (
                            self.fromaddr,
                            ",".join(self.toaddrs),
                            self.getSubject(record),
                            formatdate(), msg)
            mailer = mailutils.Mailer(current_app)
            mailer.send(recipients=self.toaddrs, subject=self.subject, body=msg)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

