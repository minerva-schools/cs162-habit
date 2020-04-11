from web import db
from flask_login import UserMixin


class User(UserMixin,db.Model):

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True)
    password = db.Column(db.String(200))

class Habit(db.Model):

    __tablename__ = 'habit'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    date_created = db.Column(db.DateTime)
    frequency = db.Column(db.String(100), default='Daily')
    active = db.Column(db.Boolean)

class Log(db.Model):

    __tablename__ = 'log'

    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'))
    date = db.Column(db.DateTime)
    status = db.Column(db.Boolean)

db.create_all()
