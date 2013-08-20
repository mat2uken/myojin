from .app import app
from flask import Flask, Response
from flask_principal import Principal, Permission, RoleNeed

principals = Principal(app)
admin_permission = Permission(RoleNeed('admin'))

#######################################################################
#######################################################################

from flask import current_app
from flaskext.principal import Identity, identity_changed

def login_view(req):
    username = req.form.get('username')

    identity_changed.send(current_app._get_current_object(),
                          identity=Identity(username))



#######################################################################
#######################################################################
import flask_principal as principal

identity_loaded = principal.identity_loaded

@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    pass
