import pytest
from web import app, db, login_manager
from web.models import User, Habit, Log
from flask import session
from datetime import date
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

def test_add_habit(client,reset_db):
	'''Adding a habit from the dashboard fails without login; Habit and Log are added successfully after login'''
	assert User.query.first() is None # no user
	create_db_user('test_user','test_password') # create a user in the db for the test
	assert len(list(User.query.filter_by(username='test_user'))) == 1 # ensure the user was added

	# adding a habit should fail without login 
	rv = client.post('/add_habit', data={
            'title' : 'title_test',
            'description' : 'description_test',
            'frequency' : 'daily'})
	# assert b'Please log in to access this page' in rv.data 
	assert Habit.query.filter_by(id=1, title='title_test').first() is None # habit should /not/ be added to db

	# log in and try again - now it should work
	login_user(client, 'test_user', 'test_password') # login with created user
	# adding a habit should fail without login 
	rv = client.post('/add_habit', data={
            'title' : 'title_test',
            'description' : 'description_test',
            'frequency' : 'daily'})
	# assert b'Please log in to access this page' in rv.data 
	assert Habit.query.filter_by(id=1, title='title_test').first() is not None # habit should /not/ be added to db
	assert Log.query.filter_by(id=1).first() is not None

def test_edit_habit(client,reset_db):
	'''Editing a habit'''
	create_db_user('test_user','test_password') #create user
	login_user(client, 'test_user', 'test_password')
	client.post('/add_habit', data={'title' : 'test_habit', 'description' : 'test_description', 'frequency' : 'daily'}) #create habit

	assert len(db.session.query(Habit, Log).filter(Habit.id == Log.habit_id).all()) is 1 #check that one habit and one log was created

	habit = Habit.query.first()
	log = Log.query.first()
	
	client.get('/logout')

	data = {
		'title' : 'test_title_edit',
		'description' : 'test_description_edit'
	}

	client.post(('/habit/{}/edit'.format(habit.id)), data=data)
	assert Habit.query.filter_by(title='test_title_edit').first() is None #title should not have ben changed

	login_user(client, 'test_user', 'test_password')

	client.post(('/habit/{}/edit'.format(habit.id)), data=data)
	assert Habit.query.filter_by(title='test_title_edit').first() is not None #title should have been changed

def test_delete_habit(client,reset_db):
	'''Delete a habit'''
	create_db_user('test_user','test_password') #create user
	login_user(client, 'test_user', 'test_password')
	client.post('/add_habit', data={'title' : 'test_habit', 'description' : 'test_description', 'frequency' : 'daily'}) #create habit

	habit = Habit.query.first()
	log = Log.query.first()

	data = {
		'delete' : 'delete'
	}

	client.post('/habit/{}/edit'.format(habit.id), data=data)
	assert Habit.query.first() is None and Log.query.first() is None #delete should delete both habit and log entries

def test_archive_habit(client,reset_db):
	'''Archive / Unarchive a Habit'''
	create_db_user('test_user', 'test_password')
	login_user(client, 'test_user', 'test_password')
	client.post('/add_habit', data={'title' : 'test_habit', 'description' : 'test_description', 'frequency' : 'daily'}) #create habit

	habit = Habit.query.first()
	log = Log.query.first()

	data = {
		'archive' : 'archive'
	}

	client.post('/habit/{}/edit'.format(habit.id), data=data)
	assert Habit.query.filter_by(active=False).first() is not None #should archive habit

	data = {
		'unarchive' : 'unarchive'
	}

	client.post('/habit/{}/edit'.format(habit.id), data=data)
	assert Habit.query.filter_by(active=True).first() is not None #should unarchive habit

def test_date_forward(client, reset_db):
	'''When a user clicks the button to go into the future on their dashboard, they should add a log entry for all active habits'''
	create_db_user('test_user', 'test_password')
	login_user(client, 'test_user', 'test_password')
	client.post('/add_habit', data={'title' : 'test_habit', 'description' : 'test_description', 'frequency' : 'daily'}) #create habit

	today = date.today()

	data = {
		'increment' : 'yesterday'
	}

	client.post('/dashboard/{}'.format(today), data=data, follow_redirects=True)

	assert len(Log.query.all()) == 1 #log table should only have one entry (created when habit was created)

	data = {
		'increment' : 'tomorrow'
	}

	client.post('/dashboard/{}'.format(today), data=data, follow_redirects=True)

	assert len(Log.query.all()) == 2 #log table should now have two, one for today and the next for tomorrow

