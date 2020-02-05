import os
from dotenv import load_dotenv

load_dotenv()
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_marshmallow import Marshmallow

app = Flask(__name__)
app.config.from_object(os.getenv("APP_SETTINGS", "app.config.DevelopmentConfig"))
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize Flask SQLAlchemy
db = SQLAlchemy(app)
ma = Marshmallow(app)

bcrypt = Bcrypt(app)

# Login Manager setup
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"

from app import routes
