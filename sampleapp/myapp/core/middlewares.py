__all__ = ['reigst_middleware']

#ex)
#class HogeMiddleware(object):
#    def __init__(self, app):
#        self.app = app
#    def __call__(self, environ, start_response):
#        return self.app(environ, start_response)

middlewares = []
def reigst_middleware(app):
    for middleware in middlewares:
        app.wsgi_app = middleware(app.wsgi_app)
