import os
import sys

def application(environ, start_response):
    # activate virtualenv
    activate_this = environ['VIRTUALENV_ACTIVATE_THIS']
    execfile(activate_this, dict(__file__=activate_this))

    ## import your app
    from sampleapp import app

    from myojin import custom_script
    config_name = environ['MYOJIN_CONFIG_NAME']
    print >>sys.stderr, '*' * 20, "initializing wsgi application by %s.cfg" % config_name, '*' * 20
    custom_script.config_from_file(defaults=('dev.cfg', '%s.cfg' % config_name,), app=app)

    from myojin.applogging import initlogging
    initlogging(app)

    app.logger.info('start wsgi application!')    
    return app(environ, start_response)
