import os
from .. import app
from mercurial import ui, hg

def get_latest_revision():
    repo = hg.repository(ui.ui(), ".")
    latest_rev = repo.changectx("tip").rev()
    return latest_rev

def get_static_file_path(type, save_filename):
    rev = get_latest_revision()
    rev_dir_path = os.path.join(app.root_path, 'static/dst/%s/%d' % (type, rev))
    if not os.path.exists(rev_dir_path):
        os.mkdir(rev_dir_path)
    dst_path = os.path.join(rev_dir_path, save_filename)
    return dst_path
