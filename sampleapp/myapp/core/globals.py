from werkzeug import LocalProxy

def get_current_user():
    from ..models import User
    return User.get_current_user()

from .app import app as current_app
current_user = LocalProxy(get_current_user)
current_app.current_user = current_user

__all__ = ['current_user', 'current_app']
