import pytest
from web import app, db, login_manager
from web.models import User, Habit, Log
from flask import session
from datetime import date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

def create_db_user(username,password):
	'''Inserts a test user to the db'''
	db.session.add(User(username=username, password=generate_password_hash(password, method='sha256')))
	db.session.commit()

def login_user(client,username,password):
	data = {
		'username' : username,
		'password' : password
	}

	client.post('/login', data=data)

def test_add_weekly_habit(client,reset_db):
	'''Adding a habit with weekly frequency'''
	assert User.query.first() is None # no user
	create_db_user('test_user','test_password') # create a user in the db for the test
	assert len(list(User.query.filter_by(username='test_user'))) == 1 # ensure the user was added
	login_user(client, 'test_user', 'test_password') # login with created user

	# adding a habit should fail without login 
	rv = client.post('/add_habit', data={
            'title' : 'title_test',
            'description' : 'description_test',
            'frequency' : 'weekly'})
	habit = Habit.query.filter_by(id=1, title='title_test').first()
	assert habit is not None # habit should /not/ be added to db
	assert habit.frequency == 'weekly' # habit has the correct frequency
	assert Log.query.filter_by(id=1).first() is not None # a log was added for the habit
	
def test_add_monthly_habit(client,reset_db):
	'''Adding a habit with monthly frequency'''
	assert User.query.first() is None # no user
	create_db_user('test_user','test_password') # create a user in the db for the test
	assert len(list(User.query.filter_by(username='test_user'))) == 1 # ensure the user was added
	login_user(client, 'test_user', 'test_password') # login with created user

	# adding a habit should fail without login 
	rv = client.post('/add_habit', data={
            'title' : 'title_test',
            'description' : 'description_test',
            'frequency' : 'monthly'})
	habit = Habit.query.filter_by(id=1, title='title_test').first()
	assert habit is not None # habit should /not/ be added to db
	assert habit.frequency == 'monthly' # habit has the correct frequency
	assert Log.query.filter_by(id=1).first() is not None # a log was added for the habit


def test_date_forward_weekly(client, reset_db):
	'''When a user clicks the button to go into the future on their dashboard, they should add a log entry for all active habits ONLY after a week'''
	create_db_user('test_user', 'test_password')
	login_user(client, 'test_user', 'test_password')
	client.post('/add_habit', data={'title' : 'test_habit', 'description' : 'test_description', 'frequency' : 'weekly'}) #create habit

	data = {'increment' : 'tomorrow'}
	client.post('/dashboard/{}'.format(date.today()), data=data, follow_redirects=True) # navigate to tomorrow
	assert len(Log.query.all()) == 1 #log table should only have one entry (created when habit was created)

	for i in range(1,7): # go to next day six more times for the new log to be created
		tmrw = date.today() + timedelta(days=i)
		client.post('/dashboard/{}'.format(tmrw), data=data, follow_redirects=True)

	correct_date = date.today() + timedelta(days=7)
	log = Log.query.filter_by(id=2).first() # now this should exist
	assert date.strftime(log.date, '%Y-%m-%d') == date.strftime(correct_date, '%Y-%m-%d') #date of log should be next week's date
	assert len(Log.query.all()) == 2 #log table should now have two, one for today and the next week

def test_date_forward_monthly(client, reset_db):
	'''When a user clicks the button to go into the future on their dashboard, they should add a log entry for all active habits ONLY after a week'''
	create_db_user('test_user', 'test_password')
	login_user(client, 'test_user', 'test_password')
	client.post('/add_habit', data={'title' : 'test_habit', 'description' : 'test_description', 'frequency' : 'monthly'}) #create habit

	data = {'increment' : 'tomorrow'}
	client.post('/dashboard/{}'.format(date.today()), data=data, follow_redirects=True) # navigate to tomorrow
	assert len(Log.query.all()) == 1 #log table should only have one entry (created when habit was created)
	assert Habit.query.all()[0].frequency == 'monthly'
	
	for i in range(1,30): # go to next day 29 more times to create the new log next month
		tmrw = date.today() + timedelta(days=i)
		client.post('/dashboard/{}'.format(tmrw), data=data, follow_redirects=True)

	correct_date = date.today() + timedelta(days=30)
	log = Log.query.filter_by(id=2).first() # now this should exist
	assert date.strftime(log.date, '%Y-%m-%d') == date.strftime(correct_date, '%Y-%m-%d') #date of log should be next week's date
	assert len(Log.query.all()) == 2 #log table should now have two, one for today and the next week

def test_edit_frequency(client,reset_db):
	'''Editing the frequency of a habit is correctly saved in the db'''
	create_db_user('test_user','test_password') #create user
	login_user(client, 'test_user', 'test_password')
	client.post('/add_habit', data={'title' : 'test_habit', 'description' : 'test_description', 'frequency' : 'daily'}) #create habit

	assert len(db.session.query(Habit, Log).filter(Habit.id == Log.habit_id).all()) is 1 #check that one habit and one log was created

	habit = Habit.query.first()
	log = Log.query.first()
	
	data = {
		'frequency' : 'weekly',
	}

	client.post(('/habit/{}/edit'.format(habit.id)), data=data)
	habit = Habit.query.filter_by(title='test_habit').first()
	assert habit.frequency == 'weekly' # frequency should have changed
	assert habit.last_modified.date() == date.today() # last modified was also changed
	
	#
	# now check whether log creation works by weekly frequency
	#
	
	data = {'increment' : 'tomorrow'}
	client.post('/dashboard/{}'.format(date.today()), data=data, follow_redirects=True) # navigate to tomorrow
	assert len(Log.query.all()) == 1 #log table should only have one entry (created when habit was created)

	for i in range(1,7): # go to next day six more times
		tmrw = date.today() + timedelta(days=i)
		client.post('/dashboard/{}'.format(tmrw), data=data, follow_redirects=True) 

	correct_date = date.today() + timedelta(days=7)
	log = Log.query.filter_by(id=2).first() # now this should exist
	assert date.strftime(log.date, '%Y-%m-%d') == date.strftime(correct_date, '%Y-%m-%d') #date of log should be next week's date
	assert len(Log.query.all()) == 2 #log table should now have two, one for today and the next week