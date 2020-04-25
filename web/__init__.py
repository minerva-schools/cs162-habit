from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from flask_login import LoginManager

# this might solve the problem of os.getenv 
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['FLASK_ENV'] = os.getenv('development')
app.config['FLASK_APP'] = os.getenv('web')

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.init_app(app)

from .models import User
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

from web import serve, models
