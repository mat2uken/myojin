import os
from .. import app

def main():
    app_root_path = app.root_path
    depswriter_path = '%s/../closure/library/closure/bin/build/depswriter.py' % app_root_path
    app_name = app_root_path.rsplit('/', 1)[1]
    js_root_path = app_root_path + '/static/js/'

    cmd = 'python %s ' % depswriter_path
    for package in app.config['USE_JS_PACKAGES']:
        cmd += ' --root_with_prefix="%s ../%s" ' % ((js_root_path + package), package)
    cmd += ' > %s ' % (js_root_path + 'deps.js')
    print cmd
    os.system(cmd)
    print 'finish'
