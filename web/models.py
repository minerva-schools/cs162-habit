from web import db
from flask_login import UserMixin

class User(UserMixin,db.Model):
	'''
	The user entity in the system.
	Curremtly only has an id, username (unique), and password.
	'''
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True) #add a way to ensure input is unique
    password = db.Column(db.String(200)) # hashed upon the creation of User object from signup
    
    def __repr__(self):
        return "<User(id={}, username={}, password={})>".format(self.id, self.username, self.password)

class Habit(db.Model):
	'''
	A habit that a particular existing user is attempting to take on.
	Includes the associated user, textual description, date created, and active/not status indicator.
	'''
	habit_id = db.Column(db.Integer, primary_key=True)
	user_id  = db.Column(db.Integer, db.ForeignKey('User.id'))
	title = db.Column(db.String(100))
	description = db.Column(db.String(500))
	date_created = db.Column(db.DateTime)
	active = db.Column(db.Boolean) #whether the habit is still actively pursued
	
	def __repr__(self):
        return "<Habit(id={}, user_id={}, title={})>".format(self.habit_id, self.user_id, self.title)
);

class Milestone(db.Model):
	'''
	A milestone that a user has set for a particular habit.
	For example, for user 1, habit "Learn Spanish", a milestone may be an hour-long practice session at a particular date and time.
	'''
	milestone_id = db.Column(db.Integer, primary_key=True)
	habit_id  = db.Column(db.Integer, db.ForeignKey('Habit.habit_id'))
	time = db.Column(db.DateTime)
	note = db.Column(db.String(500)) # milestone-specific comments, such as 'vocabulary session'.
	user_succeeded = db.Column(db.Boolean) # whether the user performed the activity as planned

	def __repr__(self):
		return "<Milestone={}, habit_id={}, time={})>".format(self.milestone_id, self.habit_id, self.time)
		
db.create_all()