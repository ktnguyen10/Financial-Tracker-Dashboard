from financial_dashboard.dashboard import DashBoard
from flask import Flask
import os


UPLOAD_FOLDER = os.path.join('financial_dashboard/static', 'uploads')

app = Flask(__name__)
app.config.from_object(__name__)

app.debug = True
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config["SESSION_TYPE"] = "filesystem"
app.config['SECRET_KEY'] = 'abc123'

from financial_dashboard.routes import *

db = DashBoard(app, routes.curs)
db.register_dashapp()

