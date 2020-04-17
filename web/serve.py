from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from web import app, db, login_manager
from .models import User, Habit, Log, Milestone

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == '': #if username is empty
            flash('Please insert a username.')
            return redirect(url_for('signup'))

        if password == '': #if password is empty
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

@app.route('/') #redirect home route
def home():
    return redirect(url_for('dashboard', current_date=date.today()))

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

        # if the username exists and the password was correct, go to the user's "dashboard" for today
        login_user(user, remember=remember)
        return redirect(url_for('dashboard', current_date=date.today()))

@app.route('/dashboard/<current_date>', methods=['GET', 'POST'])
@login_required
def dashboard(current_date):
    if request.method == 'GET':
        #find all active habits for the user that were created before or on current_date
        habits = Habit.query.filter_by(user_id=current_user.id, active=True).filter(Habit.date_created <= datetime.strptime(current_date, '%Y-%m-%d')).all()

        if habits: #if they are habits
            for habit in habits:
                #check if no log exists for the current_date
                if not Log.query.filter_by(habit_id=habit.id, date=datetime.strptime(current_date, '%Y-%m-%d')).first():
                    #if no log exists, add a log
                    log = Log(
                        user_id=current_user.id,
                        habit_id=habit.id,
                        date=datetime.strptime(current_date, '%Y-%m-%d')
                    )
                    db.session.add(log)
                    db.session.commit()

        #returns a habit, log iterable of all the logs for the current_date
        habit_log_iter = db.session.query(Habit, Log).filter(Habit.id == Log.habit_id, Log.date == datetime.strptime(current_date, '%Y-%m-%d'), Habit.active == True).all()

        return render_template('dashboard.html', user=current_user, date=current_date, habits=habit_log_iter)

    if request.method == 'POST':
        current_date = datetime.strptime(current_date, '%Y-%m-%d')
        if request.form.get('increment') == 'yesterday': #decrease current_date by one
            current_date = current_date - timedelta(days=1)
        elif request.form.get('increment') == 'tomorrow': #increase current_date by one
            current_date = current_date + timedelta(days=1)
        elif request.form.get('increment') == 'today': #return to today
            current_date = current_date.today()

        elif request.form.get('done'): #check off habits for current_date
            for checked_off_id in request.form.getlist('done'):
                log = Log.query.filter_by(user_id=current_user.id, id=checked_off_id, date=current_date).first()
                log.status = True
                db.session.add(log)
                db.session.commit()

        elif request.form.get('undo-done'): #uncheck habits for current_date
            for checked_off_id in request.form.getlist('undo-done'):
                log = Log.query.filter_by(user_id=current_user.id, id=checked_off_id).filter(Log.date.like(current_date)).first()
                log.status = False
                db.session.add(log)
                db.session.commit()

        return redirect(url_for('dashboard', current_date=datetime.strftime(current_date, '%Y-%m-%d')))

@app.route('/add_habit', methods=['GET', 'POST'])
@login_required
def add_habit():
    if request.method == 'GET':
        return render_template('add_habit.html', user=current_user)
    elif request.method == 'POST':
        #TODO: this needs to be a transaction with a db.session.rollback given an exception.

        #adds a habit
        habit = Habit(
            user_id=current_user.id,
            title=request.form.get('title'),
            description=request.form.get('description'),
            frequency=request.form.get('frequency'),
            date_created=datetime.today(),
            active=True
        )

        db.session.add(habit)
        db.session.flush() #staging

        #adds a log with the current habit's id
        log = Log(
            user_id=current_user.id,
            habit_id=habit.id,
            date=date.today()
        )

        db.session.add(log)

        
        # Add a milestone if user inserted one:
        if request.form.get('milestone'):
            deadline=None
            if request.form.get('deadline'):
                deadline=datetime.strptime(request.form['deadline'], '%Y-%m-%d')
                if deadline.date() < datetime.now().date():  #check if the deadline is not in the past
                    flash('The deadline cannot be in the past!')
                    return redirect(url_for('add_habit'))
            milestone = Milestone(user_id=current_user.id, habit_id=habit.id, text=request.form['milestone'],deadline=deadline)
            db.session.add(milestone)
            
        db.session.commit() # end of the transaction
        return redirect(url_for('dashboard', current_date=date.today()))

@app.route('/habit/<habit_id>')
@login_required
def habit(habit_id):
    habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first()
    milestones = Milestone.query.filter_by(habit_id=habit_id, user_id=current_user.id).all()
    return render_template('habit.html', habit=habit, milestones=milestones)

@app.route('/habit/<habit_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_habit(habit_id):
    habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first()
    if request.method == 'GET':
        return render_template('edit_habit.html', habit=habit)
    elif request.method == 'POST':
        if request.form.get('title') or request.form.get('description') or request.form.get('frequency'):
            habit.title = request.form.get('title')
            habit.description = request.form.get('description')
            habit.frequency = request.form.get('frequency')

            db.session.add(habit)
            db.session.commit()

            return redirect(url_for('habit', habit_id=habit.id))

        elif request.form.get('milestone'):
            deadline=None
            if request.form.get('deadline'):
                deadline=datetime.strptime(request.form['deadline'], '%Y-%m-%d')
            milestone = Milestone(user_id=current_user.id, habit_id=habit.id, text=request.form['milestone'],deadline=deadline)
            
            db.session.add(milestone)
            db.session.commit()
            
            return redirect(url_for('habit', habit_id=habit.id))
            
        elif request.form.get('archive'): #allows a user to set a habit to inactive, this will prevent habit logs from showing up on the dashboard
            habit.active = False

            db.session.add(habit)
            db.session.commit()

            return redirect(url_for('habit', habit_id=habit.id))

        elif request.form.get('unarchive'): #allows a user to set a habit to active, this will allow habit logs to show up on dashboard
            habit.active = True

            db.session.add(habit)
            db.session.commit()

            return redirect(url_for('habit', habit_id=habit.id))

        elif request.form.get('delete'): #hard delete the current habit
            #TODO: it is probably a good idea to soft delete habits and not expose hard delete functionality to the user
            Log.query.filter_by(habit_id=habit.id).delete()
            Milestone.query.filter_by(habit_id=habit.id).delete()

            db.session.delete(habit)
            db.session.commit()

            return redirect(url_for('dashboard', current_date=date.today()))

@app.route('/archive') #page for all the habits that are currently set to inactive
@login_required
def archive():
    habits = Habit.query.filter_by(user_id=current_user.id, active=False).all()
    return render_template("archive.html", habits=habits)
    
@app.route('/active_habits') #page for all current active habits 
@login_required
def active_habits():
    habits = Habit.query.filter_by(user_id=current_user.id, active=True).all()
    return render_template("active_habits.html", habits=habits)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
    
@app.shell_context_processor # Makes all objects available on flask shell for easy testing
def make_shell_context():
    '''Allows to work with all objects directly in flask shell'''
    return {'db': db, 'User': User, 'Habit': Habit, 'Milestone': Milestone, 'Log': Log}

if __name__ == '__main__':
    app.run()
