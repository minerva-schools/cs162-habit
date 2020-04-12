import pytest
from web import app, db, login_manager
from web.models import User, Milestone, Log, Habit
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
from flask_login import current_user

def create_user_active_habit():
	'''Inserts a test user that has an active habit to the db'''
	db.session.add(User(username='test_user', password=generate_password_hash('test_password', method='sha256')))
	db.session.add(Habit(user_id=1, title='test_habit',description='test_desc', active=True))
	db.session.commit()
	
def test_set_single_milestone(client,reset_db):
	'''Adds a single milestone to the database with valid input'''
	# add a user and habit to the db
	create_user_active_habit()
	assert len(list(User.query.filter_by(username='test_user'))) == 1 # ensure the user was added
	assert len(list(Habit.query.filter_by(user_id=1))) == 1 # ensure the habit was added

	# adding a milestone should fail without login
	rv = client.post('/dashboard/add_milestones', data={'num_milestones': '1', 'deadline': '2021-01-01', 'delta': '0', 'habit_started':'1', 'title':'test_mile', 'note':'test_note'}, follow_redirects=True)
	assert b'Please log in to access this page' in rv.data
	assert Milestone.query.filter_by(id=1, habit_id=1, title='test_mile').first() is None # milestone should /not/ be added to db
	
	client.post('/login', data={'username': 'test_user', 'password': 'test_password'}) # login with created user
	assert current_user.id == 1 # verify login occurred
	
	#create a single milestone
	rv = client.post('/dashboard/add_milestones', data={'num_milestones': '1', 'deadline': '2021-01-01', 'delta': '0', 'habit_started':'1', 'title':'test_mile', 'note':'test_note'}, follow_redirects=True)
	
	m = Milestone.query.filter_by(id=1, habit_id=1, title='test_mile').first()
	assert m.title == 'test_mile' # milestone should be added to db
	assert m.habit_id == 1
	assert m.user_id == 1
	assert m.deadline == date(2021,1,1) # deadline is the right date object
	assert Log.query.filter(Log.log.like('%test_mile%'),Log.habit_id==1).first() is not None # milestone creation log was added
	
def test_set_recur_milestone(client, reset_db):
	'''Adds a recurring milestone to the database'''
	create_user_active_habit() # create a user and a habit in the database
	client.post('/login', data={'username': 'test_user', 'password': 'test_password'}) # login with created user
	assert current_user.id == 1 # verify login occurred
	
	# tested milestone configuration
	num_milestones = '3'
	delta=' 7'
	deadline = '2021-01-01'
	
	rv = client.post('/dashboard/add_milestones', data={'num_milestones': num_milestones, 'deadline': deadline, 'delta': delta, 'habit_started':'1', 'title':'test_mile', 'note':'test_note'}, follow_redirects=True) # add a recurring milestone
	ms = Milestone.query.filter_by(habit_id=1, title='test_mile')
	assert len(list(ms)) == int(num_milestones) # verify the desired number of milestones was createtd
	
	# Check the deadlines are set as expected. Note that this is quite convoluted because
	# on the DB, deadline is Date while we pass a datetime object (which we use so we can 
	# easily convert from string). So we want the deadline property to equal the date object 
	# corresponding to the datetime object we actually pass the DB when we create the milestone. 
	
	for i in range(len(list(ms))):
		assert list(ms)[i].deadline == (datetime.strptime(deadline,'%Y-%m-%d')+i*timedelta(days=int(delta))).date()
	
	
#def test_set_milestone_failure:
	#'''Setting a milestone should fail with faulty input'''
	# deadline in the past
	# non-numeric or non-positive number of milestones
	# non-numeric or negative delta between events