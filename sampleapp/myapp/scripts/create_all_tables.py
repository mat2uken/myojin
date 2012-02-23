from .. import app
from ..models import *

def main():
    db.metadata.bind = db.engine
    db.metadata.bind.echo = True
    db.metadata.create_all()

