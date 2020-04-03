from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
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
    return render_template('dashboard.html', user=current_user, habits=habits)

@app.route('/dashboard/add', methods=['POST'])
@login_required
def add_habit():
    habit = Habit(user_id=current_user.id, title=request.form['habit_name'], description=request.form['habit_description'])
    db.session.add(habit)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/dashboard/edit/<habit_id>', methods=['GET', 'POST'])
@login_required
def edit_habit(habit_id):
    if request.method == 'POST':
        #get habit being edited
        habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first()
        habit.title = request.form['title']
        habit.description = request.form['description']
        db.session.add(habit)
        db.session.commit()
        return redirect(url_for('dashboard'))
    elif request.method == 'GET':
        habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first()
        return render_template('habit_edit.html', habit=habit)
    else:
        pass

@app.route('/dashboard/delete/<habit_id>', methods=['POST'])
@login_required
def delete_habit(habit_id):
    if request.method == 'POST':
        habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first()
        db.session.delete(habit)
        db.session.commit()
        return redirect(url_for('dashboard'))
    else:
        pass

if __name__ == '__main__':
    app.run()
