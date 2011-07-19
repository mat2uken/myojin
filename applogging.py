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


from flask import request
def ignore_url(ignore_urls):
    rurl = request.url
    for s in ignore_urls:
        if s in rurl: return True
    return False

import os
import sys
def initlogging(app):
    import logging, logging.handlers

    # DEBUG flag is not True set several handler for production.
    if not app.config.get('DEBUG', True):
        del app.logger.handlers[:]

        import socket
        hostname = socket.gethostname()
        exc_mailto = app.config.get('EXCEPTION_MAILTO')
        if exc_mailto is not None:
            mh = logging.handlers.SMTPHandler(app.config['MAIL_SERVER'], 'info@cerevo.com', exc_mailto, 
                                              'Application(%s) Failed on %s' % (os.path.basename(app.root_path), hostname,))

            mh.setFormatter(logging.Formatter(SMTP_LOG_FORMAT))
            mh.setLevel(logging.ERROR)
            app.logger.addHandler(mh)

        h = logging.handlers.TimedRotatingFileHandler(app.config.get('LOGFILENAME', '/tmp/myojin.log'), when='D', interval=1, backupCount=2)
        h.setLevel(logging.DEBUG)
        h.setFormatter(logging.Formatter(FILE_LOG_FORMAT))
        app.logger.addHandler(h)

        from flask import request
        # setting before and after request functions
        REQUEST_START_LOGGING_FORMAT  = "[REQSTART][user=%s] %04s %s"
        REQUEST_END_LOGGING_FORMAT    = "[  REQEND][user=%s] %04s %s %s"

        current_user = app.current_user
        ignore_urls = app.config.get('LOGGING_IGNORE_URL')

        @app.before_request
        def before_request_logging():
            if ignore_urls and ignore_url(ignore_urls): return

            try:
                app.logger.debug(REQUEST_START_LOGGING_FORMAT % (
                                 "%05s,%10s" % (current_user.id, repr(current_user).encode('utf-8', errors="ignore"))[:10] if current_user.is_authenticated() else "anonymous",
                                 request.method, request.path))
            except:
                import traceback
                traceback.print_exc(file=sys.stderr)

        @app.after_request
        def after_request_logging(response):
            if ignore_urls and ignore_url(ignore_urls): return response

            try:
                if response.status_code < 400:
                    app.logger.debug(REQUEST_END_LOGGING_FORMAT % (
                                     "%05s,%10s" % (current_user.id, repr(current_user).encode('utf-8', errors="ignore"))[:10] if current_user.is_authenticated() else "anonymous",
                                     request.method, request.path, response.status_code))
                else:
                    app.logger.info(REQUEST_END_LOGGING_FORMAT % (
                                    "%05s,%10s" % (current_user.id, repr(current_user).encode('utf-8', errors="ignore"))[:10] if current_user.is_authenticated() else "anonymous",
                                    request.method, request.path, response.status_code))
            except:
                import traceback
                traceback.print_exc(file=sys.stderr)

            return response

    print >>sys.stderr, "app.config['DEBUG'] => %s" % app.config.get('DEBUG')
    print >>sys.stderr, "app.config['LOGGING_LEVEL'] => %s" % app.config.get('LOGGING_LEVEL')

    app.logger.setLevel(app.config.get('LOGGING_LEVEL', logging.DEBUG))

    if app.config.get('DEBUG', False):
        app.logger.debug('logging startup test: level=>DEBUG')
        app.logger.info( 'logging startup test: level=>INFO')
        app.logger.warn( 'logging startup test: level=>WARN')

    print >>sys.stderr, "app.logger.effective_level: %s" % (logging.getLevelName(app.logger.getEffectiveLevel()))
    print >>sys.stderr, "app.logger.handlers: %s" % (app.logger.handlers)
    print >>sys.stderr, "app.logger initialized."

