from werkzeug.security import generate_password_hash, check_password_hash
import pytest
from web import app, db, login_manager
from web.models import User, Habit
from flask import session
from flask_login import current_user

def create_user(username,password):
	'''Returns a User object for testing'''
	return User(username=username, password=generate_password_hash(password, method='sha256'))


def test_empty_db(client):
	"""Start with a blank database - no users and habits."""

	rv = client.get('/')
	assert rv.status_code == 200
	assert b'Hello Stranger!' in rv.data # the intro text for a non-logged user
	assert User.query.first() is None # no users in the DB
	assert Habit.query.first() is None # no habits in the DB


def test_signup(client, reset_db):
	'''Register user successfully'''
	assert client.get("/signup").status_code == 200 # signup page renders fine
	
	# perform signup
	rv = client.post("/signup", data={"username": "test_user", "password": "test_password"})
	
	assert rv.status_code == 302 # posted successfully
	assert rv.location == 'http://localhost/login' # user should be redirected to login page
	assert User.query.filter_by(username="test_user").first() is not None # user was added to db
	

def test_signup_existing_username_failure(client, reset_db):
	'''Register should fail if existing  username exists in db'''
	new_user = create_user(username='test_user', password='test_password') 
	db.session.add(new_user) # add a test user to the database
	db.session.commit()
	rv = client.post("/signup", data={"username": "test_user", "password": "test_password"}, follow_redirects=True)
	assert b'Username already exists.' in rv.data # user receives the error message for failed signup
	assert len(list(User.query.filter_by(username='test_user'))) == 1 # the user was not registered twice


def test_signup_empty_username_failure(client, reset_db):
	'''Register should fail with empty username or empty password'''
	rv = client.post("/signup", data={"username": "", "password": "a"}, follow_redirects=True)
	assert b'Please insert a username.' in rv.data # user receives the error message for failed signup
	assert len(list(User.query.filter_by(username=''))) == 0 # the user was not registered


def test_signup_empty_password_failure(client, reset_db):
	'''Register should fail with empty username or empty password'''
	rv = client.post("/signup", data={"username": "test_user", "password": ""}, follow_redirects=True)
	assert b'Please insert a password.' in rv.data # user receives the error message for failed signup
	assert len(list(User.query.filter_by(username='test_user'))) == 0 # the user was not registered

	
def test_login_logout(client, reset_db):
	'''User with correct credentials can login and logout'''
	assert client.get("/login").status_code == 200 # login page renders fine
	assert User.query.first() is None # verify that the db starts empty
	new_user = create_user(username='test_user', password='test_password') # create a test User object
	db.session.add(new_user) # add a test user to the database
	db.session.commit()
	assert len(list(User.query.filter_by(username='test_user'))) == 1 # user was added to db
	rv = client.post('/login', data={'username': 'test_user', 'password': 'test_password'}) # log in with user's credentials
	assert rv.location == 'http://localhost/dashboard' # user should be redirected to dashboard page upon success
	assert current_user.is_authenticated  # the login manager should now indicate an authenticated user
	assert current_user.id == 1 # the login manager should now indicate the current user has id = 1 
	
	rv = client.get('/logout') # log out
	assert rv.location == 'http://localhost/' # user should be redirected to home page
	assert not current_user.is_authenticated  # the login manager should now indicate no current user


def test_alphnum_login_logout(client, reset_db):
	'''User with correct alphanumeric credentials can login and logout'''
	assert client.get("/login").status_code == 200 # login page renders fine
	assert User.query.first() is None # verify that the db starts empty
	new_user = create_user(username='test123', password='test123') # create a test User object
	db.session.add(new_user) # add a test user to the database
	db.session.commit()
	assert len(list(User.query.filter_by(username='test123'))) == 1 # user was added to db
	rv = client.post('/login', data={'username': 'test123', 'password': 'test123'}) # log in with user's credentials
	assert rv.location == 'http://localhost/dashboard' # user should be redirected to dashboard page upon success
	assert current_user.is_authenticated  # the login manager should now indicate an authenticated user
	assert current_user.id == 1 # the login manager should now indicate the current user has id = 1 
	
	rv = client.get('/logout') # log out
	assert rv.location == 'http://localhost/' # user should be redirected to home page
	assert not current_user.is_authenticated  # the login manager should now indicate no current user


def test_login_failure(client, reset_db):
	'''User cannot login with incorrect password or non-existing username'''
	new_user = create_user(username='a', password='a') # create a test User object
	db.session.add(new_user) # add a test user to the database
	db.session.commit()
	assert len(list(User.query.filter_by(username='a'))) == 1 # user was added to db
	
	# Incorrect password
	rv = client.post('/login', data={'username': 'a', 'password': 'b'}, follow_redirects=True) # log in with wrong password
	assert b'Incorrect password' in rv.data # the user show be shown this message
	assert not current_user.is_authenticated  # the login manager should not show an authenticated user
	
	# Non-existing username
	rv = client.post('/login', data={'username': 'b', 'password': 'a'}, follow_redirects=True) # log in with non-existing username
	assert b'This username does not exist' in rv.data # the user show be shown this message
	assert not current_user.is_authenticated  # the login manager should not show an authenticated user

