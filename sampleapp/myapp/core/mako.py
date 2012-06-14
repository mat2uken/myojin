import os
from .app import app
import myojin.mako
from . import globals
from .. import models

def latest_rev(type):
    js_dst_path = os.path.join(app.root_path, 'static/dst/%s/' % type)
    latest_rev = sorted([int(x) for x in os.listdir(js_dst_path)], reverse=True)[0]
    return str(latest_rev)

myojin.mako.init(app, globals=dict(globals.__dict__,
                            debug_out=app.debug_out,
                            latest_rev=latest_rev,
                            **models.__dict__
                            ))

