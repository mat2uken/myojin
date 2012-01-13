import os
from .. import app
from . import get_static_file_path

def main(args=None):
    app_name = app.root_path.rsplit('/', 1)[1]
    namespaces = 'USE_JS_NAMESPACES'
    save_filename = '%s.js' % app_name

    build_args = [
        'python',
        '${here}/../closure/library/closure/bin/build/closurebuilder.py',
        '--root=${here}/../closure/library/third_party/closure/',
        '--root=${here}/static/js/goog/',
        '--compiler_jar=${here}/../closure/compiler.jar',
        '--compiler_flags=--compilation_level=ADVANCED_OPTIMIZATIONS',
        '--output_mode=compiled',
    ]

    here = app.root_path
    build_args += [('--root=%s/static/js/' % here) + ns for ns in app.config['USE_JS_PACKAGES']]
    build_args += ['--namespace=' + ns for ns in app.config[namespaces]]
    print build_args
    from string import Template
    from subprocess import check_output
    from cStringIO import StringIO
    from gzip import GzipFile
    result = check_output([Template(s).substitute(here=here) for s in build_args])
    with open(get_static_file_path('js', save_filename), 'w') as f:
        js_result_buf = StringIO()
        js_result_buf.write(result)
        for path in app.config.get('PRE_JS_FILES', []):
            with open(os.path.join(app.root_path, path), 'r') as f2:
                js_result_buf.write(f2.read())

        # write file
        js_result = js_result_buf.getvalue()
        f.write(js_result)
        with GzipFile(get_static_file_path('js', save_filename+'.gz'), 'w', 9) as f3:
            f3.write(js_result)

    print 'compile finish: %s' % (get_static_file_path('js', save_filename),)
