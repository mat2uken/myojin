# -*- coding: utf-8 -*-
import os, smtplib, mimetypes
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Encoders import encode_base64
from email.Header import Header
from email.Utils import formatdate
from email.header import decode_header
from unicodedata import normalize

from myojin.mako import render
from flask.globals import current_app

EXTERNAL_CONFIG = current_app.config.get('EXTERNAL_CONFIG',{})

class Mailer(object):
    def __init__(self, app=None):
        default_config = {
            'MAIL_METHOD': 'smtp',
            'MAIL_DEBUG_LEVEL': 0,
            'MAIL_USERNAME': None,
            'MAIL_PASSWORD': None,
            'MAIL_SERVER': 'localhost',
            'MAIL_PORT': 25,
            'MAIL_SENDER_FROM': 'example@example.com',
            'MAIL_USE_TLS': False,
            'MAIL_USE_SSL': False,
        }
        app = app if app is not None else current_app
        default_config.update(app.config)
        self.config = default_config

    def send(self, recipients=None, subject=None, body=None, sender_from=None, sender_from_name=None, encoding='ISO-2022-JP', with_normalize=False):
        if isinstance(body, list) or isinstance(body, tuple):
            body = ''.join(body)

        if with_normalize:
            body = normalize("NFKC", body)

        body = body.encode(encoding, errors='replace')
        msg = MIMEText(body, 'plain', encoding)

        if sender_from is None:
            sender_from = self.config['MAIL_SENDER_FROM']

        if sender_from_name is not None:
            msg['From'] = str(Header('%s' % sender_from_name, encoding)) + ' <%s>' % sender_from
        else:
            msg['From'] = sender_from
        msg['Reply-To'] = msg['From']

        if isinstance(recipients, list) or isinstance(recipients, tuple):
            msg['To'] = ','.join(recipients)
        else:
            msg['To'] = recipients

        msg['Subject'] = Header(subject, encoding)
        msg['Date'] = formatdate()

        if self.config['MAIL_METHOD'] == 'smtp':
            return self.send_smtp(sender_from, recipients, msg)
        elif self.config['MAIL_METHOD'] == 'ses':
            return self.send_ses(sender_from, recipients, msg.as_string())
        else:
            raise Exception('Unknown sendmail Method.')

    def send_ses(self, sender_from, recipients, body):
        # SES Connection create
        aws_access_key = EXTERNAL_CONFIG['aws_access_key']
        aws_secret_key = EXTERNAL_CONFIG['aws_secret_key']

        from boto.ses import SESConnection
        ses_conn = SESConnection(aws_access_key, aws_secret_key)
        ret = ses_conn.send_raw_email(body, source=sender_from, destinations=[])

        current_app.logger.debug('sent mail to %s by SES' % (str(recipients),))
        return ret

    def send_smtp(self, sender_from, recipients, msg):
        mail_server = smtplib.SMTP(self.config['MAIL_SERVER'], self.config['MAIL_PORT'])
        mail_server.set_debuglevel(self.config['MAIL_DEBUG_LEVEL'])

        if self.config['MAIL_USE_TLS']:
            mail_server.ehlo()
            mail_server.starttls()
            mail_server.ehlo()
        if self.config['MAIL_USERNAME'] and self.config['MAIL_PASSWORD']:
            mail_server.login(self.config['MAIL_USERNAME'], self.config['MAIL_PASSWORD'])

        ret = mail_server.sendmail(sender_from, recipients, msg.as_string())

        mail_server.close()
        current_app.logger.debug('sent mail to %s by SMTP' % (str(recipients),))

        return ret

DEBUG_MAIL = """
subject: %s
body:
%s
"""

def sendmail(recipients, template, ctx, sender_from=None, sender_from_name=None):
    subject, body = render(template, ctx=ctx,to_unicode=True).split(u"\n",1)
    return sendmail_raw(recipients, subject, body, sender_from=sender_from, sender_from_name=sender_from_name)

def sendmail_raw(recipients, subject, body, sender_from=None, sender_from_name=None):
    if isinstance(recipients, basestring):
        recipients = [recipients]
    if not current_app.config.get("MAIL_SERVER", None):
        current_app.logger.debug(DEBUG_MAIL % (subject, body))
        return
    mailer = Mailer(current_app)
    return mailer.send(recipients=recipients, subject=subject, body=body, sender_from=sender_from, sender_from_name=sender_from_name)

def header2unicode(subject):
    if unicode == type(subject):
        return normalize("NFKC", subject)
    else:
        return normalize("NFKC", u"".join(unicode(s, encoding or "ascii", 'ignore') for s, encoding in decode_header(subject)))
