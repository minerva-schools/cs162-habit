import pytest
from web import app, db, login_manager
from web.models import User, Habit, Log
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash

def create_db_user(username,password):
	'''Inserts a test user to the db'''
	db.session.add(User(username=username, password=generate_password_hash(password, method='sha256')))
	db.session.commit()
	
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
	client.post('/login', data={'username': 'test_user', 'password': 'test_password'}) # login with created user
	# adding a habit should fail without login 
	rv = client.post('/add_habit', data={
            'title' : 'title_test',
            'description' : 'description_test',
            'frequency' : 'daily'})
	# assert b'Please log in to access this page' in rv.data 
	assert Habit.query.filter_by(id=1, title='title_test').first() is not None # habit should /not/ be added to db
	assert Log.query.filter_by(id=1).first() is not None