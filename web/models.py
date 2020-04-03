from web import db
from flask_login import UserMixin


class User(UserMixin,db.Model):
    '''

    '''

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True) #add a way to ensure input is unique
    password = db.Column(db.String(200)) # hashed upon the creation of User object from signup
    score = db.Column(db.Integer, default=0)

    def __repr__(self):
        return "<User(id={}, username={}, password={}, score={})>".format(self.id, self.username, self.password, self.score)

class Habit(db.Model):
    '''
	A habit that a particular existing user is attempting to take on.
	Includes the associated user, textual description, date created, and active/not status indicator.
    '''

    __tablename__ = 'habit'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    date_created = db.Column(db.DateTime)
    active = db.Column(db.Boolean)

    def __repr__(self):

        return "<Habit(id={}, user_id={}, title={}, description={}, date_created={},active={})>".format(
                self.id,
                self.user_id,
                self.title,
                self.description,
                self.date_created.strftime("%Y-%m-%d %H:%M"),
                self.active)

class Log(db.Model):
    '''
    Log entries for user / habit pairs to track success of habit on desired frequency.
    '''

    __tablename__ = 'log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'))
    date_logged = db.Column(db.DateTime)
    log = db.Column(db.String(500))

    def __repr__(self):
        return "<Log(id={}, user_id={}, habit_id={}, date_logged={}, log={})>".format(
            self.id,
            self.user_id,
            self.habit_id,
            self.date_logged,
            self.log
        )

class Milestone(db.Model):
    '''

    '''

    __tablename__ = 'milestone'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    habit_id  = db.Column(db.Integer, db.ForeignKey('habit.id'), nullable=False)

    title = db.Column(db.String(100), nullable=False)

    note = db.Column(db.String(500)) # milestone-specific comments, such as 'vocabulary session'.
    deadline = db.Column(db.Date, nullable=False) # deadline is mandatory to determine the score 
    user_succeeded = db.Column(db.Boolean, default=0) # whether the user performed the activity as planned

    def __repr__(self):
        return "<Milestone={}, habit_id={}, user_id={}, title={}, deadline={}, user_succeeded={})>".format(
                self.id,
                self.habit_id,
                self.user_id,
                self.title,
                self.deadline,
                self.user_succeeded)

db.create_all()
