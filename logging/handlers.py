# encoding: utf-8

import logging
from flask.globals import current_app

from .. import mailutils

import boto.sns

class SNSHandler(logging.Handler):
    def __init__(self, topic_name, subject="", region='ap-northeast-1',
                 aws_access_key=None, aws_secret_access_key=None):
        logging.Handler.__init__(self)

        self.subject = 'SNS Notification by error log'
        self.topic_name = topic_name

        if aws_access_key is not None:
            self.conn = boto.sns.connect_to_region(region, aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_access_key)
        else:
            self.conn = boto.sns.connect_to_region(region)
        topic_list = self.conn.get_all_topics()['ListTopicsResponse']['ListTopicsResult']['Topics']
        self.topic = None
        for topic in topic_list:
            arn = topic['TopicArn']
            if arn.endswith(topic_name):
                self.topic = arn

        if self.topic is None:
            raise NotFoundTopic('not found topic name => %s' % (self.topic_name,))

    def emit(self, record):
        try:
            msg = self.format(record)
            ret = self.conn.publish(self.topic, msg, subject=self.subject)
            app.logger.debug('sent to AWS SNS: topic=>%s, ret=%s' % (self.topic, ret))
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

class MailHandler(logging.Handler):
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

    def getSubject(self, record):
        """
        Determine the subject for the mail.

        simple return subject
        """
        return self.subject

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

