import httpagentparser
import os
import json
import datetime
from werkzeug import LocalStack, LocalProxy
def get_current_user():
    from ..models import User
    return User.current_user()
#global current_user
current_user = LocalProxy(get_current_user)
from .app import app as current_app
current_app.current_user = current_user
def normalize(text):
    from unicodedata import normalize as n
    return n("NFKC", text)
       
def init():
    
    global allow_ip_address
    allow_ip_address = None

    global maintenance_data
    path = current_app.config.get('MAINTENANCE_FILE_PATH')
    maintenance_data = None
    if path and os.path.exists(path):
        with open(path) as f:
            data = json.loads(f.read())
            data['mainte_date'] = \
                datetime.datetime.strptime(data['year'] + data['month'] + data['day'] + data['hour'] + data['minute'], '%Y%m%d%H%M')
            maintenance_data = data

def reset_allow_ip_address(new):
    global allow_ip_address
    allow_ip_address = new

def is_ie6(env):
    ua = httpagentparser.detect(env)
    try:
        return ua['browser']['name'] == 'Microsoft Internet Explorer' and ua['browser']['version'] == '6.0'
    except:
        return False

from .app import app as current_app
init()
del init
from myojin.submodule import url_for

__all__ = ['current_user', 'normalize', 'is_ie6', 'current_app', 'allow_ip_address', 'maintenance_data']
