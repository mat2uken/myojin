# encoding: utf-8

SMTP_LOG_FORMAT = """
Message type:       %(levelname)s
Location:           %(pathname)s:%(lineno)d
Module:             %(module)s
Function:           %(funcName)s
Time:               %(asctime)s

Message:
%(message)s
"""

FILE_LOG_FORMAT = """%(levelname)s %(asctime)s %(pathname)s:%(lineno)s >>> %(message)s"""

SYSLOG_FORMAT = FILE_LOG_FORMAT

import os
import sys
def initlogging(app):
    import logging
    from logging import handlers
    from . import handlers as myojin_handlers

    # DEBUG flag is not True set several handler for production.
    if app.config.get('LOGGING_DEBUG', False) or not app.config.get('DEBUG', True):
        if app.config.get('LOGGING_DEBUG') is True:
            from flask.logging import create_logger
            create_logger(app)
        else:
            del app.logger.handlers[:]

        import socket
        hostname = socket.gethostname()
        log_exc_mailto = app.config.get('LOGGING_EXCEPTION_MAILTO')
        if log_exc_mailto is not None:
            print >>sys.stderr, "register logging handler => exception mail to %s" % log_exc_mailto
            mh = myojin_handlers.MailHandler(app.config.get('MAIL_SENDER_FROM', 'example@example.com'), log_exc_mailto, 
                                              'Application(%s) Failed on %s' % (os.path.basename(app.root_path), hostname,))
            mh.setFormatter(logging.Formatter(SMTP_LOG_FORMAT))
            mh.setLevel(logging.ERROR)
            app.logger.addHandler(mh)

        log_filename = app.config.get('LOGGING_FILENAME', None)
        if log_filename is not None:
            print >>sys.stderr, "register logging handler => file to %s" % log_filename
            fh = handlers.TimedRotatingFileHandler(log_filename, when='D', interval=1, backupCount=2)
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter(FILE_LOG_FORMAT))
            app.logger.addHandler(fh)

        log_syslog_host = app.config.get('LOGGING_SYSLOG_HOST', None)
        if log_syslog_host is not None:
            print >>sys.stderr, "register logging handler => syslog to %s" % str(log_syslog_host)
            sh = handlers.SysLogHandler(log_syslog_host, app.config.get('LOGGING_SYSLOG_CATEGORY', 'local0'))
            sh.setLevel(logging.DEBUG)
            sh.setFormatter(logging.Formatter(SYSLOG_FORMAT))
            app.logger.addHandler(sh)

        request_logging = app.config.get('LOGGING_REQUEST_ENABLED', True)
        if request_logging:
            ignore_urls = app.config.get('LOGGING_REQUEST_IGNORE_URLS')
            ignore_urls_string = " ".join(ignore_urls)

            from flask import request
            # setting before and after request functions
            REQUEST_START_LOGGING_FORMAT  = "[REQSTART][%s] %04s %s"
            REQUEST_END_LOGGING_FORMAT    = "[  REQEND][%s] %04s %s %s"

            current_user = app.current_user

            @app.before_request
            def before_request_logging():
                if request.url in ignore_urls_string: return

                try:
                    app.logger.debug(REQUEST_START_LOGGING_FORMAT % (
                                     repr(current_user).encode('utf-8', errors="ignore") if current_user.is_authenticated() else "anonymous",
                                     request.method, request.path))
                except:
                    import traceback
                    traceback.print_exc(file=sys.stderr)

            @app.after_request
            def after_request_logging(response):
                if request.url in ignore_urls_string: return

                try:
                    if response.status_code < 400:
                        app.logger.debug(REQUEST_END_LOGGING_FORMAT % (
                                         repr(current_user).encode('utf-8', errors="ignore") if current_user.is_authenticated() else "anonymous",
                                         request.method, request.path, response.status_code))
                    else:
                        app.logger.info(REQUEST_END_LOGGING_FORMAT % (
                                         repr(current_user).encode('utf-8', errors="ignore") if current_user.is_authenticated() else "anonymous",
                                         request.method, request.path, response.status_code))
                except:
                    import traceback
                    traceback.print_exc(file=sys.stderr)

                return response

#    print >>sys.stderr, "app.config['DEBUG'] => %s" % app.config.get('DEBUG')
#    print >>sys.stderr, "app.config['LOGGING_LEVEL'] => %s" % app.config.get('LOGGING_LEVEL')

    app.logger.setLevel(app.config.get('LOGGING_LEVEL', logging.DEBUG))

    print >>sys.stderr, "app.logger.effective_level: %s" % (logging.getLevelName(app.logger.getEffectiveLevel()))
    print >>sys.stderr, "app.logger.handlers: %s" % (app.logger.handlers)
    print >>sys.stderr, "app.logger initialized."

