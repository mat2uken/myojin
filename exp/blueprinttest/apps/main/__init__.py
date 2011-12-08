from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound
from flask.globals import _request_ctx_stack
from flask import url_for
print "main:",__name__

mainpage = Blueprint('main', __name__ ,
                        template_folder="templates2")
page = mainpage
@mainpage.route('/', defaults={'page': 'index'})
@mainpage.route('/aaa/<page>', endpoint='aaa') 
#@mainpage.route('/<page>')
def show(page):
    ctx = _request_ctx_stack.top
    print ctx.app,mainpage
    #print url_for(".abc.show")
    return render_template('index.html')
    try:
        return render_template('pages/%s.html' % page)
    except TemplateNotFound:
        raise
        abort(404)

def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
    """Like :meth:`Flask.add_url_rule` but for a blueprint.  The endpoint for
    the :func:`url_for` function is prefixed with the name of the blueprint.
    """
    #if endpoint:
    #assert '.' not in endpoint, "Blueprint endpoint's should not contain dot's"
    self.record(lambda s:
            s.add_url_rule(rule, endpoint, view_func, **options))
