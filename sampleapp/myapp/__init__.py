# encoding: utf-8
import sys;reload(sys);sys.setdefaultencoding('utf-8')
import flaskext
from flaskext import script    # <- important for wsgi
from myojin import sessions  # <- important for wsgi
from .core.app import app

def init():
    global db
    if app.config.get('DEBUG') and app.config.get('TESTING'):
        import flaskext.datetimehack
    #from myojin import rum,converters
    from .core.database import db
    from .core import globals
    #import myojin
    #for x in globals.__all__:
    #    setattr(myojin, x, getattr(globals,x ))
    app.current_user = globals.current_user
    from .apps import main
    from .core import mako
    app.register_module(main.module)

app.init = (init)
from .core.globals import current_app
from .core.globals import current_user
#from .apps.main import models

#from .apps.main.models.tests import test_classes


#app.use_x_sendfile = True



