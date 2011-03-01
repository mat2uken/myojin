# encoding: utf-8


from flaskext.sessions import CustomFlask

from  .. import __name__

app = CustomFlask(__name__)

debug = app.logger.debug

from .middlewares import reigst_middleware
reigst_middleware(app)

## app.config.from_pyfile('test.cfg')
## app.debug = app.config['DEBUG']
