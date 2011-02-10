import os
import datetime

__all__ = ['reigst_middleware']

MAINTENANCE_PATH = '/maintenance'
class MaintenanceMiddleware(object):
    app = None
    def __init__(self, app):
        self.app = app
    def __call__(self, environ, start_response):
        from myojin.core.globals import maintenance_data
        path = environ['PATH_INFO']
        from myojin import app
        if (maintenance_data is not None
            and 'mainte_date' in maintenance_data
            and maintenance_data['mainte_date'] < datetime.datetime.now()):

            app.logger.debug(os.getpid())
            app.logger.debug(maintenance_data['mainte_date'])

            if (MAINTENANCE_PATH == path
                or '/favicon.ico' == path
                or path.startswith('/admin')
                or path.startswith('/file')
                or path.startswith('/static')):
                pass
            else:
                environ['PATH_INFO'] = MAINTENANCE_PATH
        return self.app(environ, start_response)

middlewares = [MaintenanceMiddleware]
def reigst_middleware(app):
    for middleware in middlewares:
        app.wsgi_app = middleware(app.wsgi_app)
