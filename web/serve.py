from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from web import app, db, login_manager
from .models import User, Habit, Log

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == '':
            flash('Please insert a username.')
            return redirect(url_for('signup'))
        
        if password == '':
            flash('Please insert a password.')
            return redirect(url_for('signup'))

        
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
        return redirect(url_for('dashboard', date=date.today()))

@app.route('/dashboard/<date>', methods=['GET', 'POST'])
@login_required
def dashboard(date):
    habits = Habit.query.filter_by(user_id=current_user.id).all()
    
    if request.method == 'GET':
        return render_template(
            'dashboard.html',
            user=current_user,
            date=date,
            habits=habits)
    if request.method == 'POST':
        date = datetime.strptime(date, '%Y-%m-%d')
        if request.form.get('Yesterday'):
            #decrease day by one
            yesterday = date - timedelta(days=1)
            return render_template(
                'dashboard.html',
                user=current_user,
                date=yesterday.strftime('%Y-%m-%d'),
                habits=habits)
        elif request.form.get('Tomorrow'):
            #increase day by one
            tomorrow = date + timedelta(days=1)
            return render_template(
                'dashboard.html',
                user=current_user,
                date=tomorrow.strftime('%Y-%m-%d'),
                habits=habits)
        else:
            return render_template(
                'dashboard.html',
                user=current_user,
                date=date,
                habits=habits)

@app.route('/add_habit', methods=['GET', 'POST'])
@login_required
def add_habit():
    if request.method == 'GET':
        return render_template('add_habit.html', user=current_user)
    elif request.method == 'POST':
        print(request.form.get('title'))
        habit = Habit(
            user_id=current_user.id,
            title=request.form.get('title'),
            description=request.form.get('description'),
            frequency=request.form.get('frequency'),
            active=True
        )
        db.session.add(habit)
        db.session.commit()
        return redirect(url_for('dashboard', date=date.today()))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run()
