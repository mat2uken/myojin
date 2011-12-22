import os
from .. import app
from mercurial import ui, hg

def get_static_file_path(type, save_filename):
    r = hg.repository(ui.ui(), ".")
    c = r.changectx("tip")
    rev = c.rev()
    rev_dir_path = os.path.join(app.root_path, 'static/dst/%s/%d' % (type, rev))
    if not os.path.exists(rev_dir_path):
        os.mkdir(rev_dir_path)
    dst_path = os.path.join(rev_dir_path, save_filename)
    return dst_path
