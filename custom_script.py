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
import os
import pwd
from pprint import pprint
def get_username():
    return pwd.getpwuid( os.getuid() )[ 0 ]

def config_from_file(config=None, default='dev.cfg',app=None):
    
    base_config = dict()

    if not app:
        from flask import _request_ctx_stack
        app = _request_ctx_stack.top.app
    else:
        base_config.update(app.config)

    user_config = "%s.%s" % (get_username(), default)

    if config:
        using = config
    else:
        using = default
    app.config.from_pyfile(using)
    config_obj = copy.deepcopy(app.config)
    base_config.update(config_obj)

    if os.path.exists(os.path.join(app.root_path,user_config)):
        app.config.from_pyfile(user_config)
        base_config.update(app.config)
    app.config.from_object(base_config)

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


        kws['host'] = app.config.get('HTTP_HOST',None) or self.host
        kws['port'] = app.config.get('HTTP_PORT',None) if kws['port'] == self.port else kws['port']

        return script.Server.handle(self, *args,**kws)
    
    def get_options(self):
        return (
            Option('-c', '--config',
                   dest='config',
                   default=None),
            ) + super(MyServer, self).get_options()
    
    def run(self,config, *args,**kws):
        app = config_from_file(config)
        app.db.create_all()

        kws['host'] = app.config.get('HTTP_HOST',None) or self.host
        kws['port'] = app.config.get('HTTP_PORT',None) if kws['port'] == self.port else kws['port']
        return super(MyServer,self).run(*args,**kws)


class Test(Command):
    banner = ''
    description = 'Runs a Python shell inside Flask application context.'
    
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

        app = config_from_file(config)
        app = config_from_file(config, default='test.cfg', app=app)

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
    def __init__(self, script_name='set_testdata'):
        self.script_name = script_name
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
            )
    def run(self, config, startdir, pattern):
        app = config_from_file(config)
        mod = import_module(app.import_name + ".scripts." + self.script_name)
        mod.main()
    
class Manager(script.Manager):
    def __init__(self, *args,**kws):
        super(Manager, self).__init__(*args,**kws)
        from flask import _request_ctx_stack
        app = _request_ctx_stack.top.app
        from os import listdir
        for script_name in listdir(os.path.join(app.root_path, 'scripts')):
            if script_name.endswith(".py"):
                name = script_name.split(".")[0]
                self.add_command(name, RunScript(name))
        self.add_command("runserver", MyServer())
        self.add_command("run", MyServer())
        self.add_command("shell", MyShell())
        self.add_command("test", Test())
if __name__=="__main__":
    import ntra
    
