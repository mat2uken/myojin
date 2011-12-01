from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

simple_page = Blueprint('simple_page', __name__ ,
#                        )
                        template_folder='templates2')
from flask.globals import _request_ctx_stack

@simple_page.route('/', defaults={'page': 'index'})
@simple_page.route('/<page>')
def show(page):
    ctx = _request_ctx_stack.top
    print ctx.app
    return render_template('index.html')
    try:
        return render_template('pages/%s.html' % page)
    except TemplateNotFound:
        raise
        abort(404)
