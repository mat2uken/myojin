# encoding: utf-8
if __name__=="__main__":
    import sys,os
    sys.path.append("..")
    sys.path.remove("")

from flaskext import script
from flaskext.script import Command, Option
from unittest import TestLoader, TestResult
from importlib import import_module
import copy
import os,sys
import pwd
from pprint import pprint
def get_username():
    return pwd.getpwuid( os.getuid() )[ 0 ]

def read_pyconfig(app, filename):
    filename = os.path.join(app.root_path, filename)
    
    if not os.path.exists(filename):
        return dict()
    d = dict(__file__ = filename)
    execfile(filename, d)
    return d
def use_datetime_hack():
    import myojin.datetimehack
    from datetime import date, datetime

def config_from_file(config=None, defaults=('base.cfg',),app=None,use_username_config=True):
    
    username = get_username()
    basenames = [basename for basename in tuple(defaults)]
    usernames = ["%s.%s" % (username, basename)  for basename in basenames]
    if use_username_config:
        filenames = [config] + usernames + basenames
    else:
        filenames = [config] + basenames

    print >>sys.stderr, "use config files:", filenames

    if app is None:
        from flask import _request_ctx_stack
        app = _request_ctx_stack.top.app

    configs = [read_pyconfig(app, filename) for filename in filenames if filename]
    config = dict( reversed([kv for config in configs for kv in config.items() ]))

    config_obj =  type(sys)('config')
    config_obj.__dict__.update(config)

    app.config.from_object(config_obj)

    if app.config.get("TESTING",False):
        use_datetime_hack()
    
    from datetime import date, datetime
    if hasattr(date, "set_today"):
        today = app.config.get("TODAY",None)
        now = app.config.get("NOW",None)
        if today:
            date.set_today(today)
        if now:
            datetime.set_now(now)
        
    app.init()
    app.init_middleware()

    return app

class MyShell(script.Shell):
    def get_options(self):
        return (
            Option('-c', '--config',
                   dest='config',
                   default=None),
            ) + super(MyShell, self).get_options()
    
    def run(self,config, *args, **kws):
        app = config_from_file(config)
        return super(MyShell,self).run(*args,**kws)

class MyServer(script.Server):
    def handle(self, *args, **kws):
        config = kws.pop('config', None)
        app = config_from_file(config)
        app.db.create_all()

        self.host = kws['host'] = app.config.get('HTTP_HOST',None) or self.host
        self.port = kws['port'] = app.config.get('HTTP_PORT',None) if kws['port'] == self.port else kws['port']

        return script.Server.handle(self, *args,**kws)
    def __init__(self, *args, **kws):
        super(MyServer,self).__init__(*args,**kws)
        self.port = None
        self.host = None
    def get_options(self):
        return (
            Option('-c', '--config',
                   dest='config',
                   default=None),
            ) + super(MyServer, self).get_options()

    def run(self,config, *args, **kws):
        app = config_from_file(config)
        #kws['HTTP_HOST'] = app.config.get('HTTP_HOST',None) or kws.get('HTTP_HOST')
        #kws['host'] = app.config.get('HTTP_HOST',None) or kws.get('HTTP_HOST')
        
        #kws['port'] = app.config.get('HTTP_PORT',None) or kwsget('HTTP_PORT',None)
        return app.run(
            host=kws.get('host') or app.config.get('HTTP_HOST',None),
            port=kws.get('port') or app.config.get('HTTP_PORT',None),
            debug=app.config.get('DEBUG',False),
            use_debugger=app.config.get('DEBUG',False),
            use_reloader=app.config.get('DEBUG',False),
            )
        return super(MyServer,self).run(*args,**kws)

class Test(Command):
    banner = ''
    description = 'Runs a UnitTest inside Flask application context.'
    
    def __init__(self):
        pass

    def get_options(self):
        return (
            Option('-c', '--config',
                   dest='config',
                   default=None),
            Option('-s', '--startdir',
                   dest='startdir',
                   default=None),
            Option('-p', '--pattern',
                   dest='pattern',
                   default="test*.py"),
            )

    def run(self, config, startdir, pattern):

        if not pattern.endswith('.py'):
            pattern = 'test_%s.py' % pattern

        #app = config_from_file(config)
        app = config_from_file(config, defaults=('test.cfg','base.cfg'))

        if not startdir:
            startdir = app.root_path
        import unittest
        from unittest import runner

        testRunner = runner.TextTestRunner()
        loader = TestLoader()
        self.test =  loader.discover(startdir, top_level_dir=app.root_path +"/..", pattern=pattern)
        self.result = testRunner.run(self.test)
        import sys
        sys.exit()

class RunScript(Test):

    def __init__(self, script_name='set_testdata', description=None):
        self.script_name = script_name
        self._description = description

    @property
    def description(self):
        return self._description or "No description"

    def get_options(self):
        from flask import _request_ctx_stack
        app = _request_ctx_stack.top.app
        #mod = import_module(app.import_name + ".scripts." + self.script_name)
        return (
            Option('-c', '--config',
                   dest='config',
                   default=None),
            Option('-s', '--startdir',
                   dest='startdir',
                   default=None),
            Option('-p', '--pattern',
                   dest='pattern',
                   default="test*.py"),
            Option('-a', '--args',
                   dest='args',
                   default=None),
            )
    def run(self, config, startdir, pattern, args):
        app = config_from_file(config)
        mod = import_module(app.import_name + ".scripts." + self.script_name)
        if args is None:
            mod.main()
        else:
            mod.main(args)
    
class Manager(script.Manager):
    def __init__(self, *args,**kws):
        super(Manager, self).__init__(*args,**kws)
        from flask import _request_ctx_stack
        app = _request_ctx_stack.top.app
        from os import listdir
        for script_name in listdir(os.path.join(app.root_path, 'scripts')):
            if script_name.endswith(".py") and not "__init__" in script_name:
                name = script_name.split(".")[0]
                self.add_command(name, RunScript(name, description=""))
        self.add_command("runserver", MyServer())
        self.add_command("run", MyServer())
        self.add_command("shell", MyShell())
        self.add_command("test", Test())

if __name__=="__main__":
    import ntra
    
