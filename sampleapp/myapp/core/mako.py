from .app import app
#from myojin import mako
import myojin.mako
from . import globals

#mako.init(app, globals=dict(current_user=globals.current_user))
from .. import models
myojin.mako.init(app, globals=dict(globals.__dict__,
                            debug_out=app.debug_out,
                            **models.__dict__
                            ))

