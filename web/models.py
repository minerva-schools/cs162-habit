from web import db
from flask_login import UserMixin
from datetime import datetime


class User(UserMixin,db.Model):

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True)
    password = db.Column(db.String(200))

    def __repr__(self):
        return "<User(id={}, username={}, password={})>".format(
            self.id,
            self.username,
            self.password)

class Habit(db.Model):

    __tablename__ = 'habit'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    date_created = db.Column(db.DateTime)
    last_modified = db.Column(db.DateTime, default=datetime.today)
    frequency = db.Column(db.String(100), default='Daily')
    active = db.Column(db.Boolean)

    def __repr__(self):
        return "<Habit(id={}, user_id={}, title={}, description={}, date_created={},frequency={},active={})>".format(
                self.id,
                self.user_id,
                self.title,
                self.description,
                self.date_created.strftime("%Y-%m-%d %H:%M"),
                self.last_modified.strftime("%Y-%m-%d %H:%M"), # changes if user changes the frequency
                self.frequency,
                self.active)

class Log(db.Model):

    __tablename__ = 'log'

    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.DateTime)
    status = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return "<Log(id={}, habit_id={}, user_id={}, date={}, status={})>".format(
            self.id,
            self.habit_id,
            self.user_id,
            self.date,
            self.status)

class Milestone(db.Model):

    __tablename__ = 'milestone'

    id = db.Column(db.Integer, primary_key=True)

    habit_id  = db.Column(db.Integer, db.ForeignKey('habit.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    text = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(200), default='custom')

    deadline = db.Column(db.Date) # deadline is optional
    complete = db.Column(db.Boolean, default=False)

    def __repr__(self):
        deadline='No deadline'
        if self.deadline:
            deadline = self.deadline.strftime("%Y-%m-%d")
        return "<Milestone={}, habit_id={}, user_id={}, text={}, type={}, deadline={}, user_succeeded={})>".format(
                self.id,
                self.habit_id,
                self.user_id,
                self.text,
                self.type,
                self.deadline,
                self.complete)

db.create_all()
