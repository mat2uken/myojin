from .app import app
from flaskext import mako
from . import globals

#mako.init(app, globals=dict(current_user=globals.current_user))
from .. import models
mako.init(app, globals=dict(globals.__dict__,
                            
                            debug_out=app.debug_out,
                            **models.__dict__
                            ))

