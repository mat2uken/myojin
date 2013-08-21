# encoding: utf-8
from myojin.sessions import CustomFlask
from .. import __name__
app = CustomFlask(__name__)

from .middlewares import reigst_middleware
reigst_middleware(app)
## app.config.from_pyfile('test.cfg')
## app.debug = app.config['DEBUG']

def init_babel():
    import flask_babel
    b = flask_babel.Babel(app, configure_jinja=False)
    @b.localeselector
    def get_locale():
        from flask import request
        def _get_locale():
            _lang = lambda: request.accept_languages.best_match(app.config['SUPPORT_LOCALES']) or app.config.get('DEFAULT_LANG', 'ja')
            return request.cookies.get('lang', _lang())
        return _get_locale()
init_babel()
