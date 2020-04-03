from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from web import app, db, login_manager
from .models import User, Habit, Log, Milestone

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/users')
def users():
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first() # check if a user exists

        if user: # if a user is found, try again
            flash('Username already exists')
            return redirect(url_for('signup'))

        # create new user with the form data
        new_user = User(username=username, password=generate_password_hash(password, method='sha256'))

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))
    else:
        pass
        #again, HTTP response handler baby???

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(username=username).first()

        # check if user actually exists
        if not user:
            flash('This username does not exist')
            return redirect(url_for('login'))
        if not check_password_hash(user.password, password):
            flash('Incorrect password')
            return redirect(url_for('login'))

        # if the username exists and the password was correct, go to the user's "dashboard"
        login_user(user, remember=remember)
        return redirect(url_for('dashboard'))
    else:
        pass
        #is it a good idea to throw in handlers for the other potential request methods? idk if this is handled in the decorator

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    habits = Habit.query.filter_by(user_id=current_user.id).all()
    milestones = Milestone.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', user=current_user, habits=habits, milestones=milestones)

@app.route('/dashboard/add', methods=['POST'])
@login_required
def add_habit():
    try:  # trying to implement a transaction here. Not sure if it's the right way?
        habit = Habit(user_id=current_user.id, title=request.form['habit_name'],
                      description=request.form['habit_description'],
                      date_created=datetime.now(), active=0)
        db.session.add(habit)
        db.session.commit()
        return redirect(url_for('dashboard'))
    except:
        db.session.rollback() # would this silence potential errors?

@app.route('/dashboard/start_habit', methods=['GET', 'POST'])
@login_required
def start_habit():  # starting a habit = the habit becomes active
    try:
        habit_id = request.form.get('habit_id')  # user selects the passive habit they want to start (selects the id)
        selected_habit = Habit.query.filter_by(user_id=current_user.id, id=habit_id).first() #get the corresponding habit from the db
        selected_habit.active = 1 # status of the selected habit is changed to 1 (active)
        current_user.score += 5  # user gains 5 points when starting a habit
        db.session.commit()
        return redirect(url_for('dashboard'))
    except:
        db.session.rollback()

@app.route('/dashboard/add_milestones', methods=['GET', 'POST'])
@login_required
def set_milestones(): # function for the user to add milestone to active habits
    # asks the user info on the milestone to create:
    # mandatory: which habit it falls under, title and deadline of the milestone
    # optional: note about the milestone
    milestone = Milestone(user_id=current_user.id, habit_id=request.form.get('habit_started'),
                              title=request.form['title'], note=request.form['note'],
                              deadline=datetime.strptime(request.form['deadline'], '%Y-%m-%d'))
    db.session.add(milestone)
    db.session.commit()
    return redirect(url_for('dashboard'))


@app.route('/dashboard/complete_milestone_<int:id>', methods=['GET', 'POST'])
@login_required
def complete_milestone(id): # user can mark a given milestone as "completed"
    # in the html, user selects a milestone (by clicking a button that passes the milestone id)
    milestone = Milestone.query.filter_by(id=id).first() # find the selected milestone in the db
    milestone.user_succeeded = 1 # change the status of the milestone to completed
    if milestone.deadline >= date.today(): # if finished on time, user gets 3 points
        current_user.score += 3
    elif milestone.deadline < date.today(): # if finished late, user gets 1 point
        current_user.score += 1
    db.session.commit()
    return redirect(url_for('dashboard'))



if __name__ == '__main__':
    app.run()
