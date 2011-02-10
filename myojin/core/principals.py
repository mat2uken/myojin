from .app import app
from flask import Flask, Response
from flaskext.principal import Principal, Permission, RoleNeed

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
from flaskext  import principal

identity_loaded = principal.identity_loaded
#from flaskext.principal import indentity_loaded

## from pprint import pprint
## pprint(dir(principal))
## #pprint(principal)
## pprint(type(principal))
## print principal
## indentity_loaded = principal.indentity_loaded
## from flaskext.principal import indentity_loaded, RoleNeed, UserNeed

@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    pass

    # Get the user information from the db
#    user = db.get(identity.name)
    # Update the roles that a user can provide
##     for role in user.roles:
##         identity.provides.add(RoleNeed(role.name))
