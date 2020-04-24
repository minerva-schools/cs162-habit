import pytest
from web import app, db, login_manager
from web.models import User, Milestone, Log, Habit
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
from flask_login import current_user

def create_user():
    '''Inserts a test user that has an active habit to the db'''
    db.session.add(User(username='test_user', password=generate_password_hash('test_password', method='sha256')))
    db.session.commit()
    
def test_add_milestone_no_deadline(client,reset_db):
    '''Adds a single milestone to the database with no deadline'''
    # add a user to the db
    create_user()
    assert len(list(User.query.filter_by(username='test_user'))) == 1 # ensure the user was added

    # adding a habit with a milestone should fail without login
    rv = client.post('/add_habit', data={
            'title' : 'title_test',
            'description' : 'description_test',
            'frequency' : 'daily',
            'milestone': 'test_mile',
            'deadline': None}
            )   
    assert Milestone.query.filter_by(id=1, habit_id=1, text='test_mile').first() is None # milestone should /not/ be added to db
    
    client.post('/login', data={'username': 'test_user', 'password': 'test_password'}) # login with created user
    assert current_user.id == 1 # verify login occurred
    
    #create a single milestone
    rv = client.post('/add_habit', data={
            'title' : 'title_test',
            'description' : 'description_test',
            'frequency' : 'daily',
            'milestone': 'test_mile',
            'deadline': None}
            )   
    
    m = Milestone.query.filter_by(id=1, habit_id=1, text='test_mile').first()
    assert m.text == 'test_mile' # milestone should be added to db with the correct text
    assert m.habit_id == 1 # for the correct habit
    assert m.user_id == 1 # and correct user 
    assert m.deadline == None # deadline is not set
    
    
def test_add_milestone_with_deadline(client,reset_db):
    '''Adds a single milestone to the database with no deadline'''
    # add a user to the db
    create_user()
    assert len(list(User.query.filter_by(username='test_user'))) == 1 # ensure the user was added

    # adding a habit with a milestone should fail without login
    rv = client.post('/add_habit', data={
            'title' : 'title_test',
            'description' : 'description_test',
            'frequency' : 'daily',
            'milestone': 'test_mile',
            'deadline': '2021-01-01'}
            )   
    assert Milestone.query.filter_by(id=1, habit_id=1, text='test_mile').first() is None # milestone should /not/ be added to db
    
    client.post('/login', data={'username': 'test_user', 'password': 'test_password'}) # login with created user
    assert current_user.id == 1 # verify login occurred
    
    #create a single milestone
    rv = client.post('/add_habit', data={
            'title' : 'title_test',
            'description' : 'description_test',
            'frequency' : 'daily',
            'milestone': 'test_mile',
            'deadline': '2021-01-01'}
            )   
    
    m = Milestone.query.filter_by(id=1, habit_id=1, text='test_mile').first()
    assert m.text == 'test_mile' # milestone should be added to db with the correct text
    assert m.habit_id == 1 # for the correct habit
    assert m.user_id == 1 # and correct user 
    assert m.deadline == date(2021,1,1) # deadline is not set

def test_add_milestone_from_edit_habit(client,reset_db):
    '''Adds a single milestone to the database with no deadline'''
    # add a user to the db
    create_user()
    assert len(list(User.query.filter_by(username='test_user'))) == 1 # ensure the user was added

    # login
    client.post('/login', data={'username': 'test_user', 'password': 'test_password'}) # login with created user
    assert current_user.id == 1 # verify login occurred
    
    #create a habit without a milestone
    rv = client.post('/add_habit', data={'title' : 'title_test','description' : 'description_test','frequency' : 'daily'})   
    m = Milestone.query.filter_by(habit_id=1).first()
    assert m is None # no milestone should be in the db at the moment
    
    #create a new milestone for this habit
    rv = client.post('/habit/1/edit', data={'milestone': 'test_from_edit','deadline': '2021-01-01'}, follow_redirects=True)   
    m = Milestone.query.filter_by(habit_id=1).first()
    assert m.text == 'test_from_edit' # milestone should be added to db with the correct text
    
def test_set_milestone_past(client,reset_db):
    '''Setting a milestone should fail with a deadline in the past'''
    ### First try from the add page with a brand new habit
    
    # add a user and habit to the db
    create_user()
    
    #log in
    client.post('/login', data={'username': 'test_user', 'password': 'test_password'}) # login with created user
    assert current_user.id == 1 # verify login occurred

    # adding a milestone yesterday
    deadline = datetime.strftime((datetime.now() - timedelta(days=1)),'%Y-%m-%d')
    rv = client.post('/add_habit', data={
            'title' : 'title_test',
            'description' : 'description_test',
            'frequency' : 'daily',
            'milestone': 'test_mile',
            'deadline': deadline},
            follow_redirects=True
            )  

    # query milestone
    m = Milestone.query.filter_by(habit_id=1).first()
    h = Habit.query.filter_by(title='title_test').first()
    assert m is None # the milestone was not added
    assert h is None # the habit was not added 
    assert b'The deadline cannot be in the past!' in rv.data # the message was displayed
    
    # create a habit without a milestone
    rv = client.post('/add_habit', data={'title' : 'title_test','description' : 'description_test','frequency' : 'daily'})   
    m = Milestone.query.filter_by(habit_id=1).first()
    assert m is None # no milestone should be in the db at the moment
    
    # try to add a milestone in the past
    rv = client.post('/habit/1/edit', data={'milestone': 'test_from_edit','deadline': '2000-01-01'}, follow_redirects=True)   
    m = Milestone.query.filter_by(habit_id=1).first()
    assert m is None # milestone should be added to db with the correct text