from . import user
__all__ = [name
           for mod in (user,)
           for name in mod.__all__]

from .user import *

User.encode_salt = 47


