from .apps.main.models import *
from . import db

#db.metadata.bind = db.engine
#db.engine.echo= "debug"

#db.metadata.create_all()
#app.db = db

from myojin.converters import ModelConverter
from myojin import modelutil
for mt in modelutil.model_types:
    app.url_map.converters[mt] = ModelConverter
    app.logger.debug("registered ModelConverter to converters: %s" % mt)
