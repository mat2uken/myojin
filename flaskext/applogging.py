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

def ignore_url():
    requrl = request.url
    if 'favicon' in requrl or 'imgsrc' in requrl or 'healthcheck' in requrl:
        return True
    else:
        return False
import sys
def initlogging(app):
    print >>sys.stderr, "init logging..."

    import logging, logging.handlers

    ## TODO
    app.logger.setLevel(logging.DEBUG)

    if not app.config['DEBUG']:
        app.logger.handlers = []

        import socket
        hostname = socket.gethostname()
        exc_mailto = app.config.get('EXCEPTION_MAILTO')
        if exc_mailto is not None:
            mh = logging.handlers.SMTPHandler(app.config['MAIL_SERVER'], 'server-error@filejet.jp', exc_mailto, 
                                              'FileJet Application Failed on %s' % hostname)

            mh.setFormatter(logging.Formatter(SMTP_LOG_FORMAT))
            mh.setLevel(logging.ERROR)
            app.logger.addHandler(mh)

        h = logging.handlers.TimedRotatingFileHandler(app.config.get('LOGFILENAME', '/tmp/myojin.log'), when='D', interval=1, backupCount=2)
        h.setLevel(logging.DEBUG)
        h.setFormatter(logging.Formatter(FILE_LOG_FORMAT))
        app.logger.addHandler(h)

    print >>sys.stderr, "app.logger.effective_level: %s" % (logging.getLevelName(app.logger.getEffectiveLevel()))
    print >>sys.stderr, "app.logger.handlers: %s" % (app.logger.handlers)

    app.logger.debug("app.logger test DEBUG")
    app.logger.info("app.logger test INFO")


    from flask import request
    print 'debug', app.config.get('DEBUG')
    if not app.config.get('DEBUG'):

        # setting before and after request functions
        REQUEST_START_LOGGING_FORMAT  = "[REQSTART][user=%s] %04s %s"
        REQUEST_END_LOGGING_FORMAT    = "[  REQEND][user=%s] %04s %s %s"


        current_user = app.current_user

        @app.before_request
        def before_request_logging():
            if ignore_url(): return

            try:
                app.logger.debug(REQUEST_START_LOGGING_FORMAT % (
                                 "%05s,%10s" % (current_user.id, current_user.nickname.encode('utf-8', errors="ignore"))[:10] if current_user.is_authenticated() else "anonymous",
                                 request.method, request.path))
            except:
                pass

        @app.after_request
        def after_request_logging(response):
            if ignore_url(): return response

            try:
                if response.status_code < 400:
                    app.logger.debug(REQUEST_END_LOGGING_FORMAT % (
                                     "%05s,%10s" % (current_user.id, current_user.nickname.encode('utf-8', errors="ignore"))[:10] if current_user.is_authenticated() else "anonymous",
                                     request.method, request.path, response.status_code))
                else:
                    app.logger.info(REQUEST_END_LOGGING_FORMAT % (
                                    "%05s,%10s" % (current_user.id, current_user.nickname.encode('utf-8', errors="ignore"))[:10] if current_user.is_authenticated() else "anonymous",
                                    request.method, request.path, response.status_code))
            except:
                pass

            return response

#if app.config['DEBUG']:
#    @app.after_request
#    def no_cache(response):
#        response.headers['Pragma'] = 'no-cache'
#        response.headers['Cache-Control'] = 'no-cache'
#        response.headers['Expires'] = '-1'

#        app.logger.debug(response.headers)

#        return response
