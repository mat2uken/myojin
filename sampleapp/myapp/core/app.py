# encoding: utf-8
from myojin.sessions import CustomFlask
from .. import __name__
app = CustomFlask(__name__)

from .middlewares import reigst_middleware
reigst_middleware(app)
## app.config.from_pyfile('test.cfg')
## app.debug = app.config['DEBUG']
