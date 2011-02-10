# encoding: utf-8
import sys;reload(sys);sys.setdefaultencoding('utf-8')
import flaskext
from flaskext import script    # <- important for wsgi
from flaskext import sessions  # <- important for wsgi
from .core.app import app, debug
def init():
    global db
    if app.config.get('DEBUG') and app.config.get('TESTING'):
        import flaskext.datetimehack
    from flaskext import rum,converters
    from .core.database import db
    from .core import globals
    import myojin
    for x in globals.__all__:
        setattr(myojin, x, getattr(globals,x ))
    from .apps import main
    from .core import mako
    app.register_module(main.module)

app.init = (init)
#from .apps.main import models

#from .apps.main.models.tests import test_classes


#app.use_x_sendfile = True



