
# manage.py

from flaskext.script import Manager

from myojin import app
from flaskext.custom_script import Manager
manager = Manager(app)
    
if __name__ == "__main__":
    manager.run()
