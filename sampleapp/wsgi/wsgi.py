import os
import sys

app = None
INSTALLED = False

def application(environ, start_response):
    global INSTALLED
    global app
    if INSTALLED and app: return app(environ, start_response)

    # activate virtualenv
    activate_this = environ['VIRTUALENV_ACTIVATE_THIS']
    execfile(activate_this, dict(__file__=activate_this))
    
    from sampleapp import app as sample_app
    app = sample_app

    from myojin import custom_script
    config_name = environ['MYOJIN_CONFIG_NAME']
    print >>sys.stderr, '*' * 20, "initializing wsgi application by %s.cfg" % config_name, '*' * 20
    custom_script.config_from_file(config="%s.cfg" % config_name, defaults=('base.cfg',),
                                   app=app, use_username_config=False)

    INSTALLED = True
    app.logger.info('initialized wsgi application!')
    return app(environ, start_response)

