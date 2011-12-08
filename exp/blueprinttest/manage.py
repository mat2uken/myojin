from apps.simple import simple_page
from apps import main
import apps
from flask import Flask
#from yourapplication.simple_page import simple_page

app = Flask(__name__)
app.register_blueprint(simple_page)
app.register_blueprint(apps.main.page, url_prefix="/main")

if __name__ == "__main__":
    app.run(debug=True)
